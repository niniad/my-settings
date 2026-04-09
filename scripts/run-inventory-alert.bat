@echo off
REM 在庫アラート週次実行バッチ
REM gcloudでTodoistトークンを取得し、スクリプトに渡す

for /f "tokens=*" %%i in ('gcloud secrets versions access latest --secret=todoist-api-token --project=main-project-477501') do set TODOIST_API_TOKEN=%%i

uv run --with google-cloud-bigquery python "%~dp0inventory-alert.py"
