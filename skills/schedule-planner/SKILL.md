---
name: schedule-planner
description: YAMLベースの業務スケジュールを解析し、依存関係・制約条件を考慮したスケジュールを生成するスキル。Mermaid Gantt・人別負荷分析・問題点レポートを出力する。OR-Toolsによる最適化も対応。スキルディレクトリはC:/Users/ninni/.claude/skills/schedule-planner/。このスキルは「スケジュール作成」「schedule-planner」「Gantt」「ガントチャート」「タスク割り当て」「工程表」「スケジュール最適化」「週次スケジュール」「業務スケジュール」「担当者割り当て」など、チームやプロジェクトのスケジューリングに関する依頼が来たら積極的に使用すること。
---

# schedule-planner

YAMLベースの業務スケジュールを解析し、依存関係・制約条件を考慮したスケジュールを生成するスキル。

## スキルディレクトリ

`C:/Users/ninni/.claude/skills/schedule-planner/`（以下 `SKILL_DIR`）

## 主な機能

- YAML検証（validate.py）
- 依存関係解析・Mermaid Gantt生成（render_mermaid.py）
- 依存関係グラフ生成（render_dependency_graph.py）
- 人別負荷分析（render_workload_table.py）
- 問題点レポート生成（issues_report）
- OR-Toolsによる最適化（solve_with_ortools.py、任意）
- HTMLダッシュボード生成（render_html.py、任意）

## セッション開始時の確認事項

不足情報がある場合は生成前に質問すること。特に：

- **対象ディレクトリ**: schedule-plannerのYAMLはどこにあるか（未指定ならSKILL_DIR自体のサンプルを使う）
- **勤務時間・昼休み**: settings.yamlに定義済みかどうか
- **optimize ON/OFF**: OR-Toolsを使うか（デフォルトfalse）
- **出力形式**: outputs.yamlで指定済みかどうか
- **タスク依存・担当者制約**: schedule.yaml / constraints.yamlで定義済みかどうか

## 実行フロー

1. **設定読み込み**: `settings.yaml` → プロジェクト名・勤務時間・時間単位を確認
2. **データ読み込み**: `members.yaml` / `constraints.yaml` / `schedule.yaml` を読み込み
3. **検証**: `python SKILL_DIR/scripts/validate.py` を実行。エラーがあればユーザーに報告して修正を促す
4. **最適化**（optimize=true の場合）: `python SKILL_DIR/scripts/solve_with_ortools.py` を実行
5. **結果生成**: `outputs/schedule_result.yaml` を生成（最適化しない場合はschedule.yamlから直接生成）
6. **出力生成**（outputs.yamlの設定に従う）:
   - `mermaid_gantt: true` → `python SKILL_DIR/scripts/render_mermaid.py`
   - `dependency_graph: true` → `python SKILL_DIR/scripts/render_dependency_graph.py`
   - `workload_table: true` → `python SKILL_DIR/scripts/render_workload_table.py`
   - `html_dashboard: true` → `python SKILL_DIR/scripts/render_html.py`
   - `issues_report: true` → 検証・分析結果から `outputs/issues_report.md` を生成

## 優先出力順序

Mermaid Ganttを最優先で生成し、チャットに直接表示する（即時プレビュー用）。
その後、他の出力ファイルを順次生成する。

## ファイル構成

```
schedule-planner/
├─ SKILL.md              ← このファイル
├─ settings.yaml         ← プロジェクト設定
├─ members.yaml          ← メンバー定義
├─ constraints.yaml      ← 制約条件
├─ schedule.yaml         ← タスク定義
├─ outputs.yaml          ← 出力設定
├─ templates/
│  ├─ task_template.yaml    ← タスク追加時のテンプレート
│  └─ member_template.yaml  ← メンバー追加時のテンプレート
├─ scripts/
│  ├─ validate.py
│  ├─ solve_with_ortools.py
│  ├─ render_mermaid.py
│  ├─ render_dependency_graph.py
│  ├─ render_workload_table.py
│  └─ render_html.py
├─ tasks/               ← 各タスクの手順書（Markdown）
├─ outputs/             ← 生成結果の出力先
└─ examples/
   └─ sample_project/   ← サンプル一式
```

## テンプレート利用案内

新しいタスクを追加する場合は `templates/task_template.yaml`、
新しいメンバーを追加する場合は `templates/member_template.yaml` を参照するよう案内する。
