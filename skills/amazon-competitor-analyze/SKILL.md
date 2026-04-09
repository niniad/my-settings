---
name: amazon-competitor-analyze
description: >
  Amazon競合データの取得・整形・8軸クリエイティブ分析スキル。
  SP-API + agent-browser でデータ取得 → CSV整形 → 8軸分析 → competitor-analysis.md 出力。
  トリガー: 「競合分析」「competitor-analyze」「競合データ取得」「8軸分析」「ASIN分析」
  「レビュー取得」「A+取得」「BSR取得」「販売数推定」「競合画像」
allowed-tools: Bash(uv run *), Bash(npx agent-browser:*)
---

# Amazon Competitor Analyze

SP-API + agent-browser でAmazon.co.jp競合データを取得し、8軸クリエイティブ分析まで一括実行する**グローバルスキル**。
どのプロジェクトからでも呼び出し可能。スクリプトは絶対パスで動作。

## データ保存先

### Eagle（元データ保管庫）
JSONはtmp→Eagle登録→tmp削除のパターン。

```
Eagle: Amazon競合データ/
  {product_name}/             ← --product で指定（例: マザーズリュック）
    {子ASIN}/                 ← fetch_catalog.pyに渡されたASIN単位
      catalog_YYYYMMDD.json   ← SP-API生データ（_raw_parent含む）
      reviews_YYYYMMDD.json   ← レビュー生データ
      aplus_YYYYMMDD.json     ← A+コンテンツ生データ
      {ASIN}_APLUS_01.jpg     ← A+画像
```

### ローカル（AI作業用CSV）
build_competitor_csv.py でEagle内JSONをCSV化。Phase 0 の入力データ。

```
ec/products/{slug}/competitor-data/
  catalog.csv   ← 全競合の商品仕様（_raw_parentフラット化。カラム動的）
  reviews.csv   ← 全レビュー（variation付き）
  images.csv    ← 商品画像URL + A+画像パス + テキスト抽出結果
```

**ASIN用語**:
- `child_asin`: Eagleフォルダ名のASIN（fetch_catalog.pyに渡された子ASIN）
- `parent_asin`: 真の親ASIN（_raw_parent.relationships から解決）

## スクリプトパス

```
C:/Users/ninni/.claude/skills/amazon-data/scripts/
  fetch_catalog.py         ← SP-API Catalog Items取得（親ASIN自動解決・全バリエーション展開）
  fetch_reviews.py         ← agent-browserでレビュー取得（バリエーション別情報含む）
  fetch_aplus.py           ← agent-browserでA+コンテンツ取得
  bsr_to_sales.py          ← BSR→販売数変換
  build_competitor_csv.py  ← Eagle内JSON → ローカルCSV参照用ファイル生成
```

---

## 事前確認（agent-browser使用時）

fetch_reviews.py・fetch_aplus.py は agent-browser を使用する。実行前に確認:

1. **Eagleが起動している**こと
2. **agent-browserのAmazonセッションが確立されている**こと
   - 初回またはセッション切れの場合: `npx.cmd agent-browser --session-name amazon-jp open https://www.amazon.co.jp` でブラウザを開き、Amazonにログインしてからスクリプトを実行する
   - セッションは `~/.agent-browser/sessions/amazon-jp-default.json` に自動保存される
   - 一度ログインすれば次回以降は自動再利用

---

## コマンドリファレンス

### fetch_catalog.py — 商品情報・BSR・全バリエーション画像取得

SP-APIを使用。Chromeは不要。

```bash
# 子ASINでも親ASINでも可（自動で親に解決して全子ASIN取得）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_catalog.py \
  --asins B091NQ5WXY B0FB8Z8RZV --product マザーズリュック

# 複数商品（同じ親の子ASINを複数渡しても1回だけ取得）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_catalog.py \
  --asins B000AAA B000BBB B000CCC --product マザーズリュック
```

**取得内容**: 商品名・箇条書き・BSR（カテゴリ別）・全バリエーション（色・サイズ等）・画像・カテゴリ

### fetch_reviews_playwright.py — 全★レビュー取得（Playwright版・汎用）

```bash
SCRIPT_DIR=C:/Users/ninni/.claude/skills/amazon-competitor-analyze/scripts

# 初回のみ: ブラウザが開くのでAmazonにログイン→ブラウザを閉じる
uv run $SCRIPT_DIR/fetch_reviews_playwright.py --login

# 推奨: catalog.csvから全商品の全★レビューを一括取得
uv run $SCRIPT_DIR/fetch_reviews_playwright.py \
  --catalog path/to/competitor-data/catalog.csv \
  --output path/to/competitor-data/reviews.json

# ASIN直接指定（テスト用）
uv run $SCRIPT_DIR/fetch_reviews_playwright.py --asins B091NQ5WXY

# CAPTCHAが出た場合: ペースを遅くして再実行
uv run $SCRIPT_DIR/fetch_reviews_playwright.py --catalog ... --pace slow
```

**仕組み**:
- catalog.csvの子ASIN→親ASINを自動解決。両方試行してレビューページが存在する方を使用
- ★別フィルタ（1-5★）で全レビューを偏りなく取得
- 「さらに10件表示」ボタンをクリックして全件読み込み（URLページネーションは無効）
- 人間のブラウジング速度でアクセス（normal: 4-7秒/ページ）。8商品ごとに45秒休憩
- CAPTCHA検出時は即中断（取得済み分は保持）
- セッションは `~/.playwright-amazon/` に永続保存（初回ログイン後は自動再利用）
- inline script dependenciesでどのプロジェクトからでも `uv run` で実行可能

**注意**:
- 旧agent-browser版 `fetch_reviews.py` は非推奨。この Playwright版を使うこと
- 在庫切れ商品はレビューページが存在しない場合がある（自動スキップ）
- 37社で約1時間（normalペース）

### fetch_product_page.py — 価格・評価・スペック取得（Playwright版・汎用）

```bash
SCRIPT_DIR=C:/Users/ninni/.claude/skills/amazon-competitor-analyze/scripts

uv run $SCRIPT_DIR/fetch_product_page.py --asins B091NQ5WXY B0FB8Z8RZV
uv run $SCRIPT_DIR/fetch_product_page.py --asins B091NQ5WXY --output prices.json
```

**仕組み**: Playwright headlessで商品ページ（/dp/ASIN）にアクセス。ログイン不要。
**取得内容**: 販売価格、評価、レビュー数、★分布、**スペック表の全key-value**（カテゴリ非依存）、箇条書き全文
**注意**: `specs`フィールドに商品詳細テーブルの全項目がkey-value形式で入る。カテゴリ固有のスペック（重量、容量等）は分析時にここから取得する

### fetch_aplus.py — A+コンテンツ取得（agent-browser使用）

```bash
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_aplus.py \
  --asins B000PARENT1 B000PARENT2 --product マザーズリュック
```

**注意**: 親ASINを推奨（Amazonが自動的にデフォルトバリエーションにリダイレクト）。

### bsr_to_sales.py — BSR→販売数推定

```bash
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/bsr_to_sales.py \
  estimate --bsr 500 --category baby_products

uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/bsr_to_sales.py \
  estimate --bsr 500 --category baby_products/diaper_bags
```

---

## build_competitor_csv.py — Eagle → ローカルCSV変換

Eagle内の元データ（JSON）を読み取り、3つのCSVファイルをローカルに出力する。

```bash
# 基本（CSV生成のみ）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/build_competitor_csv.py \
  --product マザーズリュック \
  --output C:/Users/ninni/projects/ec/products/mothers-backpack/competitor-data

# テキスト抽出付き（Gemini Vision で商品サブ画像をOCR。API課金あり）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/build_competitor_csv.py \
  --product マザーズリュック \
  --output C:/Users/ninni/projects/ec/products/mothers-backpack/competitor-data \
  --extract-text
```

**出力ファイル（3つ）**:

| CSV | 内容 | 主なカラム |
|-----|------|-----------|
| `catalog.csv` | 商品仕様一覧（_raw_parentフラット化。カラムは動的） | child_asin, parent_asin, title, brand, color, size, bsr_rank_1, bsr_category_1, bullet_1-N, has_reviews, has_aplus |
| `reviews.csv` | 全レビュー | child_asin, parent_asin, variation, star, title, body, date |
| `images.csv` | 商品画像URL + A+画像パス + テキスト | child_asin, parent_asin, source, variant, url, eagle_path, text |

**catalog.csv の特徴**:
- SP-APIの `_raw_parent` を完全フラット化。カラムは商品・カテゴリにより動的に変わる
- BSR、寸法、重量、バリエーション情報も含む
- `has_reviews` / `has_aplus` でデータ有無を確認可能

**images.csv の特徴**:
- `source=product`: 商品画像URL（MAIN/PT01〜PT08）。`--extract-text` でサブ画像のテキストをOCR
- `source=aplus`: A+画像（eagle_path付き）。A+テキストデータをtext列に紐付け

**reviews.csv のクリーンアップ**:
- `variation`: "Amazonで購入" → 空欄に自動補正。"色: ブラック" 等は保持
- `title`: スクレイパーバグで星評価が入っている場合 → 空欄に自動補正

### データ取得後の自動実行

fetch_catalog / fetch_reviews / fetch_aplus でデータ取得が完了したら、
**必ず build_competitor_csv.py を実行**してローカルCSVを最新化すること。

---

## Phase 0: 競合クリエイティブ分析（8軸）

CSVデータ + Eagle画像を入力として、商品ページのクリエイティブ戦略を分析する。
**出力**: `ec/products/{slug}/competitor-data/competitor-analysis.md`

### データ参照方法

| やりたいこと | 方法 |
|------------|------|
| 競合の商品仕様を比較 | `catalog.csv` を Read |
| レビュー分析 | `reviews.csv` を Read |
| 競合画像のテキスト分析 | `images.csv` の `text` 列を Read |
| 競合画像を視覚的に分析 | `images.csv` の `url`（商品画像）または `eagle_path`（A+画像）を Read |

### 8軸分析

| # | 軸 | 見つけるもの |
|---|-----|-------------|
| ① | メッセージング | 競合が言っていない訴求軸。「誰も言っていないが顧客が求めていること」 |
| ② | ビジュアル戦略 | 視覚的に違う見せ方。構図・背景・モデル・撮影スタイルの差 |
| ③ | 購買心理フロー | 画像の並び順から読み取れる意図。最も効果的な訴求順序 |
| ④ | レビュー・VOC | セグメント×シグナルタイプで構造化分析。テーブルステークス・USP検証・差別化機会を導出。分析の限界を明示 |
| ⑤ | サムネイル戦場 | 検索結果で目を引く方法。「自社が埋もれないか」 |
| ⑥ | 価格帯別ポジショニング | 価格帯に合う訴求スタイル。安すぎると品質を疑われる |
| ⑦ | A+ベンチマーク | 商品説明欄の構成パターン。競合が力を入れているモジュール |
| ⑧ | 時系列変化 | 画像変更とBSR変動の因果。「変えたら売れた」パターン |

### ④ レビュー・VOC 分析手順（詳細）

レビュー分析は他の7軸と異なり、**2エージェント × 6段階プロセス**で実行する。
KW出現頻度カウントだけでは文脈を見落とす（800gへの「重い」批判と400gへの「軽かった」確認は全く異なるシグナル）。

#### 思考規律（hypothesis-actionフレームワークから借用）

全てのInsight記述に以下を適用する:
1. **根拠の明示**: 件数・セグメント・★帯を必ず記載
2. **反証探索（別エージェント）**: コンテキスト汚染を防ぐため、分析と反証は別エージェントで実行
3. **確信度ラベル**: 各Insightに3段階ラベルを付与

```
**Insight**: [主張]
- 根拠: [件数, セグメント, ★帯]
- 反証: [反証エージェントの報告。件数・具体的レビュー引用]
- 確信度: 強い根拠 / 一定の示唆 / 推測レベル
- 限界: [このデータからは言えないこと]
```

**確信度の判定基準**:
- **強い根拠**: 50件以上 + 複数セグメントで一貫 + 反証なし
- **一定の示唆**: 10件以上 + 方向性一貫 + 反証軽微
- **推測レベル**: 10件未満 or セグメント間で矛盾 or 反証あり

#### 5つのシグナルタイプ（全カテゴリ共通）

| タイプ | 定義 | 抽出元 | appeal-mapへの意味 |
|---|---|---|---|
| **未充足ニーズ** | 欲しいが満たされなかった | ★1-3不満 + ★4「惜しい」 | 自社で満たせれば差別化 |
| **期待確認** | 期待通りだった（良い意味の当たり前） | ★4-5の「当然」的トーン | テーブルステークス候補 |
| **想定外の満足** | 予想以上だった・思わぬ使い方 | ★4-5の驚き・発見 | 隠れたUSP候補 |
| **期待裏切り** | 訴求に反して不満足 | ★1-2の怒り + ★3落胆 | 不安解消訴求の必要性 |
| **妥協の受容** | 不満はあるが許容範囲 | ★3-4の「まあこんなもの」 | 自社が超えればアップセル可能 |

#### 2エージェント構成（確証バイアス防止）

| # | エージェント | 入力 | 役割 |
|---|---|---|---|
| 1 | **分析エージェント** | reviews.csv + catalog.csv | Stage 0-4を実行。Insightリストを出力 |
| 2 | **反証エージェント**（別コンテキスト） | reviews.csv + catalog.csv + **Insightリストのみ** | 各Insightに対して生データを独自に読み、矛盾する事例を報告 |

反証エージェントは分析プロセスを知らない（結論リストだけ受け取る）。
「この結論を覆すレビューはあるか？」だけに集中する。

#### 6段階プロセス

**Stage 0: セグメント軸の決定**
1. catalog.csvのスペック列と価格から、購買判断に最も影響する2-3の属性を特定
2. 各属性で2-3の帯域に分割（データの自然なクラスタに従う）
3. セグメント軸とその根拠を④-Aに記載

**Stage 1: サンプリング + シグナル分類（分析エージェント）**
1. reviews.csvとcatalog.csvをJOINし、各レビューにセグメント情報を付与
2. セグメント × ★帯（★1-2 / ★3 / ★4 / ★5）ごとにレビューをサンプリング（各セル最大20件、計200-400件）
3. 各レビューを5つのシグナルタイプに分類（1つのレビューが複数シグナルを含む場合は複数分類）
4. 代表的なレビューを引用とともに記録

**Stage 2: 定量バリデーション**
1. Stage 1で特定されたシグナルに対応するKWを定義
2. reviews.csv全件に対してセグメント別KWカウントを実行
3. セグメント間の差異を定量化（例: 800g帯では「重い」が22%、400g帯では3%）
4. Stage 1の定性分析とStage 2の定量結果が矛盾する場合は、矛盾を明示

**Stage 3: テーブルステークス抽出**
判定基準:
1. 「期待確認」シグナルが3セグメント以上で出現
2. ★4-5レビュー全体の20%以上で言及
3. 欠如時に★1-2で不満として言及されている（「ないと怒られる」証拠）

出力テーブル: | 要素 | 期待確認の出現率 | 欠如時の不満率 | 自社充足 | 自社訴求 |

**Stage 4: USP検証 + 差別化機会導出 → Insightリスト出力**
1. 自社USP候補をリストアップ（タイトル・箇条書きから）
2. 各USPについて:
   - 自社レビューでの認知状況（シグナルタイプ別）
   - 同セグメント競合での充足状況
   - 3段階評価: **検証済USP** / **認知済だが差別化弱い** / **未認知USP**
3. 「競合の未充足ニーズ」×「自社が満たせる機能」のクロスで差別化機会を導出
4. **全Insightをリストとして出力**（次のStage 5の入力）

**Stage 5: 反証エージェント起動**
- Insightリスト + reviews.csv + catalog.csv を別エージェントに渡す
- 各Insightに対して独立に反証を探索
- 反証が見つかれば件数・具体的レビュー引用とともに報告
- 見つからなければ「確認した範囲で反証なし」と報告

**Stage 6: 統合 + 分析の限界明示**
1. 分析エージェントが反証結果をInsightに統合し、確信度ラベルを付与
2. 以下の限界を必ず記載:
   - レビュー総数と各セグメントの件数偏り
   - 自己選択バイアス（レビューを書く人は極端な意見に偏る）
   - 検証不能: 「購入しなかった人の理由」はレビューからは分からない
   - KWカウントの限界: 同じKWでも文脈で意味が異なる（Stage 1で補完しているが完全ではない）

#### competitor-analysis.md ④セクション構成

```
④ レビュー・VOC
  ④-A. 分析フレームワーク（セグメント軸定義・シグナルタイプ・データ範囲）
  ④-B. テーブルステークス（全セグメント共通の「当然期待される」要素）
  ④-C. セグメント別シグナルマップ（セグメントごとの5シグナル分析）
  ④-D. 自社ポジション分析（USP検証結果 + テーブルステークス充足度）
  ④-E. 差別化機会（Insightフォーマットで記述。反証エージェント結果統合済み）
  ④-F. 分析の限界
```

#### 汎用化ルール

- セグメント軸はハードコードしない（分析時にcatalog.csvから動的決定）
- シグナルタイプ5種は全カテゴリ共通。追加・変更しない
- テーブルステークス閾値（20%、3セグメント以上）は目安。レビュー総数100件未満なら閾値を下げる
- 確信度ラベルの件数基準も目安。全体レビュー数に応じて比例調整する

---

### 分析の実行方法

**別エージェント（Evaluator パターン）で実行する。**
メインの会話コンテキストとは別に Agent tool で起動し、
CSVデータ + Eagle画像を渡して分析結果を出力させる。

①〜③、⑤〜⑧は1つの分析エージェントで実行。
④は上記の2エージェント構成（分析 + 反証）で実行。

1. Agent tool で `subagent_type=general-purpose` を起動（分析エージェント）
2. 分析エージェントに渡す:
   - `ec/products/{slug}/competitor-data/catalog.csv`
   - `ec/products/{slug}/competitor-data/reviews.csv`
   - `ec/products/{slug}/competitor-data/images.csv`
   - Eagle 内の競合商品画像（images.csv の url/eagle_path 参照）
3. ①〜③、⑤〜⑧ + ④のStage 0-4を実行
4. ④のInsightリストを出力
5. Agent tool で別の `subagent_type=general-purpose` を起動（反証エージェント）
6. 反証エージェントにInsightリスト + reviews.csv + catalog.csv を渡す
7. 反証結果を統合し、④のStage 6を完成
8. 出力: `ec/products/{slug}/competitor-data/competitor-analysis.md`

### appeal-map への引き渡し項目

competitor-analysis.md の以下のセクションは listing-appeal-map の入力として直接使用される:
- ④-B テーブルステークス → appeal-mapの「購入前の不安」「必須訴求要素」
- ④-D USP検証結果 → appeal-mapの「USP」「コアメッセージ」の裏付け
- ④-E 差別化機会 → appeal-mapの「訴求すべきポイント」の優先度付け
- ④-F 分析の限界 → appeal-mapの「検証が必要な前提」

### competitor-analysis.md フォーマット

```markdown
# Phase 0: 競合クリエイティブ分析

対象: {ASIN}（{商品名}）
分析日: YYYY-MM-DD
データソース: amazon-data CSV + Eagle画像

## 自社現状
- BSR / 価格 / 月間販売数 / 評価数 / A+有無

## 分析対象（競合Top10-20）
| ASIN | ブランド | BSR | 価格 | 評価数 | A+有無 |

## 8軸分析
### ① メッセージング
### ② ビジュアル戦略
...

## 差別化方針
- 訴求すべきポイント
- 避けるべきポイント（競合と同じになる表現）
- 優先度付き行動リスト
```

---

## トリガー例

| ユーザーの依頼 | 実行コマンド |
|--------------|------------|
| 「マザーズリュックの競合データを取得して」 | `fetch_catalog.py` → `build_competitor_csv.py` |
| 「このASINのレビューを取得して」 | `fetch_reviews.py` → `build_competitor_csv.py` |
| 「A+コンテンツを取得して」 | `fetch_aplus.py` → `build_competitor_csv.py` |
| 「BSR 500 のベビー用品の月間販売数を推定して」 | `bsr_to_sales.py estimate --bsr 500 --category baby_products` |
| 「競合データをCSVに更新して」 | `build_competitor_csv.py` |
| 「競合画像のテキストも抽出して」 | `build_competitor_csv.py --extract-text` |
| 「競合分析して」「8軸分析して」 | CSV + Eagle画像 → 8軸分析 → `competitor-analysis.md` |
| 「competitor-analysis を更新して」 | 最新CSV + Eagle画像で再分析 |

---

## 注意事項

- **SP-API**: 無料。レート制限 2 TPS（自動管理）
- **agent-browserスクレイピング**: 20商品以下・月2回まで。自動定期実行禁止
- **セッション切れの症状**: 0件取得・ログインページにリダイレクト → 上記「事前確認」を実行
- **セラスプ月額契約**: 新カテゴリ市場規模・キーワード逆引きはSP-APIでは代替不可 → 必要時のみ

## 関連スキル

| 状況 | スキル | 説明 |
|------|--------|------|
| 取得した画像・JSONをEagleで整理・検索したいとき | `/eagle` | Eagle APIで画像管理・フォルダ整理 |
