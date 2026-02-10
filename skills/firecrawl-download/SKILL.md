---
name: firecrawl-download
description: Download entire documentation websites as Markdown with images using Firecrawl CLI. Use when retrieving documentation for offline use or context injection.
---

## 概要

Firecrawl CLIを使用してWebドキュメントサイトをMarkdown形式で一括ダウンロードする。

## 前提条件

- Firecrawl CLI (`firecrawl --version` で確認)
- 環境変数 `FIRECRAWL_API_KEY`
- クレジット残高確認 (`firecrawl usage`)

## 使用手順

### 基本コマンド

```bash
firecrawl crawl <URL> \
  --output /workspace/downloaded-docs \
  --format markdown \
  --max-depth 3 \
  --include-images \
  --rate-limit 5
```

### バッチダウンロード (推奨・安定版)

CLIの `crawl` コマンドが期待通りに動作しない場合、同梱のスクリプトを使用することで、各ページを個別の Markdown ファイルとして確実に保存できます。

```bash
node .agent/skills/firecrawl-download/scripts/batch_download.js <URL> <出力ディレクトリ> <上限数>
```

※ プロジェクトルート (`c:\Users\ninni\projects\.env`) に `.env` ファイルがあれば自動的に読み込みます。手動でセットする必要はありません。

### サイト規模別の推奨設定

| 規模 | ページ数 | 設定例 |
| :--- | :--- | :--- |
| **小規模** | ~50 | `--max-depth 3 --include-images --rate-limit 3` |
| **中規模** | 50~200 | `--max-depth 2 --include-images --rate-limit 5` |
| **大規模** | 200+ | `--max-depth 2 --rate-limit 10` (画像なし推奨) |

※ `--format markdown` は常に指定すること。

## 実行ワークフロー

1. **見積もり**: 対象サイトのページ数がクレジット残高（無料枠500/月）内か確認。
2. **テスト**: 単一ページまたは `--max-depth 1` で動作確認。
3. **本番実行**: 適切な `rate-limit` を設定して実行。
4. **検証**: 出力ディレクトリの構造とMarkdownの品質を確認。

## トラブルシューティング

- **Rate Limit Exceeded**: `--rate-limit` の値を増やす（例: 5 -> 10）。
- **JavaScriptコンテンツ**: `--wait-for 5000` を追加してレンダリングを待機。
- **クレジット不足**: `firecrawl usage` で確認。

## ベストプラクティス

- サーバー負荷を考慮し、必ず `rate-limit` を設定する。
- 巨大なサイトはサブディレクトリ単位でクロールすることを検討する。
- ダウンロードプロセスは中断しない（不完全なデータになるため）。
