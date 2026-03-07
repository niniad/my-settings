---
name: new-project
description: >
  新プロジェクトの初期セットアップ。CLAUDE.md・decisions.md・.gitignore・
  標準ディレクトリ（tmp/, archive/）・.claude/ を種類別テンプレートで生成する。
  トリガー: 「新プロジェクト」「プロジェクト作成」「初期設定」「new-project」
argument-hint: "[プロジェクト名]"
model: sonnet
---

# new-project スキル

新しいプロジェクトの初期ファイル構造を対話的にセットアップする。

## Step 1: 情報収集

以下をまとめて 1 メッセージで確認する:

1. **プロジェクト名**: 引数 `$ARGUMENTS` で指定済みの場合は確認不要
2. **種類**（番号で選択）:
   - `1` — EC（販売オペレーション・スキル活用）
   - `2` — accounting（会計・財務インフラ）
   - `3` — life（ライフ・個人管理）
   - `4` — tool（ツール・スクリプト・Python パイプライン）
   - `5` — general（汎用）
3. **概要**: 1〜2 文。CLAUDE.md 冒頭に使う

## Step 2: 作成内容の確認

以下を提示してユーザーの承認を得る:

```
作成場所: C:/Users/ninni/projects/[名前]/

ファイル一覧:
  CLAUDE.md           ← [種類]向けテンプレート
  decisions.md        ← 意思決定ログ
  .gitignore
  tmp/                ← 一時ファイル（.gitignore 対象）
  archive/            ← アーカイブ
  .claude/            ← Claude 設定ディレクトリ

作成しますか？
```

## Step 3: ファイル作成

承認後、以下を順に作成する:

1. ディレクトリ: `tmp/`, `archive/`, `.claude/`
2. `.gitignore`（下記テンプレート）
3. `decisions.md`（下記テンプレート）
4. `CLAUDE.md`（種類別テンプレート）

---

## テンプレート集

### .gitignore（全種類共通）

```
tmp/
*.log
.env
.env*
__pycache__/
*.pyc
.DS_Store
```

### decisions.md（全種類共通）

```markdown
# 意思決定ログ

重要な方針変更・設計判断を日時と理由とともに記録する。

| 日付 | 決定内容 | 理由 |
|------|---------|------|
| [今日の日付] | 初期設定 | プロジェクト開始 |
```

---

### CLAUDE.md — EC・販売オペレーション

```markdown
# [プロジェクト名]

## コンパクション後の復帰手順

コンパクション直後は必ず: (1) この CLAUDE.md を再読 (2) 現在のタスクを確認してから再開

## 目的

[概要]

## 事業概要

- **ブランド**:
- **販路**: Amazon.co.jp FBA
- **運営**: 個人事業主

## スキル構成

業務に応じてスキルを選択する（.claude/rules/ 参照）。

## 共通リソース

### BigQuery
- プロジェクト: `main-project-477501`
- データセット: `analytics`（us-central1）
- MCP: `mcp__bigquery__execute_sql` 等

### NocoDB
- nocodb スキル（`~/.claude/skills/nocodb/SKILL.md`）経由

## 外部リソース

| リソース | パス |
|---------|------|
| 会計方針 | `C:/Users/ninni/projects/accounting/accounting_policies.md` |
```

---

### CLAUDE.md — 会計・財務インフラ

```markdown
# [プロジェクト名]

## コンパクション後の復帰手順

コンパクション直後は必ず: (1) この CLAUDE.md を再読 (2) 現在のタスクを確認してから再開

## プロジェクト概要

[概要]

## 重要ファイル

| ファイル | 内容 |
|---------|------|
| `decisions.md` | 設計判断ログ |

## 外部リソース

| リソース | パス / ID |
|---------|-----------|
| NocoDB SQLite | `C:/Users/ninni/nocodb/noco.db` |
| BQ Project | `main-project-477501` |
| nocodb-to-bq 同期 | `cd C:/Users/ninni/projects/nocodb-to-bq && uv run python main.py` |

## Python 実行環境

- `uv run python` を使用
- freee 依存: `--with requests --with google-cloud-secret-manager --with google-auth`
- BQ 依存: `--with google-cloud-bigquery`
- 日本語出力: `sys.stdout.reconfigure(encoding='utf-8')` 必須
```

---

### CLAUDE.md — ライフ・個人管理

```markdown
# [プロジェクト名]

## コンパクション後の復帰手順

コンパクション直後は必ず: (1) この CLAUDE.md を再読 (2) 現在のタスクを確認してから再開

## 目的

[概要]

## 構成

| ディレクトリ/ファイル | 内容 |
|---------------------|------|
| `docs/` | ドキュメント |
| `tmp/` | 一時ファイル |
| `decisions.md` | 意思決定ログ |

## 関連スキル

- `life-session` — ライフセッション（相談・ヒアリング）

## 注意

EC 事業のアクション管理は ec プロジェクトで管理。
```

---

### CLAUDE.md — ツール・スクリプト・パイプライン

```markdown
# [プロジェクト名]

## コンパクション後の復帰手順

コンパクション直後は必ず: (1) この CLAUDE.md を再読 (2) 現在のタスクを確認してから再開

## 目的

[概要]

## 実行方法

\`\`\`bash
cd C:/Users/ninni/projects/[名前]
uv run python main.py
\`\`\`

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `main.py` | エントリポイント |
| `pyproject.toml` | Python 依存関係 |
| `tmp/` | 一時出力（.gitignore 対象）|

## 注意

- 日本語出力: `sys.stdout.reconfigure(encoding='utf-8')` 必須
- uv run 内から gcloud が見つからない → トークンを環境変数で渡す
```

---

### CLAUDE.md — 汎用

```markdown
# [プロジェクト名]

## コンパクション後の復帰手順

コンパクション直後は必ず: (1) この CLAUDE.md を再読 (2) 現在のタスクを確認してから再開

## 目的

[概要]

## 構成

| ディレクトリ/ファイル | 内容 |
|---------------------|------|
| `tmp/` | 一時ファイル（.gitignore 対象）|
| `archive/` | 不要ファイルのアーカイブ |
| `decisions.md` | 重要な意思決定ログ |
```

---

## 完了後の案内

作成完了後、ユーザーに以下を伝える:

1. 作成したファイル一覧と場所
2. CLAUDE.md のカスタマイズが必要な箇所（[概要] 等）
3. スキルを追加する場合は `skill-creator` スキルを呼び出すよう案内
4. プロジェクト専用スキルを追加する場合は `.claude/skills/<name>/SKILL.md` を作成するよう案内
