# Windows Task Scheduler — 自作タスク一覧

## タスク一覧

| タスク名 | スケジュール | 実行内容 | スクリプト |
|----------|------------|---------|-----------|
| NocoDB_Daily_Backup | 毎日 3:00 | NocoDB を Google Drive にバックアップ（対数リテンション、最大9ファイル） | `scripts/backup_nocodb.py` |
| NocoDB-to-BQ-Daily | 毎日 9:30 | NocoDB → BigQuery 日次同期 | `C:\Users\ninni\infra\nocodb-to-bq\run_sync.bat` |
| WiFiOff22 | 毎日 22:00 | Wi-Fi アダプタを無効化（netsh 直接実行） | なし（netsh直接） |

## 補足

- PC未起動時: `StartWhenAvailable=True` により次回起動時に実行される
- バッテリー動作: 全タスク実行可
- ログ: NocoDB バックアップ → `C:\Users\ninni\nocodb\backup.log`

## WiFi 復旧

22時にWiFiが切れた後、復旧するには:
- デスクトップの「WiFi-ON」ショートカットをダブルクリック
- または `my-settings\scripts\wifi-on.bat` を実行

## タスク管理コマンド

```powershell
# 一覧確認
Get-ScheduledTask -TaskPath "\" | Where-Object {$_.TaskName -match "NocoDB|WiFi"}

# 手動実行
Start-ScheduledTask -TaskName "NocoDB_Daily_Backup"

# 新規タスク追加時はこのファイルも更新すること
```
