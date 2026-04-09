---
name: todoist
description: >
  Todoistタスク管理スキル。REST API v1経由でタスクの一覧取得・作成・更新・完了・削除を実行する。
  MAP/TODOIST分離原則に従い、物理的な次のアクションのみをTodoistで管理する。
  トリガー：「Todoistタスク」「タスク確認」「タスク作成」「タスク完了」「@ec @awi @life」
  「今日のタスク」「期限切れ」「タスク一覧」
---

# Todoist タスク管理スキル

Todoist REST API v1 を使ってタスクを操作する。MCP不要。

## 使い方

スクリプト: `~/.claude/skills/todoist/scripts/todoist_api.py`

```bash
# タスク一覧（全件）
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list

# フィルター付き一覧
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --filter "today | overdue"
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --label ec

# タスク作成
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py create "SBI証券でGLDM50株を売却する" --label ec --due "2026-12-31" --desc "金比率調整"

# タスク更新
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py update TASK_ID --content "新しいタイトル" --desc "新しい説明"

# タスク完了
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py complete TASK_ID

# タスク削除
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py delete TASK_ID
```

## 認証

環境変数 `TODOIST_API_TOKEN` を優先。未設定時は GCP Secret Manager `todoist-api-token` から自動取得。

## MAP/TODOIST分離原則

タスク作成前に `projects/.claude/rules/task-management.md` の卒業ルールを確認:

1. 物理的な次のアクションが明確か
2. 現在の時間軸で実行可能か
3. 完了条件があるか

3条件を満たさないものはTodoistに入れず、Maps（`projects/maps/`）で管理する。

## セッション開始時のタスク確認

```bash
# ドメイン別に確認（起動ディレクトリに応じて）
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --label ec
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --label awi
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --label life

# 期限切れ・今日期限
uv run python ~/.claude/skills/todoist/scripts/todoist_api.py list --filter "today | overdue"
```
