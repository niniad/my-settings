#!/bin/bash
# GCP環境セットアップスクリプト

set -e

echo "=== GCP環境セットアップ ==="

# 1. gcloud CLIの確認
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLIがインストールされていません"
    echo "インストール: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "✅ gcloud CLI: $(gcloud --version | head -1)"

# 2. 認証設定
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
    echo "📝 環境変数からサービスアカウントキーを設定中..."
    mkdir -p ~/.config/gcloud
    echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > ~/.config/gcloud/application_default_credentials.json
    export GOOGLE_APPLICATION_CREDENTIALS=~/.config/gcloud/application_default_credentials.json
    gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
    echo "✅ サービスアカウント認証完了"
elif [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "📝 キーファイルから認証中..."
    gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
    echo "✅ サービスアカウント認証完了"
else
    echo "⚠️  認証情報が見つかりません。手動でログインしてください:"
    echo "   gcloud auth login"
    echo "   gcloud auth application-default login"
fi

# 3. プロジェクト設定
PROJECT_ID="${GCP_PROJECT_ID:-main-project-477501}"
gcloud config set project "$PROJECT_ID"
echo "✅ プロジェクト設定: $PROJECT_ID"

# 4. リージョン設定
gcloud config set run/region us-central1
gcloud config set scheduler/location us-central1
echo "✅ リージョン設定: us-central1"

# 5. Python SDKインストール確認
if command -v pip &> /dev/null; then
    echo "📦 Python SDKをインストール中..."
    pip install --quiet google-cloud-storage google-cloud-bigquery google-cloud-secret-manager google-cloud-run google-cloud-scheduler 2>/dev/null || true
    echo "✅ Python SDKインストール完了"
fi

echo ""
echo "=== セットアップ完了 ==="
echo "現在のアカウント:"
gcloud auth list --filter=status:ACTIVE --format="value(account)"
