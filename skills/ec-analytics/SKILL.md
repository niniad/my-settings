---
name: ec-analytics
description: >
  EC事業の数値分析・戦略的意思決定スキル。BigQuery MCP経由でデータ取得し、KPIレビュー・利益分析・広告効率分析を行う。
  トリガー: 「EC分析」「売上分析」「利益計算」「広告分析」「在庫確認」「月次レビュー」
  「TACOS」「ACOS」「KPI」「クロス購入」「ポートフォリオ」「BCG」「商品改廃」
---

# EC Analytics

数値に基づく戦略的意思決定。BigQuery Report層 VIEW + NocoDB で分析・記録する。

---

## 0. 判断原則（最優先で読む）

### シグナルの4分類

| 分類 | 定義 | 対応 |
|---|---|---|
| **ノイズ** | 月間±15-20%の変動。月200件程度の注文では偶然の範囲 | **何もしない。** 次月確認 |
| **トレンド** | 3ヶ月以上同方向に動いている変化 | 原因調査。市場要因か自社要因かを分離 |
| **構造変化** | 原価改定、新競合、カテゴリ規模変動、Amazon手数料改定 | 対応策の検討。中長期視点 |
| **危機** | 在庫切れ、連続赤字、アカウント問題 | 即時対応 |

> **重要**: 月間注文200件・ASIN単位で5-39件の事業規模では、月次の変動の大半はノイズ。
> 「まだ判断できない」は正しい結論。無理にアクションをひねり出さないこと。

### アクション優先度

| 優先度 | 基準 | 例 |
|---|---|---|
| **高: 低労力×高効果** | 数時間で完了、P&Lに直接影響 | 赤字商品の広告停止、在庫補充発注 |
| **中: 中労力×高効果** | 数日かかるが売上構造を変える | タイトル・画像改善、新バリエーション追加 |
| **低: 高労力×不確実** | 時間がかかり効果不明 | KW個別最適化、新カテゴリ参入調査 |
| **保留** | データ不足 | 判断可能になる条件を定義して保留 |

### 事業継続の判断基準

| 条件 | 判断 |
|---|---|
| Settlement営業利益が **3ヶ月連続赤字** | 構造的問題。原因分析と改善期限を設定 |
| 6ヶ月平均利益が **時給換算で最低賃金未満** | ピボットまたは撤退の検討 |
| 市場全体が **6ヶ月以上縮小トレンド** | カテゴリの将来性を再評価 |

---

## 1. データ量の限界（これを無視した判断は全て無効）

| 粒度 | 信頼性 | 用途 |
|---|---|---|
| **事業全体×月次** | ±30%以上は検出可能 | KPI監視、損益判断 |
| **商品カテゴリ×月次** | 傾向の参考値 | ポートフォリオ判断 |
| **個別ASIN×月次** | 月5-39件。統計的判断は**不可能** | 在庫管理の参考のみ |
| **キャンペーン×掲載枠** | 20クリック未満はゼロ判断も困難 | 20クリック以上で「ゼロか否か」を判断 |
| **キーワード/ターゲット単位** | 20クリック未満はゼロ判断も困難 | 停止基準は費用閾値（クリック数より優先） |

> **sp_placementsテーブルの既知制約**: `sales14d`/`purchases14d` は常にnull。
> 掲載枠別の売上・CVRは `amazon_ads_v1_external.sp_product_search_term_placements` から取得する。

---

## 2. 広告分析フレームワーク

詳細（分析軸・操作軸・停止基準・掲載枠調整・クロス購入）: [references/advertising-analysis.md](references/advertising-analysis.md)

**必須確認フロー:**
1. 分析軸で問題の所在を特定（KW×掲載枠で確認）
2. 変更対象の粒度でクリック数が20以上か確認
3. 操作軸に変換して変更を提案
4. キャンペーン単位のACOSだけで変更を提案しない

---

## 3. データアーキテクチャ（4層）

### Source層（変更不可）
| データセット | 内容 |
|---|---|
| `sp_api_external` | Amazon SP-API生データ（注文・在庫・Settlement） |
| `amazon_ads_external` | 広告API生データ（SPキャンペーン・キーワード・商品広告） |
| `amazon_ads_v1_external` | 広告API v1（**クロス購入** を含む） |
| `nocodb` | NocoDB同期データ（原価・商品マスタ） |
| `accounting` | 会計ビュー（仕訳・P&L・BS） |

### Staging層（VIEW）
| ビュー | 用途 |
|---|---|
| `stg_sp_traffic_child_asin` | 日次×子ASIN売上・トラフィック |
| `stg_sp_traffic_daily` | 日次全体サマリー |
| `stg_sp_settlement` | Settlement明細 |
| `stg_sp_inventory` | FBA在庫 |
| `stg_ads_campaign_daily` | キャンペーン日次 |
| `stg_ads_keyword_daily` | キーワード日次 |
| `stg_ads_product_daily` | 商品広告日次 |
| `stg_ads_search_term_daily` | 検索語句日次 |
| `stg_ads_cross_purchase` | クロス購入 |
| `stg_sqp_weekly` | 検索クエリパフォーマンス週次 |
| `stg_cost_standard` | **原価の正本** |

### Report層（Claudeが直接叩く）
| ビュー | 用途 |
|---|---|
| `rpt_data_freshness` | **最初に確認。** 各データソースの鮮度 |
| `rpt_kpi_monthly` | 月次KPIダッシュボード |
| `rpt_kpi_weekly` | 週次KPI + 月次目標進捗率 |
| `rpt_profit_variance_monthly` | 利益変動の前月比ウォーターフォール分解 |
| `rpt_pnl_monthly_detail` | 経費内訳P&L |
| `rpt_pnl_monthly_sku` | 月次SKU別P&L |
| `rpt_product_profitability` | 商品別収益性 + BCG分類 |
| `rpt_market_trend_monthly` | 市場トレンド分析 |
| `rpt_ad_campaign_performance` | キャンペーン月次パフォーマンス |
| `rpt_ad_keyword_efficiency` | キーワード効率分析 |
| `rpt_ad_cross_purchase` | クロス購入サマリー + 真のROAS |
| `rpt_weekly_asin_with_sqp` | 週次ASIN + 市場データ |
| `rpt_inventory_health` | 在庫健全性 |
| `rpt_repeat_purchase` | リピート購入分析 |

全VIEWは `analytics` データセット内。

### 売上・利益の2系統

| 系統 | カラム | 即時性 | 用途 |
|------|--------|--------|------|
| **Traffic系** | `total_sales`, `estimated_profit` | 翌日反映 | トレンド監視 |
| **Settlement系** | `settlement_sales`, `settlement_profit` | 1-2週遅延 | **損益判断** |

> `estimated_profit` は実際の利益より¥10-30万高い。絶対にこれだけで利益の良否を判断しないこと。

---

## 4. 月次レビュー手順

KPI定義・目標値: [references/kpi-targets.md](references/kpi-targets.md)

```
■ Phase 0: コンテキストロード（主会話で実行、サブエージェント不可）
> **Phase 0 は月次レビューだけでなく、全ての分析タスク（アドホック分析・広告判断・撤退判断等）で必須。**
> 対象商品やキャンペーンに関連するPDCA_ActionsとEC_Data_Insightsを必ず取得してから分析を開始する。
0-1. NocoDB EC_Data_Insights（Status=有効）を全件取得
0-2. NocoDB PDCA_Actions（Category=EC, Status≠完了,中止）を全件取得
0-3. Insights + Actions を要約表示（既知異常値、進行中アクション、Related_Action紐付け）
0-4. 【運用状況サマリー】以下の形式で提示（月次レビュー時は必須、アドホック分析時は省略可）:

【運用状況 {YYYY-MM}】
📊 データパイプライン: {正常（最終: M/D）／遅延（{N}日古い）}  ← rpt_data_freshness で確認
📋 月次締め（{対象月}）: {完了 ／ 未完了（楽天銀行{N}件など）／ 明細未インポート}  ← Phase 1b で確認
⏰ PDCA 期限アラート: {期限切れ or 3日以内のアクション名 ／ なし}
📈 進行中アクション: {N}件（内容は上記 0-3 参照）

> 運用カレンダー詳細: [references/operations-calendar.md](references/operations-calendar.md)

■ Phase 1: 状況把握
1. データ鮮度: rpt_data_freshness（rpt_data_freshnessの監視対象外のテーブルも個別確認）
   - fact_daily_asin の鮮度を必ず個別確認: `SELECT MAX(report_date), DATE_DIFF(CURRENT_DATE(), MAX(report_date), DAY) as days_stale FROM \`main-project-477501.analytics.fact_daily_asin\``
   - days_stale > 3 の場合: **分析停止**。「fact_daily_asinが{days_stale}日古い。KPI・日販ベースの指標が不正確」と警告
1b. 月次締め完了チェック（BQ nocodb データセット）:
   BQ の nocodb データセットで未分類取引（勘定科目未設定かつ振替でない）を検出する:
   ```sql
   SELECT source_table, COUNT(*) AS unclassified_count
   FROM (
     SELECT '楽天銀行' AS source_table
     FROM `main-project-477501.nocodb.rakuten_bank_statements`
     WHERE LEFT(transaction_date, 7) = '{対象月}'
       AND is_transfer = FALSE AND freee勘定科目_id IS NULL
     UNION ALL
     SELECT 'PayPay銀行'
     FROM `main-project-477501.nocodb.paypay_bank_statements`
     WHERE LEFT(transaction_date, 7) = '{対象月}'
       AND is_transfer = FALSE AND freee勘定科目_id IS NULL
     UNION ALL
     SELECT '代行会社'
     FROM `main-project-477501.nocodb.agency_transactions`
     WHERE LEFT(transaction_date, 7) = '{対象月}'
       AND is_transfer = FALSE AND freee勘定科目_id IS NULL
   )
   GROUP BY source_table
   ```
   さらに、経費データの有無を確認:
   ```sql
   SELECT COUNT(*) AS entry_count
   FROM `main-project-477501.accounting.pl_journal_entries`
   WHERE small_category = '経費'
     AND FORMAT_DATE('%Y-%m', journal_date) = '{対象月}'
     AND source_table NOT IN ('amazon_settlement')
   ```
   判定ロジック:
   - **未分類あり** → 「{source}: {N}件の未分類取引があります。NocoDB で科目設定後、`cd C:/Users/ninni/infra/nocodb-to-bq && uv run python main.py` を実行してください。固定経費は算出不可。Settlement P&L のみで続行。」
   - **未分類0件・経費データ0件** → 「{対象月}の銀行明細がインポートされていません。NocoDB にインポートし、科目設定後に nocodb-to-bq 同期を実行してください。」
   - **未分類0件・経費データあり** → 月次締め完了。Phase 3c を実行。事業主借の有無はデータから自動判定される（個別に聞く必要なし）
2. KPI取得: rpt_kpi_monthly（当月+3ヶ月推移）
3. 閾値判定: sales/profit/tacos/cvr_status

■ Phase 2: シグナル判定
4. シグナル4分類 → ノイズなら Phase 4 へスキップ

■ Phase 3: 深掘り（トレンド/構造変化/危機のみ）
5. 変動分解 → 主因に応じた深掘り → 商品別 → P&L → 広告 → 在庫
※ 異常検出時: Insights→既知? Actions→対応済み? → いずれも該当なしなら新規発見

■ Phase 3b: 広告深掘り（広告が主因の時）
references/advertising-analysis.md のフレームワークに従って分析する。
必ず「分析軸で確認 → クリック数チェック → 操作軸に変換」の順で進める。

■ Phase 3c: 固定経費分析（月次レビュー時は毎回必須）
Phase 1b でデータあり確認済みの場合のみ実行。データなしの場合は依頼メッセージを再掲して終了。

```sql
-- 固定経費内訳（Settlement由来を除外して二重計上を防ぐ）
SELECT
  account_name,
  SUM(-pl_contribution) AS amount
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE small_category = '経費'
  AND FORMAT_DATE('%Y-%m', journal_date) = '{対象月}'  -- e.g. '2026-02'
  AND source_table NOT IN ('amazon_settlement')  -- Settlement P&L に含まれる広告費・手数料を除外
GROUP BY account_name
ORDER BY amount DESC
```

上記クエリ結果と Settlement 利益（`rpt_pnl_monthly_detail` の settlement_profit）を合算し、
以下の形式で**完全営業利益**を表示する:

```
【完全営業利益 {対象月}】
Settlement 利益（変動費差引後）    : ¥XXX,XXX
  ├ 売上高                         : ¥XXX,XXX
  ├ 売上原価                       : -¥XX,XXX
  ├ Amazon手数料（FBA・紹介料等）  : -¥XX,XXX
  └ 広告費                         : -¥XX,XXX
固定経費                           : -¥XX,XXX
  ├ [科目名]                       : -¥X,XXX
  ├ [科目名]                       : -¥X,XXX
  └ ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完全営業利益                       : ¥XXX,XXX  ← これが事業の実力値
```

> **注**: Settlement 利益は `rpt_pnl_monthly_detail` の settlement_profit カラムを使用。
> 固定経費が当月未入力の場合は「固定経費: 未入力（参考値）」として Settlement 利益のみ表示する。

■ Phase 4: 戦略判断とアクション提示
6-0. 広告変更を推奨する前に、advertising-analysis.md Step 0 を必ず実施。
     Status=検証中 かつ DueDate > 今日 のアクションが対象キャンペーンと重複する場合は変更提案を禁止し、中間経過のみ報告する（analysis-rules.md ルール2参照）。
6. アクション提示（優先度順）+ PDCA_Actions/EC_Data_Insights に記録
```

## 5. 週次チェック（毎週月曜）

1. `rpt_kpi_weekly` で月次目標に対する進捗率
2. `rpt_inventory_health` で在庫アラート
3. 進行中アクション確認
※ 週次では深掘りしない

---

## 6. アクション管理

- **記録先**: NocoDB PDCA_Actions（CLAUDE.md参照）
- 広告変更等の実行前に必ずユーザー承認
- **効果測定**: 施策前後1ヶ月比較、カテゴリ単位、市場トレンド排除

### PDCA_Actions 記録フォーマット（広告関連）

```
Title: [商品略称]_[キャンペーン名]_[変更内容の概要]

Detail フィールドに必須記載:
・キャンペーン名（完全名）とID
・変更したKW/ターゲット名（完全表記）
・変更した掲載枠
・変更前 → 変更後（数値で）
・変更理由（ACOS, クリック数, 損益分岐との比較など）
・検証条件（いつ、何の数値で効果を判定するか）
```

**「変更前の値」と「キャンペーン名・KW名の完全表記」は絶対に省略しない。**

---

## 7. 知見管理（EC_Data_Insights）

- 記録: 数値異常の原因、季節パターン、確定済み事業判断、データ障害
- Related_Action: 対応済みアクションと紐付け → 重複調査防止
- Category選択肢: `異常値` / `季節パターン` / `事業判断` / `データ障害`

---

## 8. 広告設定（ads_api.py スクリプト）

スクリプトパス: `.claude/skills/ec-analytics/scripts/ads_api.py`

| 目的 | コマンド例 |
|------|-----------|
| 過去のパフォーマンス | BigQuery Report層 |
| キャンペーン一覧 | `uv run ads_api.py list_campaigns [--state ENABLED]` |
| キーワード一覧 | `uv run ads_api.py list_keywords --campaign-id <id>` |
| ターゲット一覧 | `uv run ads_api.py list_targets --campaign-id <id>` |
| 入札額変更 | `uv run ads_api.py update_keyword_bid --keyword-id <id> --bid <円>` |
| ON/OFF切替 | `uv run ads_api.py update_campaign_state --campaign-id <id> --state PAUSED` |
| 予算変更 | `uv run ads_api.py update_campaign_budget --campaign-id <id> --budget <円>` |

実行は必ずプロジェクトルート（`C:/Users/ninni/projects/ec`）から行う。

**書き込み操作の手順（厳守）：**
1. **分析提示**: データに基づく変更理由と期待効果を提示
2. **ユーザー確認**: 変更内容を具体的に列挙し、明示的な承認を得る
3. **実行**: 承認後のみ `uv run` で実行
4. **結果報告**: 変更後の状態をリスト系コマンドで確認し報告

安全策: ARCHIVED除外。入札額上限5,000円。予算上限100,000円。

---

## 分析パターン一覧

詳細SQL: [references/analysis-patterns.md](references/analysis-patterns.md)

| # | 分析 | Report VIEW | 頻度 |
|---|------|---|---|
| 0 | **データ鮮度確認** | `rpt_data_freshness` | **毎回最初** |
| 1 | 月次KPIレビュー | `rpt_kpi_monthly` | 月次 |
| 2 | 利益変動分解 | `rpt_profit_variance_monthly` | 月次 |
| 3 | 経費内訳P&L（変動費） | `rpt_pnl_monthly_detail` | 経費が主因の時 |
| 3b | 固定経費内訳（完全営業利益） | `accounting.pl_journal_entries` | **月次必須**（Phase 3c） |
| 4 | SKU別P&L | `rpt_pnl_monthly_sku` | 月次 |
| 5 | 商品別収益性 | `rpt_product_profitability` | 月次 |
| 6 | 市場トレンド | `rpt_market_trend_monthly` | 売上が主因の時 |
| 7-9 | 広告分析 | `rpt_ad_*` | 月次/広告変更時 |
| 10 | 週次＋市場データ | `rpt_weekly_asin_with_sqp` | 週次 |
| 11 | 在庫健全性 | `rpt_inventory_health` | 月次 |
| 12 | リピート購入 | `rpt_repeat_purchase` | 四半期 |
