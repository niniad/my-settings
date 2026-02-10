---
name: mcp-sync
description: MCP サーバー設定の一元管理と同期。mcp-servers.json を元データとして Claude Code（Claude Desktop共有）・Antigravity に自動配信。トリガー：MCP設定の追加・変更・削除、MCPサーバー同期、ツール間の設定統一時。
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# MCP設定 一元管理

## 概要

`mcp-servers.json` を単一の元データ（Single Source of Truth）とし、全AIツールのMCP設定を同期する。

## 使い方

### 1. MCP サーバーを追加/変更する

`mcp-servers.json` を編集:
```json
{
  "mcpServers": {
    "サーバー名": {
      "command": "npx",
      "args": ["-y", "パッケージ名"],
      "env": {}
    }
  }
}
```

### 2. 全ツールに同期

```powershell
powershell.exe -ExecutionPolicy Bypass -File .claude/skills/mcp-sync/scripts/sync.ps1
```

## 配信先

| ツール | 方法 |
|--------|------|
| Claude Code / Claude Desktop | `claude mcp add/remove` コマンドで user scope に登録（`~/.claude.json` 共有） |
| Antigravity | `%USERPROFILE%\.gemini\antigravity\mcp_config.json` に書き込み |

## 現在の MCP サーバー一覧

`mcp-servers.json` を参照。

## 注意

- 同期後は各アプリを再起動すること
- Claude Desktop は Claude Code と `~/.claude.json` を共有するため、個別の同期は不要
