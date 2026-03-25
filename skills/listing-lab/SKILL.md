---
name: listing-lab
description: Amazon商品画像のA/B評価実験ラボを運営するスキル。ベンチマーク画像と生成画像をブラインド比較（subagent×3並列評価）して客観的に最良デザインを選定する。listings/lab/ディレクトリ配下のR&Dラボワークフロー全体（初期化・実験実行・評価・本番昇格）を担当する。トリガー: "listing-lab", "ラボ実験", "実験を実行", "A/B評価", "ブラインド評価", "exp-001", "ベンチマーク比較", "画像を評価して", "実験結果を記録"
---

# listing-lab スキル

Amazon商品画像の品質を、人間の主観ではなくブラインド評価ループで客観的に最大化するためのスキル。

**このスキルが担うもの**: 画像1枚を作ることではなく、「何が売れる画像を生み出すか」を学習するワークフロー。実験→評価→知見蓄積のループを回すことで、再現可能な勝ちパターンを発見する。

---

## 重要な前提: 役割の分担

| 要素 | 担当 | 役割 |
|------|------|------|
| **訴求内容・構成** | `appeal-map.md` | 何を伝えるか（固定。変更はユーザー承認後のみ） |
| **競合調査・差別化軸** | `competitor-analysis.md` | どう差別化するか |
| **ベンチマーク画像** | `benchmark/` | **デザイン品質の参考のみ**。訴求内容・コピーは参照しない |
| **実験で変えてよいもの** | `experiments/` | デザイン手法・レイアウト・フォント・写真・表現方法 |

> **ベンチマーク画像はデザインインスピレーション源であり、訴求内容のコピー元ではない。**
> `appeal-map.md` の内容（USP・コピー・写真仕様）が実験コンテンツの正本。

---

## 起動モード

| コマンド例 | 動作 |
|-----------|------|
| `listing-lab init mothers-backpack` | 商品ラボを初期化 |
| `listing-lab exp-001` | 評価のみ実行（画像生成済み前提） |
| `listing-lab exp-001 render` | HTMLレンダリング → 評価 |
| `listing-lab exp-001 generate` | Gemini生成 → 評価 |
| `listing-lab exp-001 fullset` | フルセット評価モード（sub_02〜sub_08全スロット）※デフォルト |
| `listing-lab exp-001 vs exp-002` | 2実験を直接対戦（ベンチマーク不使用） |
| `listing-lab next mothers-backpack sub_02` | 次実験の仮説・設計を生成 |
| `listing-lab synthesize mothers-backpack` | 全実験から設計ルールを合成 |
| `listing-lab refine-criteria` | 評価基準を改善（外側ループ） |
| `listing-lab promote exp-003` | 勝利実験を本番出力にコピー |
| `listing-lab status` | 現在の実験状況を表示 |

---

## Mode: init

新しい商品のラボを初期化する。

```
listings/lab/{product-slug}/
  benchmark/           ← デザイン参考画像（訴求内容はここから取らない）
  experiments/         ← 実験フォルダ（exp-001等）
  lab-journal.md       ← 実験履歴・知見の蓄積
```

1. ディレクトリ構造を作成
2. `lab-journal.md` を初期化（予算欄・USP欄は空欄で作成）
3. ユーザーに以下を確認:
   - `listings/{product-slug}/appeal-map.md` のパス（訴求内容の正本）
   - `listings/{product-slug}/competitor-analysis.md` のパス（差別化軸）
   - 対象スロット（例: sub_02, aplus_01 など）
   - ベンチマーク画像のファイル名（デザイン参考として配置）
   - 予算（実験数または金額）
   - 評価モード: `single`（1スロットずつ） or `fullset`（複数スロットを購買導線として評価）
   - **`product_context` 文（必須）**: 評価プロンプトに注入する顧客設定。以下フォーマットで `lab-journal.md` に記入:
     ```
     **product_context**: あなたは{顧客像}です。{状況・行動}。¥{価格帯}の商品を検討しています。
     ```

---

## Mode: run（メインループ）

### Step 0: 訴求内容の確認（必須）

実験開始前に必ず `appeal-map.md` を読み、対象スロットの訴求仕様を把握する:

- そのスロットで伝えるべき訴求（1〜2つ）
- 使用すべきコピー・見出し
- 写真仕様（撮影シーン・構図・主役・背景）
- 禁止事項（appeal-map.md 内の「禁止」項目）

**この仕様が実験コンテンツの設計基準。** ベンチマークのコピーや写真は絶対に流用しない。

### Step 1: 実験設定の確認

`experiments/{exp-id}_{method-name}/config.md` を読む。存在しない場合はテンプレートから作成してユーザーに確認を求める。

config.md から必ず取得:
- 対象スロット（例: sub_02）
- 手法（html-puppeteer / gemini-direct / gemini-hybrid）
- ソースファイルのパス
- `appeal-map.md` のどの要素をどう表現するか（仮説）

### Step 2: ソースファイルの確認

config.md の仮説に基づき、ソースファイル（src/design.html または src/prompt.json）が存在することを確認する。存在しない場合はユーザーに作成を依頼する。

### Step 3: 画像生成（renderまたはgenerateフラグ時のみ）

**html-puppeteer の場合:**
```bash
NODE_PATH=./node_modules uv run python listings/scripts/render_html.py \
  {src/design.html のパス} \
  experiments/{exp-id}_{method}/output/{slot}.png \
  --width 1600 --height 2000
```
A+コンテンツの場合: `--width 970 --height 600`

**gemini-direct の場合（有料APIを使用）:**
```bash
uv run python listings/scripts/generate_photo.py \
  --prompt experiments/{exp-id}/src/prompt.json \
  --output experiments/{exp-id}/output/{slot}.png
```

> Gemini無料枠は枯渇している場合がある。枯渇時は有料API（GEMINI_API_KEY環境変数）を使用する。

### Step 4: 比較対象の確認

**比較対象は常に `exp-001_production-baseline/output/{slot}.png`（現行本番デザイン）。**

`experiments/exp-001_production-baseline/output/` に sub_02〜sub_08 の7枚が存在することを確認する。
存在しない場合は exp-001 を再生成してから続ける（この実験は評価対象外・ベースラインのみ）。

`benchmark/` は**デザインのインスピレーション参照のみ**。評価比較には使用しない。

### Step 5: 評価モードの選択

**フルセット評価（fullset / デフォルト）:**
- sub_02〜sub_08（7枚）のセット同士を比較
- 購買導線全体（どの順序で何を伝えるか）の有効性を評価
- **比較対象: exp-001_production-baseline の7枚セット vs 今回実験の7枚セット**

**単一スロット評価（single）:**
- 1スロットのみを比較（高速プロトタイピング用）
- 用途: デザイン要素のクイックチェック。本番昇格判断には使わない

### Step 6: 評価プロンプトの準備（再現性の核心）

1. スキルディレクトリ内の `prompts/evaluate-v3.md` を読む（verbatim、一字一句変更しない）
2. `lab-journal.md` の `**product_context**:` 行を読み、`{product_context}` プレースホルダーを置換する
3. `{evaluation_mode}` を `single` または `fullset` で置換する
4. テンプレートファイルの SHA256 ハッシュを計算（置換前のファイルに対して）:
   ```bash
   C:/Users/ninni/scoop/apps/python/current/python.exe -c "
   import hashlib, sys
   sys.stdout.reconfigure(encoding='utf-8')
   data = open('C:/Users/ninni/.claude/skills/listing-lab/prompts/evaluate-v3.md','rb').read()
   print(hashlib.sha256(data).hexdigest())
   "
   ```
5. ランダム化の設計を決定（3 subagent の A/B 順序）:
   ```
   Evaluator-1: A=実験画像, B=exp-001
   Evaluator-2: A=exp-001, B=実験画像  ← 入替え（順序バイアス排除）
   Evaluator-3: A=実験画像, B=exp-001
   ```

### Step 7: subagent ×3 並列評価

3つの subagent を**同時に**起動する（並列実行が重要）。

各 subagent に渡す内容:
```
タスク: 2つの商品画像（またはセット）を評価してJSONを返す

評価プロンプト:
{evaluate-v3.md の全文をそのまま貼り付け（product_context・evaluation_mode置換後）}

【fullsetの場合】
画像A（実験）: sub_02〜sub_08の7枚を順に列挙（絶対パス）
画像B（exp-001）: experiments/exp-001_production-baseline/output/ の7枚を順に列挙

【singleの場合】
画像A: {対象スロットの実験画像（絶対パス）}
画像B: experiments/exp-001_production-baseline/output/{slot}.png

出力: JSONのみ。他のテキストは不要。
```

Evaluator-2 のみ A/B を入れ替える。

**集計ルール（最大30点）:**
- Evaluator-2 の結果は逆転して記録（"B"勝ち → 実験画像勝ちに変換）
- 3票中2票以上が「実験画像の勝ち」→ 実験勝ち
- 3票中2票以上が「exp-001の勝ち」→ 実験負け
- 3票全て分かれた場合 → confidence: low として記録し追加評価1回

### Step 8: 結果記録

**eval.md を作成:**

```markdown
# 評価結果: {exp-id}

**日時**: {YYYY-MM-DD HH:MM}
**スロット**: {slot または fullset: sub_02〜sub_08}
**評価モード**: single / fullset
**比較対象**: exp-001_production-baseline
**評価プロンプト**: evaluate-v3.md
**プロンプトSHA256**: {hash}
**使用モデル**: claude-sonnet-4-6（または実際のモデルID）
**A/B順序**:
  - Evaluator-1: A=実験, B=exp-001
  - Evaluator-2: A=exp-001, B=実験（入替え）
  - Evaluator-3: A=実験, B=exp-001

## 判定

| Evaluator | 勝者（補正後） | 実験スコア | ベンチスコア | confidence |
|-----------|--------------|-----------|-------------|------------|
| Evaluator-1 | | | | |
| Evaluator-2（入替補正） | | | | |
| Evaluator-3 | | | | |
| **集計** | | **avg** | **avg** | |

**最終判定: {実験 or ベンチマーク}の{勝利 or 敗北}（N/3票）**

## フィードバックサマリー

**実験画像の強み:**
- ...

**実験画像の改善点:**
- ...

**visual_quality 評価:**
- ...

## 次の仮説
- ...

---

## 生データ

<details><summary>Evaluator-1 Raw JSON</summary>
```json
{...}
```
</details>

<details><summary>Evaluator-2 Raw JSON（入替え前の生データ）</summary>
```json
{...}
```
</details>

<details><summary>Evaluator-3 Raw JSON</summary>
```json
{...}
```
</details>
```

**lab-journal.md を更新:**
- 予算トラッカーの「消費済み」を更新
- 実験ログに結果エントリを追記:

```markdown
### {exp-id}: {method-name} - {日付}
- **スロット**: {slot}
- **評価モード**: single / fullset
- **結果**: 勝ち / 負け（実験 {score}/30 vs exp-001 {score}/30、{N}-{M}票）
- **仮説**: {config.mdから転記}
- **知見**: {今回の評価から得られた新たな知見}
- **次の仮説**: {次に試すべきこと}
```

### Step 9: 判断を提示

ユーザーに以下を提示:
1. 勝敗の結果と信頼度
2. 3票のスコア比較表（6軸）
3. `visual_quality` の評価根拠（脱スライド観点）
4. 最も重要な改善点（ネガの理由）
5. 次の実験の推奨仮説（appeal-map.md の何を、どのデザイン手法で強化するか）
6. 予算残と推奨アクション（続ける/昇格する/再評価）

---

## Mode: next（次実験の設計生成）

1. `lab-journal.md` の全実験ログを読む
2. 対象スロットの全 `eval.md` を読む
3. `appeal-map.md` の対象スロット仕様を読む（まだ反映できていない要素を特定）
4. 以下の分析を行う:
   - 最も低かった評価軸（impression/clarity/desire/trust/mobile/visual_quality）
   - 同じ弱点が複数実験で繰り返されているか
   - `appeal-map.md` の訴求要素で未実装のものはあるか
   - `design-system.md` の脱スライド原則で未適用のものはあるか
5. 次実験の `config.md` ドラフトを作成してユーザーに確認を求めてから実験フォルダを作成

---

## Mode: synthesize（設計ルール合成）

一定数（3実験以上）蓄積された後に実行する。

1. 全実験の eval.md を読む
2. 勝ちパターン・負けパターンを横断分析
3. `listings/lab/{product}/design-rules.md` を出力:

```markdown
# 設計ルール - {product} （{N}実験から合成、{日付}）

## 有効なパターン（複数実験で勝ち）
- ...

## 無効なパターン（複数実験で負け）
- ...

## 未検証（試す価値あり）
- ...

## 評価軸ごとの傾向
| 軸 | 平均スコア（実験） | 最有効な改善手法 |
|---|---|---|
| impression | | |
| visual_quality | | |
```

4. `design-system.md` への昇格は**ユーザーが判断する**。Claudeは材料を提示するだけ:

**Claudeが提示するもの:**
- 勝ちパターンの該当実験一覧（exp-id・スロット・スコア差）
- 「何が変わったか」の具体的な説明（フォントサイズ・レイアウト等）
- 評価エージェントの限界の注記: 「エージェント評価は実際の購買効果ではない。過去にも楽観バイアスが確認されている。」
- 昇格した場合の `design-system.md` 追記案（ドラフト）

**Claudeが判断しないこと:**
- 「このパターンは昇格すべき」とは言わない
- 勝ち回数で自動昇格しない（回数基準は廃止）

**ユーザーが判断する基準（例）:**
- 自分の目で画像を見て、実際に差があると感じるか
- 評価軸のスコア差が大きいか（特に trust / desire）
- ベンチマーク（競合画像）の質を考慮してもなお説得力があるか

> **重要**: `listings/brand/design-system.md` はlab検証済みの知見のみを収録する。ただし「lab勝利」はエージェント評価に過ぎず、実際の売上への影響は別途確認が必要。未検証の仮説は `design-hypotheses.md` に留める。

---

## Mode: refine-criteria（外側ループ：評価基準の更新）

**トリガー**: ユーザーが「AIの評価と自分の評価が違う」「AIが勝利と言ったが実際はそうでなかった」と感じたとき

このモードは2つのループの「外側ループ」。内側ループ（実験→評価）を回した後、評価基準自体を改善する。

```
内側ループ: 実験 → AI評価 → 結果記録（自動）
外側ループ: ユーザー指摘 → 基準の問題特定 → 新バージョン作成（ユーザー確認後）
```

### Step 1: 問題の特定

ユーザーに以下を確認する:
- どの実験の、どの評価が「おかしい」と感じたか（exp-id・評価者番号）
- 「AIはAが勝ちと言ったが、自分が見るとBの方が良い」等、具体的な乖離内容
- 問題だと思う評価軸（impression? trust? visual_quality?）

対象の `eval.md` と生JSONを読み、AIがなぜその判定を出したかを分析する。

### Step 2: 現行基準の問題を言語化

`CRITERIA-CHANGELOG.md` の最新バージョンの「残課題」欄を読む。

問題を以下のカテゴリで分類:
- **アンカーが甘い**: 「5点=良い」の定義が曖昧で高得点になりやすい
- **ネガ判断の欠如**: 「悪い場合に減点する基準」がない
- **相対評価の罠**: どちらかを必ず「勝者」にしようとして、両方不合格の判定ができない
- **軸の定義が不明確**: 評価者によって解釈がばらつく

### Step 3: 新バージョンのドラフト作成

現行の最新プロンプト（evaluate-v{N}.md）をベースに、問題箇所を修正したドラフトを作成する。

修正の方向性:
- アンカーを厳格化: 「3点は合格点に届かない水準」「4点は合格」「5点はごく稀」
- 減点基準を追加: 「これがあればその軸は最大3点」などの上限設定
- 絶対基準を追加: 「どちらが良くても、両方とも合格点（12/20以上）に満たない場合は両方不合格と記録」
- confidence判定を厳格化: 「スコア差が2点以内ならconfidence: low必須」

### Step 4: ユーザー確認 → 新バージョン確定

ドラフトをユーザーに見せ、承認後に `evaluate-v{N+1}.md` として保存。

`CRITERIA-CHANGELOG.md` に以下を追記:
```markdown
## v{N} → v{N+1}: {変更のサマリー}
**作成日**: {日付}
**きっかけ**: {ユーザーが指摘した乖離事例}
**変更内容**: {具体的な変更点}
**残課題**: {まだ解決されていない問題}
```

### Step 5: 再評価（オプション）

新基準で過去の実験画像を再評価すると、基準変更の効果を確認できる。
ただし異なるバージョンの結果は直接比較不可。lab-journal.mdに「v{N}基準での結果とv{N+1}基準での結果は別扱い」と記録する。

---

## Mode: promote

勝利した実験の成果物を本番ディレクトリにコピーする。

```bash
cp listings/lab/{product}/experiments/{exp-id}_{method}/output/{slot}.png \
   listings/{product-dir}/output/{slot}.png
```

ユーザーに確認を取ってから実行。`lab-journal.md` に昇格記録を追記。

---

## 再現性の保証

| 記録項目 | 保存場所 | 目的 |
|---------|---------|------|
| 評価プロンプトのバージョン | eval.md | どの基準で評価したか |
| プロンプトSHA256 | eval.md | ファイルが変更されていないことを検証 |
| 使用モデルID | eval.md | モデル更新による結果変化を追跡 |
| A/B順序（evaluatorごと） | eval.md | 順序バイアスの確認 |
| 評価モード（single/fullset） | eval.md | 評価単位の記録 |
| 生JSON（3票全て） | eval.md | 集計ロジックのデバッグ・再集計が可能 |
| ソースファイル | src/ | 実験を再実行できる |

**評価プロンプトの更新ポリシー:**
- 変更は `prompts/evaluate-v4.md` として新規作成
- `evaluate-v1.md` `evaluate-v2.md` `evaluate-v3.md` は変更禁止
- プロンプトバージョンが異なる実験間の比較は無効

---

## ディレクトリ参照

| パス | 内容 |
|-----|------|
| `~/.claude/skills/listing-lab/prompts/evaluate-v3.md` | 評価プロンプト（変更禁止） |
| `~/.claude/skills/listing-lab/templates/config.md` | 実験設定テンプレート |
| `listings/{product}/appeal-map.md` | **訴求内容の正本**（実験コンテンツの設計基準） |
| `listings/{product}/competitor-analysis.md` | 競合分析・差別化軸 |
| `listings/lab/{product}/benchmark/` | デザイン品質参考画像 |
| `listings/lab/{product}/experiments/{exp-id}_{method}/` | 実験フォルダ |
| `listings/lab/{product}/lab-journal.md` | 実験履歴・知見 |
| `listings/brand/design-system.md` | デザインルール（lab検証済みの知見のみ収録） |
| `listings/lab/{product}/design-hypotheses.md` | 未検証のデザイン仮説候補 |
| `listings/scripts/render_html.py` | HTMLレンダリング |
| `listings/scripts/generate_photo.py` | Gemini API 写真生成（有料API対応） |
