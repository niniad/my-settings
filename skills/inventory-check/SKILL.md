---
name: inventory-check
description: >
  FBA在庫残日数と輸入リードタイムを比較し発注必要な商品を検出するスキル。BigQueryで在庫データを取得し、季節係数・春節補正・進行中輸入を考慮した発注判断レポートを生成する。
  トリガー: 「在庫チェック」「発注確認」「在庫確認」「補充発注」「在庫残日数」
---

# 在庫・発注チェックスキル

FBA在庫の残日数と輸入リードタイムを比較し、発注が必要な商品を検出する。

## リファレンスドキュメント

| 内容 | ファイル |
|------|---------|
| 商品カタログ（SKU一覧・セット構成・廃盤情報） | [references/product-catalog.md](references/product-catalog.md) |
| リードタイム実績・輸送手段選択・中国休暇 | [references/lead-times.md](references/lead-times.md) |
| 季節係数・セール補正 | [references/seasonal-coefficients.md](references/seasonal-coefficients.md) |

> **廃盤確定・廃盤検討中商品の発注推奨は出さない。** 詳細は product-catalog.md 参照。

---

## データソース

| データ | 取得先 |
|--------|--------|
| 現在のFBA在庫・残日数 | BigQuery `analytics.rpt_inventory_health` |
| 輸入リードタイム実績 | NocoDB `mm0qwmulkk77q2r`（輸入ロットマスタ） / SQLite直接 |
| 輸入明細（商品別数量）| NocoDB `moe6396o8vxmo1a`（輸入明細）/ SQLite直接 |
| 製品マスタ（SKU・商品名）| NocoDB `mbmwar2oovnkfc9`（製品マスタ）/ SQLite直接 |

---

## 発注要否の判断基準

```
発注リードタイム（目安）+ 安全在庫（30日）= 発注ポイント（在庫残日数）

OCS   発注ポイント（通常期）: 40日 + 30日 = 70日
海源  発注ポイント（通常期）: 60日 + 30日 = 90日

春節前（発注月が11月〜1月）:
OCS   春節前発注ポイント: 70日 + 30日 = 100日
海源  春節前発注ポイント: 85日 + 30日 = 115日
```

---

## 分析手順

### Step 0: データ鮮度チェック（必須・スキップ不可）

**0-a: 日次ASINデータの鮮度確認**

```sql
SELECT
  MAX(report_date) as latest_date,
  DATE_DIFF(CURRENT_DATE(), MAX(report_date), DAY) as days_stale
FROM `main-project-477501.analytics.fact_daily_asin`
```

- `days_stale <= 3`: OK → 0-b へ
- `days_stale > 3`: **分析を停止**。「fact_daily_asinが{days_stale}日古く、日販計算が不正確です」と警告して終了

**0-b: 販売実績データの網羅性確認**

```sql
-- 直近30日間のデータが存在するか確認
SELECT
  COUNT(DISTINCT report_date) as data_days,
  MIN(report_date) as from_date,
  MAX(report_date) as to_date
FROM `main-project-477501.analytics.fact_daily_asin`
WHERE report_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
```

- `data_days >= 25`: OK（30日間のうち25日以上） → Step 1 へ
- `data_days < 25`: **警告表示**。「直近30日のうち{data_days}日分しかデータがなく、日販が過少推定になっている可能性があります」と注記して続行

---

### Step 1: 現在のFBA在庫確認

```sql
SELECT
  seller_sku,
  product_name,
  fulfillable_quantity,
  inbound_working_quantity + inbound_shipped_quantity + inbound_receiving_quantity as inbound_total,
  units_sold_30d,
  ROUND(avg_daily_units, 2) as avg_daily_units,
  ROUND(days_until_stockout, 0) as days_until_stockout,
  stock_status
FROM `main-project-477501.analytics.rpt_inventory_health`
WHERE product_name LIKE '%Ufa%'
ORDER BY days_until_stockout ASC NULLS LAST
```

---

### Step 2: 発注フラグ判定と推奨発注数の計算

**2-a: 発注ポイントと発注フラグ**

```
季節判断:
- 現在月が 10〜1月 → 春節前後リスク期間
- それ以外 → 通常期

発注フラグON（要発注）条件:
  days_until_stockout < 発注ポイント かつ inbound_total == 0

警告条件（inbound_total > 0 でも確認）:
  days_until_stockout < 30日 → 緊急
  days_until_stockout < 発注ポイント × 0.5 → 要注意

除外条件（発注フラグを立てない）:
  廃盤確定・廃盤検討中の商品（product-catalog.md 参照）
```

**2-b: 推奨発注数の計算**

```
目標カバー期間 = リードタイム + 安全在庫 + 次回補充まで
               = OCS: 40日 + 30日 + 90日 = 160日
               = 海源: 60日 + 30日 + 90日 = 180日

推奨発注数 = MAX(0, ceil(目標カバー期間 × avg_daily_units) - fulfillable_quantity - inbound_total)
```

**2-c: エプロンのセット考慮（重要）**

エプロンはセット商品（セットA・セットB）が存在するため、単品カラーの発注数をセット用と単品用に分けて計算する。

```
各カラーの発注数 = セット用発注数 + 単品用発注数

セット用発注数:
  セットA構成（はたらくくるま・恐竜・トラ）の場合:
    セットA avg_daily × 目標日数 - セットA fulfillable_quantity
  セットB構成（クマ・オリーブ・うさぎ）の場合:
    セットB avg_daily × 目標日数 - セットB fulfillable_quantity

単品用発注数:
  当該カラー単品の avg_daily × 目標日数 - 単品 fulfillable_quantity

※ 単品廃盤・セット継続の商品（オリーブ・トラ・うさぎ）はセット用発注数のみ。
※ セット構成は references/product-catalog.md を参照。
```

---

### Step 3: 進行中の輸入を確認

```bash
sqlite3 "C:/Users/ninni/nocodb/noco.db" "
SELECT lot.id, lot.carrier, lot.ship_date, lot.import_permit_date,
       prod.sku, prod.name, det.shipped_qty
FROM 'nc_opau___輸入ロットマスタ' lot
JOIN 'nc_opau___輸入明細' det ON det.nc_opau___shipments_id = lot.id
JOIN 'nc_opau___製品マスタ' prod ON det.nc_opau___製品マスタ_id = prod.id
WHERE lot.destination = 'FBA'
  AND lot.delivery_date IS NULL
  AND lot.ship_date IS NOT NULL
ORDER BY lot.ship_date DESC;
"
```

---

### Step 4: 結果レポート

```
【在庫チェック結果】 {確認日}
データ鮮度: fact_daily_asin 最終日 {latest_date}（{days_stale}日前）

■ 発注必要 🔴
  {SKU} {商品名}: 残{N}日 → 発注推奨（ポイント: {X}日）
  推奨発注数: {合計}枚
    - セット用: {N}枚（セット{A/B} × {n}セット分）
    - 単品用:   {N}枚

■ 要観察 🟡（残{発注ポイント}日〜発注ポイント日）
  {SKU} {商品名}: 残{N}日（発注期限目安: {日付}）

■ 適正 🟢
  {SKU} {商品名}: 残{N}日

■ 進行中の輸入
  ロット{id} {輸送会社}: 発送済み、輸入許可{日付}予定
  - {商品名} {N}個

■ 廃盤・対象外（表示のみ）
  {SKU} {商品名}: 残{N}日（{廃盤状況}）
```

---

## 注意事項

- `rpt_inventory_health` の `days_until_stockout` は30日間の平均日販ベース。季節変動に注意。
- 繁忙期（10〜12月）は日販が平常期の1.5〜2倍になるため、残日数を0.6〜0.7掛けで評価する。
- `inbound_total` > 0 の場合は納品中分を加算した実質残日数で判定する:
  実質残日数 = (fulfillable_quantity + inbound_total) / avg_daily_units
- 過剰在庫（days_until_stockout > 180日）は通常発注不要。ただし販売増トレンドがある場合は再判断。
