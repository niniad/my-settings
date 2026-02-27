---
name: ec-analytics
description: >
  EC事業（Amazon FBA お食事エプロン・マザーズリュック）の戦略的意思決定スキル。
  BigQuery MCP経由でデータ取得し、事業利益の最大化に向けた判断を支援する。
  トリガー: 「EC分析」「売上分析」「利益計算」「広告分析」「在庫確認」「月次レビュー」
  「エプロン」「マザーズリュック」「3枚セット」「TACOS」「ACOS」「KPI」
  「クロス購入」「商品ポートフォリオ」「BCG」「商品改廃」「新商品」
---

# EC Analytics

## このスキルの目的

EC事業の**利益最大化**のための戦略的意思決定を支援する。広告効率の微調整ではなく、以下を含む事業全体の判断を行う:

- 商品ポートフォリオの最適化（改廃・新バリエーション・新カテゴリ）
- 商品ページの改善（クリエイティブ・タイトル・箇条書き）
- 広告・在庫の運用判断
- 事業継続/ピボット/撤退の判断

**個人事業主が1人で運営する前提**で、手間と効果のバランスを常に考慮する。

---

## 判断フレームワーク

### シグナルの4分類

月次レビューの最初に、KPIの変動を以下の4つに分類する。分類によって対応が異なる。

| 分類 | 定義 | 対応 |
|---|---|---|
| **ノイズ** | 月間±15-20%の変動。月200件程度の注文では偶然の範囲 | **何もしない。** 次月確認 |
| **トレンド** | 3ヶ月以上同方向に動いている変化 | 原因調査。市場要因か自社要因かを分離（rpt_market_trend_monthly） |
| **構造変化** | 原価改定、新競合、カテゴリ規模変動、Amazon手数料改定 | 対応策の検討。中長期視点 |
| **危機** | 在庫切れ、連続赤字、アカウント問題 | 即時対応 |

> **重要**: 月間注文200件・ASIN単位で5-39件の事業規模では、月次の変動の大半はノイズである。
> 「わからない」「まだ判断できない」は正しい結論。無理にアクションをひねり出さないこと。

### アクション優先度（個人事業主向け）

| 優先度 | 基準 | 例 |
|---|---|---|
| **高: 低労力×高効果** | 数時間で完了、P&Lに直接影響 | 赤字商品の広告停止、在庫補充発注、明らかに非効率な支出の削減 |
| **中: 中労力×高効果** | 数日かかるが売上構造を変える可能性 | 商品タイトル・画像の改善、新バリエーション追加、高利益率商品の強化 |
| **低: 高労力×不確実** | 時間がかかり効果が読めない | 広告キーワード個別最適化、新カテゴリ参入調査 |
| **保留** | データ不足で判断不可能 | 明示的に「保留」と記録し、判断可能になる条件を定義 |

「現状維持がベター」と判断できれば、中長期的に注力すべきアクション（商品開発、ページ改善等）を提案する。

### 事業継続の判断基準

以下に該当する場合、`life` プロジェクトの `action-plan.md` にエスカレーションする。

| 条件 | 判断 |
|---|---|
| Settlement営業利益が **3ヶ月連続赤字** | 構造的問題の可能性。原因分析と改善期限を設定 |
| 6ヶ月平均利益が **時給換算で最低賃金未満** | ピボットまたは撤退の検討を開始 |
| 市場全体が **6ヶ月以上縮小トレンド** | カテゴリの将来性を再評価 |

### データ量の限界

この事業規模（月間注文~200件）で信頼できる判断の粒度:

| 粒度 | 信頼性 | 用途 |
|---|---|---|
| **事業全体×月次** | 大きな変動（±30%以上）は検出可能 | KPI監視、損益判断 |
| **商品カテゴリ×月次** | 傾向の参考値（エプロン全体、リュック全体） | ポートフォリオ判断 |
| **個別ASIN×月次** | 月5-39件。統計的判断は**不可能** | 在庫管理の参考のみ |
| **個別ASIN×週次** | ほぼノイズ | 判断材料としない |

> 個別ASINレベルでCVRが先月5%→今月3%に下がっても、注文数10件→6件の差に過ぎず、偶然の範囲。

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
■ Phase 1: 状況把握
0. データ鮮度: rpt_data_freshness で全ソースの状態確認。異常があれば報告
1. KPI取得: rpt_kpi_monthly で当月+3ヶ月推移。data_quality列を必ず確認
2. 閾値判定: sales_status/profit_status/tacos_status/cvr_status を確認
   ※ profit_status はSettlement基準。当月は「集計中」なので前月以前で判断

■ Phase 2: シグナル判定（最重要）
3. 変動をシグナル4分類に判定:
   - ノイズ（±15-20%、単月の変動）→ Phase 4 へスキップ
   - トレンド（3ヶ月以上同方向）→ Phase 3 へ
   - 構造変化（原価改定、新競合等）→ Phase 3 へ
   - 危機（連続赤字、在庫切れ等）→ Phase 3 へ（即時対応）

■ Phase 3: 深掘り（トレンド/構造変化/危機の場合のみ）
4. 変動分解: rpt_profit_variance_monthly で前月比の利益変動要因を特定（primary_driver）
5. 主因に応じた深掘り:
   - 売上変動 → rpt_market_trend_monthly で市場要因 vs 自社要因を判別
   - 経費変動 → rpt_pnl_monthly_detail で手数料内訳・固定費を確認
   - 広告費変動 → rpt_ad_campaign_performance でキャンペーン別効率を確認
6. 商品別: rpt_product_profitability で利益貢献上位/下位を特定
7. P&L: rpt_pnl_monthly_sku でSKU別の利益構造を確認
8. 広告: rpt_ad_cross_purchase で真のROAS確認（広告変更検討時のみ）
9. 在庫: rpt_inventory_health で補充アラート確認

■ Phase 4: 戦略判断とアクション提示
10. 事業継続判断: 3ヶ月連続赤字等の基準に該当するか確認
11. アクション提示（優先度順）:
    - 即時対応が必要なもの（危機の場合）
    - 低労力×高効果のアクション
    - 「現状維持」の場合は中長期アクション（商品開発、ページ改善等）を提案
    - 「今やらないこと」を明示（過剰な最適化の抑制）
12. 記録: NocoDB KPI_Monthly にスナップショット、PDCA_Actions にアクション
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
2. rpt_inventory_health で在庫アラート（2ヶ月未満 or 8ヶ月超）
3. 進行中アクションの進捗確認
※ 週次では深掘り分析しない。異常値があっても月次で判断する（データ量不足のため）
```

## アクション管理

### 記録
- 全てのアクションを NocoDB `PDCA_Actions`（m8ocl2tmdt5p0fk）に記録
- 記録項目: 日時、アクション内容、変更前後の値、理由、期待効果
- 広告変更等の実行前に必ず**ユーザー承認**を得る

### 効果測定の原則
- **評価期間**: 施策前1ヶ月 vs 施策後1ヶ月（7日では判断不可能）
- **評価粒度**: カテゴリ単位（エプロン全体 / リュック全体）。個別ASINでは統計的に判断できない
- **複合観察**: 注文数・セッション数・CVR・impression_shareが同方向に動いていれば効果の可能性が高い
- **市場トレンド排除**: rpt_market_trend_monthly で市場全体の変動を差し引いて評価する
- **広告の間接効果**: 広告費の月次推移と翌月のオーガニックセッション・impression_shareの推移を並べて相関を観察（因果の証明ではなく整合性の確認）
- **結論が出ない場合**: 「データ不足で判断不可」と明示。追加の観察期間を設定して保留

### アクションの分類

| 種類 | 例 | 評価方法 |
|---|---|---|
| **短期戦術** | 広告停止/再開、在庫発注 | 翌月のP&L変動で確認 |
| **中期改善** | クリエイティブ改善、タイトル最適化 | 2-3ヶ月後のセッション・CVR推移で観察 |
| **長期戦略** | 新商品導入、カテゴリ参入/撤退 | 6ヶ月後のポートフォリオ収益性で評価 |

中期・長期アクションの効果は、個別の因果関係ではなく、ポートフォリオ全体の収益性トレンドで判断する。

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
