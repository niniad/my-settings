# 特殊取引処理手順

## 1. Amazon不足金支払い

Amazonの精算でネット金額がマイナスになった場合（広告費 > 売上 等）。

**発生パターン**: PayPay明細に「Vデビット AMAZON.CO.JP」のマイナス出金が出現

**処理手順**:
1. PayPay明細の該当行: freee勘定科目_id = 9（Amazon出品アカウント）
2. NocoDB「振替」テーブルに新規レコード追加（振替日・金額・メモ）
3. PayPay側の行に 振替_id を設定
4. settlement_journal_view で対応するマイナスSettlement Netを確認

## 2. ESPRIME送金処理

PayPay銀行からESPRIMEへの送金。

**発生パターン**: PayPay明細に「振込 カ）エスプリム」

**処理手順**:
1. PayPay明細の該当行: freee勘定科目_id = 5（ESPRIME）、振替_id = 新ID
2. NocoDB「振替」テーブルに新規レコード追加
3. NocoDB「代行会社」テーブルに2行追加:
   - **入金本体**: amount_foreign = +CNY金額, exchange_rate = 適用レート
   - **代行手数料2%**: amount_foreign = -(入金額×0.02), 同レート, freee勘定科目_id = 148（支払手数料）
4. 入金行に 振替_id を設定（PayPay側と紐付）

**為替レート**: 直近の入金時レートを以降の取引に適用。PayPal変換レートを使用。

**balance_jpy**: Google Sheetsから直接転記（自動計算しない）

## 3. セールモンスター入金処理

セールモンスターからPayPayへの入金。

**発生パターン**: PayPay明細に「振込 エイチキユ」

**処理手順**:
1. PayPay明細の該当行: freee勘定科目_id = 166（セールモンスター）
2. 振替リンクは不要（セールモンスター側は売上時に売掛金計上済み、入金時に売掛金消込）

## 4. 振替テーブル設定の手順

NocoDB「振替」テーブル（http://localhost:8080）:

1. 振替テーブルを開く
2. 新規行を追加:
   - **振替日**: 取引日
   - **金額**: 振替金額（円）
   - **メモ**: 「Amazon入金」「ESPRIME送金」等
3. 作成された行のnocodb_idを確認
4. 振替元テーブル（PayPay等）の該当行の「振替」列にリンク設定
5. 振替先テーブル（Amazon/代行会社等）の該当行の「振替」列にリンク設定

## 5. ESPRIME共有スプレッドシート

URL: https://docs.google.com/spreadsheets/d/1RlrGi_G4k4n37ezgE5sJpgWPXw8CBhHmrTeTJ9UjWH4/

- 定期的にシートが新しくなる（最新シートを使用）
- 入金取引を「入金本体 + 代行手数料2%」に分割して管理
- 為替レートは直近入金時のレートを以降の取引に適用
- `import_agency_sheet.py` でSheetsから直接読取→NocoDB書込
