# MCP設定同期スクリプト
# 元データ: mcp-servers.json -> Claude Code (+ Claude Desktop 共有) / Antigravity に配信
# 使い方: powershell.exe -ExecutionPolicy Bypass -File scripts/sync.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$sourceFile = Join-Path $skillDir "mcp-servers.json"

if (-not (Test-Path $sourceFile)) {
    Write-Output "[ERROR] Source not found: $sourceFile"
    exit 1
}

$mcpConfig = Get-Content $sourceFile -Raw | ConvertFrom-Json
$serverNames = ($mcpConfig.mcpServers | Get-Member -MemberType NoteProperty).Name
Write-Output "Source: $sourceFile"
Write-Output "MCP Servers: $($serverNames -join ', ')"
Write-Output ""

# 1. Claude Code (via claude mcp commands)
Write-Output "--- Claude Code ---"
foreach ($name in $serverNames) {
    $server = $mcpConfig.mcpServers.$name
    $cmd = $server.command
    $args = $server.args -join " "

    # Remove existing first (ignore errors if not found)
    claude mcp remove $name -s user 2>$null | Out-Null

    # Build env flags
    $envFlags = ""
    if ($server.env) {
        $envProps = ($server.env | Get-Member -MemberType NoteProperty).Name
        foreach ($envKey in $envProps) {
            $envVal = $server.env.$envKey
            $envFlags += " -e ${envKey}=${envVal}"
        }
    }

    # Add MCP server
    $addCmd = "claude mcp add --scope user $name $envFlags -- $cmd $args"
    Invoke-Expression $addCmd 2>&1 | Out-Null
    Write-Output "[OK] Claude Code: $name"
}

# 2. Antigravity
Write-Output ""
Write-Output "--- Antigravity ---"
$agDir = Join-Path $env:USERPROFILE ".gemini\antigravity"
$agPath = Join-Path $agDir "mcp_config.json"
if (Test-Path $agDir) {
    $mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $agPath -Encoding UTF8
    Write-Output "[OK] Antigravity: $agPath"
} else {
    Write-Output "[SKIP] Antigravity: directory not found"
}

Write-Output ""
Write-Output "Sync complete. Please restart apps to apply changes."
