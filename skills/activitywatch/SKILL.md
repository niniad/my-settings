---
name: activitywatch
description: >
  ActivityWatch（ローカルPC時間追跡ツール）のデータを取得・分析するスキル。
  PC使用状況のサマリー、カテゴリ別時間集計、22時以降の深夜帯分析を提供する。
  行動パターンの検証、睡眠改善の効果測定、時間配分の最適化に使用。
  トリガー：「PCの使用状況」「昨日何してた」「深夜のPC使用」「activitywatch」
  「22時以降」「時間の使い方を確認」「行動ログ」「スクリーンタイム」
---

# ActivityWatch データ分析スキル

ActivityWatch API（localhost:5600）からPC使用データを取得し、カテゴリ別に分析する。

## 使い方

スクリプト `scripts/aw_query.py` を実行する。依存パッケージ不要（標準ライブラリのみ）。

```bash
# 今日のサマリー
uv run python ~/.claude/skills/activitywatch/scripts/aw_query.py

# 直近7日間
uv run python ~/.claude/skills/activitywatch/scripts/aw_query.py --days 7

# 22時以降の深夜帯使用だけ
uv run python ~/.claude/skills/activitywatch/scripts/aw_query.py --after-22 --days 7

# 特定日
uv run python ~/.claude/skills/activitywatch/scripts/aw_query.py --date 2026-03-28

# JSON出力（プログラム連携用）
uv run python ~/.claude/skills/activitywatch/scripts/aw_query.py --json --days 7
```

## カテゴリ分類

スクリプトはアプリ名とウィンドウタイトルから自動分類する:

| カテゴリ | 判定条件 |
|---------|---------|
| EC (Amazon) | Seller Central, Amazon Ads |
| EC (NocoDB) | NocoDB |
| AI/開発 (VSCode/Claude) | VSCode, Code.exe |
| AI/開発 (GCP/GitHub) | BigQuery, Cloud Console, GitHub |
| AI/開発 | Claude, ChatGPT |
| 本業 (M365) | Outlook, Teams, Excel, Word, PowerPoint |
| コンテンツ消費 (YouTube) | YouTube |
| コンテンツ消費 (動画) | Prime Video, Netflix |
| コンテンツ消費 (SNS/ニュース) | Twitter/X, Reddit, ニュース |
| ゲーム | Minecraft, Steam, RimWorld |
| ブラウジング (その他) | Chrome, Firefox, Edge（上記に該当しないもの） |
| スリープ/放置 | unknown（PC画面が開いたまま放置） |
| システム | Explorer, LockApp |

分類ルールの追加・変更が必要な場合は `scripts/aw_query.py` の `categorize_app()` を編集する。

## 出力の読み方

- **アクティブ時間（AFK判定）**: マウス/キーボード操作があった時間（ActivityWatchのAFK watcher基準）
- **アプリ使用時間（放置除く）**: スリープ/放置・システムを除いた実質的な作業時間
- **深夜帯（22時-6時）**: 睡眠改善の指標。ここのアクティブ時間がゼロになることが目標

## 前提条件

- ActivityWatch がローカルで起動していること（http://localhost:5600）
- aw-watcher-window と aw-watcher-afk が有効であること
- ホスト名は自動検出（バケット名から取得）

## 活用シーン

- **睡眠改善の効果測定**: キッズタイマー設定後、22時以降の使用がゼロになったか確認
- **EC作業時間の実測**: 復職後、計画通り週5-6時間確保できているか
- **行動パターンの検証**: 「構築→飽き」パターンの兆候（EC関連時間の減少傾向）を検出
- **仮説検証のエビデンス**: 一次データとしてソース等級Aで利用可能
