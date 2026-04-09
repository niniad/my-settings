# テンプレート集

map.md、INDEX.md、リサーチレポートのテンプレート。ファイル生成時にこのテンプレートに従って出力する。

---

## INDEX.md テンプレート

```markdown
# Hypothesis Action — プロジェクト一覧

| プロジェクト | 目的 | 状態 | 仮説数 | 検証済 | 作成日 | 最終更新 |
|-------------|------|------|--------|--------|--------|---------|
| [{project-name}]({project-slug}/map.md) | {purpose} | {status} | {total} | {verified} | {created} | {updated} |
```

**記入ルール**:
- status: `mapping` / `looping` / `leaping` / `concluded`
- concluded なプロジェクトは下部に移動し、decision を付記（go / pivot / kill / wait）
- プロジェクト名はリンクとして map.md を参照する

---

## map.md テンプレート

```markdown
---
project: {project-name}
purpose: {purpose-description}
status: mapping
phase_detail: 初期マップ作成中
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
concluded:
decision:
timeline: {deadline-or-target}
next_milestone: {next-action-or-checkpoint}
hypothesis_count: {total-number}
parent: {親マップの仮説ID（例: life-strategy H06）。最上位マップなら空}
---

# 仮説マップ: {project-name}

> **目的**: {purpose-description}
> **タイムライン**: {timeline}
> **上位仮説**: {parent の内容を記載。最上位なら省略}

## 最上位仮説

**{このマップ全体の頂点となる1つの仮説。言い切り形・反証可能・具体的であること}**

## ピラミッド構造

### 課題仮説（何が問題/ニーズか）
- **P01**: {top-level-problem-hypothesis}
  - **H02**: {sub-hypothesis}
    - **H05**: {detail-hypothesis}
  - **H03**: {sub-hypothesis}
  - **H04**: {sub-hypothesis}

> ピラミッドはざっくりの俯瞰図。厳密な依存関係は仮説台帳の「前提」「支持先」で管理する。
> 1つの仮説が複数の親を持つ場合や相互依存はピラミッドでは表現しきれないため、台帳が正。

## 評価マトリックス（影響度 x 確信度）

|            | 確信度: 低         | 確信度: 中       | 確信度: 高       |
|------------|-------------------|-----------------|-----------------|
| 影響度: 高  | ★最優先検証        | 検証継続         | 中核仮説         |
|            | {hypothesis-ids}  | {hypothesis-ids} | {hypothesis-ids} |
| 影響度: 中  | 次の候補           | 経過観察         | 安定仮説         |
|            | {hypothesis-ids}  | {hypothesis-ids} | {hypothesis-ids} |
| 影響度: 低  | 後回し             | 現状維持         | 前提条件         |
|            | {hypothesis-ids}  | {hypothesis-ids} | {hypothesis-ids} |

> ★高影響・低確信 = リスク仮説。最優先で検証する。

## 仮説台帳

| ID | 仮説 | タイプ | 前提 | 支持先 | 影響度 | 確信度 | 強度 | 状態 | 最終検証日 |
|----|------|--------|------|--------|--------|--------|------|------|-----------|
| H01 | {仮説の内容} | {タイプ} | — | — | 高/中/低 | 高/中/低 | 作業仮説/仮説/強い仮説/クレーム | 未検証/検証中/検証済/棄却 | {YYYY-MM-DD} |
| H02 | {仮説の内容} | {タイプ} | H01 | H01 | 高/中/低 | 高/中/低 | {強度} | {状態} | {YYYY-MM-DD} |

**列の意味**:
- **タイプ**: マップの性質に応じて使い分ける
  - 事業・プロジェクト系: `課題` / `解決策`
  - 人生戦略・自己理解系: `発見` / `行動` / `実行`
- **前提**: この仮説が成立するために必要な他の仮説（例: H02棄却, P01）
  - 解決策仮説の前提に課題仮説を記載することで、課題→解決策の紐づけを管理する
- **支持先**: この仮説が支えている上位仮説（例: H01, H06）
- **強度**: 作業仮説 → 仮説 → 強い仮説 → クレーム（検証の進展に応じて昇降格）

子マップへの展開がある場合、仮説の末尾に `→ {子マップ名}` と記載する。

> **重要**: 課題仮説が棄却された場合、前提にその課題を持つ解決策仮説をすべて見直す。課題が検証されていない段階で解決策に飛びつかない。

## アクション

| ID | アクション | 対象仮説 | 期限 | 状態 |
|----|----------|---------|------|------|
| A01 | [動詞] [対象] [完了条件] | H{XX} | {YYYY-MM-DD または なし} | 未着手/実行中/✅完了/中止 |
| A02 | {アクション内容} | H{XX} | {期限} | {状態} |

**アクションの3条件**（この3つを満たすものだけ記載する）:
1. 物理的な次のアクションが明確
2. 現在の時間軸で実行可能
3. 完了条件がある

> 仮説そのもの（「ブランド戦略確立」）や検証判定（「CVR改善しなければKill」）はアクションではない。

## 検証ログ

### {YYYY-MM-DD}: {verification-title}

- **対象仮説**: H{XX}
- **検証方法**: {method}（デスクリサーチ/インタビュー/サーベイ/観察/実験/MVP）
- **勝利条件**: {事前に設定した基準}
- **撤退条件**: {事前に設定した基準}
- **エビデンス**: {evidence-summary}
  - 根拠: {追跡可能な1次情報をソース付きで記載}
- **結果**: {支持/一部支持/反証/判断保留}
- **Fact**: {観察された事実}
- **Insight**: {So What? / Why So?}
- **Action**: {次の行動}
- **確信度変化**: {before} → {after}
- **カスケード影響**: {affected-hypotheses}（影響がある場合のみ）

---

### {YYYY-MM-DD}: {verification-title}

（同じフォーマットで追記）

## 決断ログ

### {YYYY-MM-DD}: {decision-type}（リープ①/リープ②）

- **決断内容**: {decision-description}
- **根拠となる仮説**: {hypothesis-ids-and-summary}
- **決断条件の評価**:
  - 十分性: {assessment}
  - 経済性: {assessment}
  - 機会性: {assessment}
  - リスク許容度: {assessment}
- **残存リスク**: {remaining-risks}
- **次のアクション**: {next-actions}
```

---

---

## リサーチレポートテンプレート

ファイルパス: `research/H{ID}_{YYYYMMDD}.md`

```markdown
# リサーチレポート: H{ID} — {hypothesis-summary}

- **対象仮説**: H{ID}: {full-hypothesis-text}
- **調査日**: {YYYY-MM-DD}
- **調査方法**: {methods-used}

## エグゼクティブサマリー

{3-5行の要約。結論を先に述べる}

## 反対エビデンス（この仮説が誤りである可能性を示す情報）

### E1: {evidence-title}
- **内容**: {evidence-detail}
- **根拠**: {追跡可能な1次情報をソース付きで記載}
- **ソース等級**: {A-E}
- **確信度への影響**: {impact}

## 支持エビデンス（この仮説を支持する情報）

### E2: {evidence-title}
- **内容**: {evidence-detail}
- **根拠**: {追跡可能な1次情報をソース付きで記載}
- **ソース等級**: {A-E}
- **確信度への寄与**: {contribution}

## 分析

### Fact（観察された事実）
{事実の列挙}

### Insight（So What? / Why So?）
{上位仮説への影響、根本原因の推論}

### Action（次の行動）
- {recommended-next-action-1}
- {recommended-next-action-2}

## 推奨アクション

- **確信度更新**: {before} → {after}
- **次の検証**: {recommended-next-verification}
- **カスケード影響**: {hypotheses-to-review}

## エビデンス一覧

| # | タイトル | ソース等級 | 方向 | 根拠 |
|---|---------|-----------|------|------|
| E1 | {title} | {grade} | 支持/反対 | {1次情報ソース} |
| E2 | {title} | {grade} | 支持/反対 | {1次情報ソース} |
```
