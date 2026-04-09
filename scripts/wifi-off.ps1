# Wi-Fiラジオをオフにする（右下パネルのWiFiボタンと同等）
# アダプターは無効化しない。右下パネルのWiFiボタンをワンクリックで復帰可能
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Runtime.WindowsRuntime

# ポップアップ通知
[System.Windows.Forms.MessageBox]::Show('22:00 就寝時間です', 'おやすみ', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)

# UWP Radio API でWiFiラジオをオフ
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null

# GetRadiosAsync
$asTaskGet = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$async = [Windows.Devices.Radios.Radio]::GetRadiosAsync()
$task = $asTaskGet.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($async))
$task.Wait()
$radios = $task.Result

$wifi = $radios | Where-Object { $_.Kind -eq 'WiFi' }
if ($wifi) {
    # SetStateAsync(Off)
    $asTaskSet = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    $setAsync = $wifi.SetStateAsync([Windows.Devices.Radios.RadioState]::Off)
    $setTask = $asTaskSet.MakeGenericMethod([Windows.Devices.Radios.RadioAccessStatus]).Invoke($null, @($setAsync))
    $setTask.Wait()
}
