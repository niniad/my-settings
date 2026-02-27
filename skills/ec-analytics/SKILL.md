---
name: ec-analytics
description: >
  EC事業（Amazon FBA お食事エプロン・マザーズリュック）の分析・利益計算スキル。
  BigQuery MCP経由でデータ取得し、月次レビュー・商品別利益・広告効率・クロス購入・在庫を分析する。
  トリガー: 「EC分析」「売上分析」「利益計算」「広告分析」「在庫確認」「月次レビュー」
  「エプロン」「マザーズリュック」「3枚セット」「TACOS」「ACOS」「KPI」
  「クロス購入」「商品ポートフォリオ」「BCG」
---

# EC Analytics

## BigQuery アクセス

BigQuery MCP ツール（`mcp__bigquery__*`）を使用する。直接SQLを実行できる。

```
mcp__bigquery__execute_sql     — SQL実行（主力）
mcp__bigquery__search_catalog  — テーブル/ビュー検索
mcp__bigquery__get_table_info  — スキーマ確認
mcp__bigquery__list_table_ids  — テーブル一覧
```

プロジェクト: `main-project-477501`

## データアーキテクチャ（4層）

### Source層（変更不可）
| データセット | 内容 |
|---|---|
| `sp_api_external` | Amazon SP-API生データ（注文・在庫・Settlement）。GCS外部テーブル |
| `amazon_ads_external` | 広告API生データ（SPキャンペーン・キーワード・商品広告）|
| `amazon_ads_v1_external` | 広告API v1（**クロス購入 `sp_purchased_products`** を含む）|
| `nocodb` | NocoDB同期データ（原価 `standard_cost_history`・商品マスタ `product_master`）|
| `accounting` | 会計ビュー（仕訳・P&L・BS）|

### Staging層（VIEW — コスト0、常にソース最新）
| ビュー | 用途 |
|---|---|
| `analytics.stg_sp_traffic_child_asin` | 日次×子ASIN売上・トラフィック |
| `analytics.stg_sp_traffic_daily` | 日次全体サマリー |
| `analytics.stg_sp_settlement` | Settlement明細（フィルタ済み）|
| `analytics.stg_sp_inventory` | FBA在庫（ネストフラット化）|
| `analytics.stg_ads_campaign_daily` | キャンペーン日次 |
| `analytics.stg_ads_keyword_daily` | キーワード日次 |
| `analytics.stg_ads_product_daily` | 商品広告日次（ASIN別広告費の算出元）|
| `analytics.stg_ads_search_term_daily` | 検索語句日次 |
| `analytics.stg_ads_cross_purchase` | クロス購入（広告ASIN×購入ASIN）|
| `analytics.stg_sqp_weekly` | 検索クエリパフォーマンス週次 |
| `analytics.stg_cost_standard` | **原価の正本。** nocodb.standard_cost_history + product_master |

### Fact層（Scheduled Queryで日次実体化）
| テーブル | 粒度 | リフレッシュ |
|---|---|---|
| `analytics.fact_daily_asin` | 日次×子ASIN | 02:00 JST |
| `analytics.fact_daily_parent_asin` | 日次×親ASIN | 02:00 JST |
| `analytics.fact_monthly_settlement_sku` | 月次×SKU | 03:00 JST |

### Report層（VIEW — Claudeが直接叩く）
| ビュー | 用途 |
|---|---|
| `analytics.rpt_data_freshness` | **最初に確認。** 各データソースの鮮度・遅延状態・安全基準日 |
| `analytics.rpt_kpi_monthly` | **月次KPIダッシュボード。** Traffic系+Settlement系の2軸。閾値判定 + `data_quality` フラグ |
| `analytics.rpt_kpi_weekly` | 週次KPI + 月次目標進捗率 |
| `analytics.rpt_profit_variance_monthly` | **利益変動の前月比ウォーターフォール分解。** 主因自動特定 |
| `analytics.rpt_pnl_monthly_detail` | **経費内訳P&L。** Amazon手数料分解 + 固定費（保管・月額・Vine等）|
| `analytics.rpt_pnl_monthly_sku` | 月次SKU別P&L（広告費配賦済み）|
| `analytics.rpt_product_profitability` | 商品別月次収益性 + BCGマトリクス分類（**Settlement利益率基準**）|
| `analytics.rpt_market_trend_monthly` | **市場トレンド分析。** 市場規模変動 vs 自社シェア変動 |
| `analytics.rpt_ad_campaign_performance` | キャンペーン月次パフォーマンス + 効率分類 |
| `analytics.rpt_ad_keyword_efficiency` | キーワード効率分析（直近30日、無駄コスト算出）|
| `analytics.rpt_ad_cross_purchase` | クロス購入サマリー + 真のROAS（直近90日）|
| `analytics.rpt_weekly_asin_with_sqp` | 週次ASIN + 市場データ（Impシェア・購入シェア）|
| `analytics.rpt_inventory_health` | 在庫月数 + 補充/過剰フラグ + 在庫切れ予測日数 |
| `analytics.rpt_repeat_purchase` | リピート購入分析（月次）|

### 売上・利益の2系統

rpt_kpi_monthly には2系統のデータが含まれる。目的に応じて使い分けること。

| 系統 | カラム | ソース | 即時性 | 用途 |
|------|--------|--------|--------|------|
| **Traffic系** | `total_sales`, `estimated_profit` | fact_daily_asin | 翌日反映 | 売上トレンド・CVR・TACOS監視 |
| **Settlement系** | `settlement_sales`, `settlement_profit` | rpt_pnl_monthly_detail | 1-2週遅延 | **損益判断・意思決定** |

- `estimated_profit` = 売上 - 原価 - 広告費。**Amazon手数料・ポイント・プロモ・返品を含まない概算**
- `settlement_profit` = 全費用込みの営業利益。**利益の判断にはこちらを使う**
- 当月の `settlement_profit` は NULL（「集計中」）。売上・CVR・TACOSでトレンド監視
- `profit_status` の閾値: Settlement営業利益 ≥¥50K→OK / ≥¥0→注意 / <¥0→警告

> **注意**: `estimated_profit` は実際の利益より¥10-30万高く表示される。
> 絶対にestimated_profitだけで利益の良否を判断しないこと。

---

## 分析パターン

詳細SQL: [references/analysis-patterns.md](references/analysis-patterns.md)

| # | 分析 | Report VIEW | 頻度 |
|---|------|---|---|
| 0 | **データ鮮度確認** | `rpt_data_freshness` | **毎回最初に実行** |
| 1 | 月次KPIレビュー | `rpt_kpi_monthly` | 月次 |
| 2 | **利益変動分解** | `rpt_profit_variance_monthly` | 月次（KPI確認後） |
| 3 | 経費内訳P&L | `rpt_pnl_monthly_detail` | 変動分解で経費が主因の時 |
| 4 | SKU別P&L | `rpt_pnl_monthly_sku` | 月次 |
| 5 | 商品別収益性 | `rpt_product_profitability` | 月次 |
| 6 | **市場トレンド** | `rpt_market_trend_monthly` | 変動分解で売上が主因の時 |
| 7 | 広告キャンペーン | `rpt_ad_campaign_performance` | 月次 |
| 8 | キーワード効率 | `rpt_ad_keyword_efficiency` | 月次 |
| 9 | **広告クロス購入** | `rpt_ad_cross_purchase` | 広告変更時 |
| 10 | 週次＋市場データ | `rpt_weekly_asin_with_sqp` | 週次 |
| 11 | 在庫健全性 | `rpt_inventory_health` | 月次 |
| 12 | リピート購入 | `rpt_repeat_purchase` | 四半期 |

### 広告停止・変更時の必須チェック

広告の停止・予算変更を検討する際は、**同一商品TACOSだけで判断しない**。
必ず `rpt_ad_cross_purchase` でクロス購入を確認する。

全商品でクロス購入率64〜79%（広告経由購入の大半が他柄の購入）。
`true_roas` = クロス購入込み総売上 / 広告費 で評価する。

## 月次レビュー手順（毎月1〜3日）

KPI定義・目標値: [references/kpi-targets.md](references/kpi-targets.md)

```
手順:
0. データ鮮度: rpt_data_freshness で全ソースの状態確認。異常があれば報告
1. KPI取得: rpt_kpi_monthly で当月+3ヶ月推移。data_quality列を必ず確認
2. 異常検知: sales_status/profit_status/tacos_status/cvr_status で閾値判定
   ※ profit_status はSettlement基準。当月は「集計中」なので前月以前で判断
3. 変動分解: rpt_profit_variance_monthly で前月比の利益変動要因を特定（primary_driver）
4. 深掘り（primary_driverに応じて分岐）:
   - 売上変動 → rpt_market_trend_monthly で市場要因 vs 自社要因を判別
   - 経費変動 → rpt_pnl_monthly_detail で手数料内訳・固定費を確認
   - 広告費変動 → rpt_ad_campaign_performance でキャンペーン別効率を確認
5. 商品別: rpt_product_profitability で利益貢献上位/下位を特定
6. P&L: rpt_pnl_monthly_sku でSKU別の利益構造を確認
7. 広告: rpt_ad_campaign_performance で非効率キャンペーン特定
8. クロス購入: rpt_ad_cross_purchase で真のROAS確認（広告変更検討時のみ）
9. 在庫: rpt_inventory_health で補充アラート確認
10. 記録: NocoDB KPI_Monthly にスナップショット、PDCA_Actions にアクション
```

### 月次KPI取得SQL

```sql
SELECT * FROM `main-project-477501.analytics.rpt_kpi_monthly`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
ORDER BY year_month DESC
```

## 週次チェック（毎週月曜）

```
手順:
1. rpt_kpi_weekly で月次目標に対する進捗率
2. rpt_weekly_asin_with_sqp で市場データとの比較（Impシェア、購入シェアの変動）
3. rpt_inventory_health で在庫アラート（2ヶ月未満 or 8ヶ月超）
4. 前週アクションの進捗確認
```

## PDCAサイクル

### Plan: データに基づく仮説立案
- 仮説テンプレート: 「{KPI}が{変化}しているのは{原因仮説}が要因。{対策}により{期待効果}が見込める」
- NocoDB PDCA_Actions に「計画中」で記録

### Do: 実行（ユーザー確認必須）
- 広告変更: Amazon Ads MCP で現在値確認 → 変更案提示 → **ユーザー承認** → 実行
- **全ての変更を NocoDB にログ**（日時、変更前後の値、理由）
- PDCA_Actions のステータスを「実行中」に更新

### Check: 効果測定（7〜14日後）
- fact_daily_asin で変更前/後7日の比較
- PDCA_Actions に KPI_Before/KPI_After を記録

### Act: 次のアクション決定
- 効果あり → 継続/拡大
- 効果なし → 原因分析、仮説修正
- 悪化 → 即時ロールバック検討、ユーザーに報告
- PDCA_Actions を「完了」に更新

## 広告設定の確認・変更（Amazon Ads MCP）

リアルタイムの広告設定値（配信中/一時停止、入札額、予算）は Amazon Ads MCP（`mcp__amazon-ads__*`）で操作する。
BigQuery の `amazon_ads_external` は過去のパフォーマンスデータ（日次バッチ）なので、**現在の設定値** とは異なる。

### 使い分け

| 目的 | ツール |
|------|--------|
| 過去の広告パフォーマンス（ACOS・売上・クリック）| BigQuery Report層 VIEW |
| 現在の配信状態・入札額・予算 | Amazon Ads MCP |
| 広告の有効/一時停止・入札額変更 | Amazon Ads MCP（書き込み）|

### 読み取りツール

| ツール | 説明 |
|--------|------|
| `amazon_ads_list_campaigns` | キャンペーン一覧（名前・状態・日予算）|
| `amazon_ads_list_ad_groups` | 広告グループ一覧 |
| `amazon_ads_list_product_ads` | 商品広告一覧（ASIN・SKU・状態）|
| `amazon_ads_list_keywords` | キーワード一覧（マッチタイプ・入札額・状態）|
| `amazon_ads_list_targets` | ターゲット一覧（ターゲット式・入札額・状態）|

### 書き込みツール（実行前にユーザー確認必須）

| ツール | 説明 |
|--------|------|
| `amazon_ads_update_campaign_state` | キャンペーンの有効/一時停止 |
| `amazon_ads_update_campaign_budget` | キャンペーンの日予算変更 |
| `amazon_ads_update_ad_group_state` | 広告グループの有効/一時停止 |
| `amazon_ads_update_keyword_state` | キーワードの有効/一時停止 |
| `amazon_ads_update_keyword_bid` | キーワードの入札額変更 |
| `amazon_ads_update_target_state` | ターゲットの有効/一時停止 |
| `amazon_ads_update_target_bid` | ターゲットの入札額変更 |

安全策: ARCHIVED（不可逆）は除外。入札額上限 5,000円。予算上限 100,000円。変更前後の値を返す。

## 外部リソース

| リソース | パス |
|---------|------|
| EC戦略書 | `C:/Users/ninni/projects/life/docs/ec_strategy.md` |
| アクションプラン | `C:/Users/ninni/projects/life/docs/action-plan.md` |
| 会計方針 | `C:/Users/ninni/projects/gcp-main-project-477501/accounting_policies.md` |
| NocoDB | nocodb スキル経由 |
| freee | freee スキル経由 |

## NocoDB テーブルID

| テーブル | ID |
|---------|-----|
| KPI_Monthly | mtjjrfldelt8wlp |
| PDCA_Actions | m8ocl2tmdt5p0fk |
