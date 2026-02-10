
import pandas as pd
import os
import glob

def convert_csv_to_xlsx():
    # Target directory
    target_dir = r"c:/Users/ninni/Documents/projects/freee/money_forward/"
    
    # Pattern for generated CSVs
    csv_files = glob.glob(os.path.join(target_dir, "import_deals_*.csv")) + \
                glob.glob(os.path.join(target_dir, "import_journals_*.csv"))
                
    for csv_file in csv_files:
        print(f"Converting {os.path.basename(csv_file)} to XLSX...")
        try:
            # Read CSV (using Shift-JIS as generated)
            df = pd.read_csv(csv_file, encoding='shift_jis')
            
            # Construct XLSX path
            base_name = os.path.basename(csv_file).replace('.csv', '.xlsx')
            xlsx_path = os.path.join(target_dir, base_name)
            
            # Save to XLSX
            df.to_excel(xlsx_path, index=False)
            print(f"Saved {xlsx_path}")
            
        except Exception as e:
            print(f"Error converting {csv_file}: {e}")

if __name__ == "__main__":
    convert_csv_to_xlsx()
