
import pandas as pd
import json
import os
import glob

# Load Metadata
WALLETS = []
try:
    with open('wallets.json', 'r', encoding='utf-8') as f:
        WALLETS = json.load(f)
except:
    print("wallets.json not found. Proceeding without mapping (User must map manually).")

# Mapping Helpers
def get_freee_wallet_name(mf_sub_account, mf_account_name):
    # Mapping Logic
    # 1. Try exact match with Wallet Name
    # 2. Try partial match
    if not mf_sub_account or str(mf_sub_account) == 'nan':
        # If no sub, maybe account name? "現金"
        mf_sub_account = mf_account_name
    
    csv_val = str(mf_sub_account).strip()
    
    for w in WALLETS:
        w_name = w['name']
        # Heuristics
        if csv_val in w_name:
            return w_name
        if "楽天" in csv_val and "楽天" in w_name and "銀行" in w_name:
            return w_name
        if "PayPay" in csv_val and "銀行" in csv_val and "PayPay" in w_name and "銀行" in w_name and "デビット" not in w_name:
            return w_name
        if "PayPay" in csv_val and "デビット" in csv_val and "デビット" in w_name:
            return w_name
        if "NTT" in csv_val and "NTT" in w_name:
            return w_name
        if "直行便" in csv_val and "直行便" in w_name:
            return w_name
        if "ESPRIME" in csv_val and "ESPRIME" in w_name:
            return w_name
        if "YP" in csv_val and "YP" in w_name:
            return w_name
            
    return None # Let user map or leave blank

def is_wallet(account_name, sub_name):
    # Check if this account/sub combination represents a Freee Wallet
    # Standard MF Wallet Accounts
    wallet_accs = ['現金', '普通預金', '当座預金', '預け金', '売掛金', '未払金', '前払金'] 
    # Note: 売掛金/未払金 are Wallets in Freee ONLY if they are synced (e.g. Card, Amazon). 
    # If they are just "Unsettled AR/AP", they are NOT Wallets.
    
    # Check if we can map it to a PRE-DEFINED Freee Wallet
    mapped = get_freee_wallet_name(sub_name, account_name)
    if mapped:
        return True, mapped
    
    # "現金" is always a wallet
    if account_name == '現金':
        # Find '現金' wallet
        for w in WALLETS:
            if w['name'] == '現金':
                return True, '現金'
                
    return False, None

def process_file(file_path):
    print(f"Processing {os.path.basename(file_path)}...")
    df = pd.read_excel(file_path)
    
    deals_rows = []
    journal_rows = []
    
    for _, row in df.iterrows():
        date = str(row['発生日']).split(' ')[0].replace('/', '-') # YYYY-MM-DD
        amount = row['借方金額'] # Assuming Balanced
        desc = str(row['摘要']) if not pd.isna(row['摘要']) else ""
        
        dr_acc = str(row['借方勘定科目']).strip()
        if dr_acc == '外注工賃': dr_acc = '外注費'
        
        dr_sub = row['借方補助科目']
        dr_tax = str(row['借方税区分']).strip()
        # Simple Tax Mapping
        if dr_tax == 'nan': dr_tax = ''
        if '課税仕入' in dr_tax and '10%' in dr_tax: dr_tax = '課対仕入 10%'
        
        cr_acc = str(row['貸方勘定科目']).strip()
        if cr_acc == '外注工賃': cr_acc = '外注費'
        cr_sub = row['貸方補助科目']
        cr_tax = str(row['貸方税区分']).strip()
        if cr_tax == 'nan': cr_tax = ''
        if '課税仕入' in cr_tax and '10%' in cr_tax: cr_tax = '課対仕入 10%'
        
        dr_is_wallet, dr_wallet_name = is_wallet(dr_acc, dr_sub)
        cr_is_wallet, cr_wallet_name = is_wallet(cr_acc, cr_sub)
        
        # Classification
        # Case A: Transfer (Wallet to Wallet) -> Journal
        if dr_is_wallet and cr_is_wallet:
            # Manual Journal
            # Problem: How to specify Wallet in Journal CSV?
            # Freee Manual Journal Import expects '勘定科目' to be valid (Account Item).
            # If we put '楽天銀行' (Wallet Name) as Account Item, Freee usually accepts it if the Account Item exists.
            # (Freee creates Account Items for Wallets).
            # So we use `dr_wallet_name` and `cr_wallet_name` as Account Items.
            
            j_row = {
                "発生日": date,
                "借方勘定科目": dr_wallet_name,
                "借方補助科目": "", # Don't map Sub here, irrelevant for Wallet usually
                "借方税区分": dr_tax,
                "借方金額": amount,
                "貸方勘定科目": cr_wallet_name,
                "貸方補助科目": "",
                "貸方税区分": cr_tax,
                "貸方金額": amount,
                "摘要": desc
            }
            journal_rows.append(j_row)
            
        # Case B: Expense (Deal)
        # Dr != Wallet (Expense), Cr = Wallet OR Unsettled
        elif not dr_is_wallet:
            # It's an Expense Deal
            d_row = {
                "収支区分": "支出",
                "発生日": date,
                "勘定科目": dr_acc,
                "金額": amount,
                "税区分": dr_tax,
                "備考": desc,
                "品目": dr_sub if not pd.isna(dr_sub) else "", # Map Sub to Tag/Item
            }
            
            # Settlement
            if cr_is_wallet:
                d_row["決済状況"] = "完了"
                d_row["決済口座"] = cr_wallet_name
                d_row["決済金額"] = amount
                d_row["決済日"] = date # Assume same day
            elif cr_acc in ['未払金', '買掛金']:
                d_row["決済状況"] = "未決済"
                # If Cr has sub (e.g. Partner), map to Remarks or Partner?
                # Freee Import has '取引先'.
                if not pd.isna(cr_sub):
                    d_row["取引先"] = cr_sub
            else:
                d_row["決済状況"] = "未決済" # Default
                
            deals_rows.append(d_row)
            
        # Case C: Income (Deal)
        # Cr != Wallet (Income), Dr = Wallet OR Unsettled
        elif not cr_is_wallet:
            # It's an Income Deal
            d_row = {
                "収支区分": "収入",
                "発生日": date,
                "勘定科目": cr_acc,
                "金額": amount,
                "税区分": cr_tax,
                "備考": desc,
                "品目": cr_sub if not pd.isna(cr_sub) else "",
            }
            
            # Settlement
            if dr_is_wallet:
                d_row["決済状況"] = "完了"
                d_row["決済口座"] = dr_wallet_name
                d_row["決済金額"] = amount
                d_row["決済日"] = date 
            elif dr_acc in ['売掛金', '未収金']:
                d_row["決済状況"] = "未決済"
                if not pd.isna(dr_sub):
                    d_row["取引先"] = dr_sub
            else:
                d_row["決済状況"] = "未決済"
                
            deals_rows.append(d_row)
            
        else:
            # Fallback (Should be rare: Wallet to Wallet was caught first)
            # Maybe Liability to Liability? Journal.
            j_row = {
                "発生日": date,
                "借方勘定科目": dr_acc,
                "借方補助科目": dr_sub,
                "借方税区分": dr_tax,
                "借方金額": amount,
                "貸方勘定科目": cr_acc,
                "貸方補助科目": cr_sub,
                "貸方税区分": cr_tax,
                "貸方金額": amount,
                "摘要": desc
            }
            journal_rows.append(j_row)

    # Save CSVs
    base = os.path.basename(file_path).split('.')[0]
    
    # Deals CSV
    if deals_rows:
        df_d = pd.DataFrame(deals_rows)
        # Reorder/Ensure Columns for Freee
        # Required: 収支区分, 発生日, 勘定科目, 金額
        # Optional: 決済状況, 決済口座
        df_d.to_csv(f"import_deals_{base}.csv", index=False, encoding='shift_jis') # Excel often prefers Shift-JIS for JP
        print(f"Saved import_deals_{base}.csv ({len(deals_rows)} rows)")
        
    # Journals CSV
    if journal_rows:
        df_j = pd.DataFrame(journal_rows)
        df_j.to_csv(f"import_journals_{base}.csv", index=False, encoding='shift_jis')
        print(f"Saved import_journals_{base}.csv ({len(journal_rows)} rows)")

if __name__ == "__main__":
    files = [
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2023.xlsx",
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2024.xlsx",
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2025.xlsx"
    ]
    for f in files:
        process_file(f)
