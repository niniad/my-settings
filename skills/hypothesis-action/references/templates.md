# テンプレート集

map.md、INDEX.md、リサーチレポートのテンプレート。ファイル生成時にこのテンプレートに従って出力する。

---

## INDEX.md テンプレート

```markdown
# Hypothesis Action — プロジェクト一覧

| プロジェクト | 目的 | 状態 | 仮説数 | 検証済 | 作成日 | 最終更新 |
|-------------|------|------|--------|--------|--------|---------|
| [{project-name}]({project-slug}_{YYYYMMDD}/map.md) | {purpose} | {status} | {total} | {verified} | {created} | {updated} |
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
---

# 仮説マップ: {project-name}

> **目的**: {purpose-description}
> **タイムライン**: {timeline}

## ピラミッド構造

### 最上位仮説
- **H01**: {top-level-hypothesis}
  - **H02**: {sub-hypothesis}
    - **H05**: {detail-hypothesis}
    - **H06**: {detail-hypothesis}
  - **H03**: {sub-hypothesis}
    - **H07**: {detail-hypothesis}
  - **H04**: {sub-hypothesis}

> ピラミッドの上位ほど影響度が大きく、下位ほど検証しやすい。
> 下位の検証結果を積み上げて上位の確信度を高める。

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

| ID | 仮説 | カテゴリ | 影響度 | 確信度 | 強度 | 状態 | 最終検証日 |
|----|------|---------|--------|--------|------|------|-----------|
| H01 | {hypothesis-text} | {category} | 高/中/低 | 高/中/低 | 作業仮説/仮説/強い仮説/クレーム | 未検証/検証中/検証済/棄却 | {YYYY-MM-DD} |
| H02 | {hypothesis-text} | {category} | 高/中/低 | 高/中/低 | {strength} | {state} | {YYYY-MM-DD} |

**カテゴリ凡例**: 価値 / 市場 / 製品 / 戦略 / BM / 財務 / 組織 / 採用
**強度**: 作業仮説 → 仮説 → 強い仮説 → クレーム（検証の進展に応じて昇降格）

## 検証ログ

### {YYYY-MM-DD}: {verification-title}

- **対象仮説**: H{XX}
- **検証方法**: {method}（デスクリサーチ/インタビュー/サーベイ/観察/実験/MVP）
- **エビデンス**: {evidence-summary}
  - ソース等級: {A-E} / 確信度: {1-5}
- **結果**: {支持/一部支持/反証/判断保留}
- **So What?**: {implication-for-upper-hypothesis}
- **Why So?**: {root-cause-analysis}
- **確信度変化**: {before} → {after}
- **強度変化**: {before} → {after}（変化がある場合のみ）
- **カスケード影響**: {affected-hypotheses}（影響がある場合のみ）

---

### {YYYY-MM-DD}: {verification-title}

（同じフォーマットで追記）

## 決断ログ

### {YYYY-MM-DD}: {decision-type}（小リープ/大リープ）

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

## リサーチレポートテンプレート

ファイルパス: `research/H{ID}_{YYYYMMDD}.md`

```markdown
# リサーチレポート: H{ID} — {hypothesis-summary}

- **対象仮説**: H{ID}: {full-hypothesis-text}
- **調査日**: {YYYY-MM-DD}
- **調査方法**: {methods-used}

## エグゼクティブサマリー

{3-5行の要約。結論を先に述べる}

## 支持するエビデンス

### E1: {evidence-title}
- **内容**: {evidence-detail}
- **ソース**: {source-name-and-url}
- **ソース等級**: {A-E}
- **確信度への寄与**: {contribution}

### E2: {evidence-title}
（同じフォーマットで追記）

## 反対するエビデンス

### E3: {evidence-title}
- **内容**: {evidence-detail}
- **ソース**: {source-name-and-url}
- **ソース等級**: {A-E}
- **確信度への影響**: {impact}

### E4: {evidence-title}
（同じフォーマットで追記）

## 分析

### So What?（この調査結果は何を意味するか）
{上位仮説やマップ全体への影響を記述}

### Why So?（なぜこのような結果になったか）
{根本原因の推論を記述}

### 新たに浮上した論点
- {new-question-or-hypothesis-1}
- {new-question-or-hypothesis-2}

## 推奨アクション

- **確信度更新**: {before} → {after}
- **強度更新**: {before} → {after}（変化がある場合）
- **次の検証**: {recommended-next-verification}
- **カスケード影響**: {hypotheses-to-review}

## エビデンス一覧

| # | タイトル | ソース等級 | 方向 | ソース |
|---|---------|-----------|------|--------|
| E1 | {title} | {grade} | 支持/反対 | {source} |
| E2 | {title} | {grade} | 支持/反対 | {source} |
```
