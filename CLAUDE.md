# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

Claude Code のエージェントスキルを管理するリポジトリ。`skills/` は `~/.claude/skills` へのシンボリックリンクであり、ここでの変更はユーザーレベルの Claude Code スキルに直接反映される。

## 構成

- `skills/<name>/SKILL.md` — スキル定義（YAML frontmatter の `name` と `description` でトリガー判定）
- `skills/<name>/scripts/` — 実行スクリプト
- `skills/<name>/references/` — 参照ドキュメント
- `skills/anthropic/` — Anthropic 公式スキル
- `scripts/skills-to-zip.sh` — Claude Desktop アップロード用 ZIP 作成

## スキル作成・パッケージ化

```bash
python skills/skill-creator/scripts/init_skill.py <skill-name> --path skills/
python skills/skill-creator/scripts/package_skill.py skills/<skill-name>
```

## 認証

GCP Secret Manager（project: `main-project-477501`）で一元管理。ローカルに認証ファイルを置かない。
