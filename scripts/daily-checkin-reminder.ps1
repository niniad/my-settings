# daily-checkin リマインダー
# 毎朝9:00にトースト通知を表示し、Claude Code セッションでの振り返りを促す

Add-Type -AssemblyName System.Windows.Forms

$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$balloon.BalloonTipTitle = "Daily Check-in"
$balloon.BalloonTipText = "前日の振り返りヒアリングをしましょう。`nClaude Code で /daily-checkin を実行してください。"
$balloon.Visible = $true
$balloon.ShowBalloonTip(10000)

Start-Sleep -Seconds 12
$balloon.Dispose()
