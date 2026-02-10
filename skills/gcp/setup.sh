#!/bin/bash
# GCP開発環境セットアップスクリプト（汎用版）
# Claude Code Web版・CLI版・VSCode版に対応
# ローカルUbuntu環境とクラウド環境の両方で動作

set -e

# 環境検出
detect_environment() {
    if [ "$EUID" -eq 0 ]; then
        echo "cloud"  # root権限 = Web版（クラウド環境）
    else
        echo "local"  # 非root = ローカル環境
    fi
}

ENV_TYPE=$(detect_environment)
echo "=== GCP開発環境セットアップ（${ENV_TYPE}環境） ==="

# gcloud CLIがインストールされているか確認
if ! command -v gcloud &> /dev/null; then
    echo "gcloud CLIをインストール中..."

    if [ "$ENV_TYPE" = "cloud" ]; then
        # クラウド環境: /optにインストール
        if [ -d "/opt/google-cloud-sdk" ]; then
            rm -rf /opt/google-cloud-sdk
        fi
        curl -sSL https://sdk.cloud.google.com > /tmp/install_gcloud.sh
        bash /tmp/install_gcloud.sh --disable-prompts --install-dir=/opt
        export PATH="/opt/google-cloud-sdk/bin:$PATH"
        GCLOUD_PATH="/opt/google-cloud-sdk/bin"
    else
        # ローカルUbuntu環境: aptでインストール
        echo "aptパッケージからgcloud CLIをインストールします..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq apt-transport-https ca-certificates gnupg curl

        if [ ! -f /usr/share/keyrings/cloud.google.gpg ]; then
            curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
        fi

        echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null
        sudo apt-get update -qq && sudo apt-get install -y -qq google-cloud-cli
        GCLOUD_PATH="/usr/bin"
    fi
else
    echo "gcloud CLIは既にインストールされています"
    GCLOUD_PATH=$(dirname "$(which gcloud)")
fi

# PATHを確実に設定
export PATH="$GCLOUD_PATH:/usr/bin:/bin:/usr/local/bin:$PATH"

# PATHを.bashrcに追加（未設定の場合）
if ! grep -q 'google-cloud-sdk' ~/.bashrc 2>/dev/null && ! grep -q 'gcloud' ~/.bashrc 2>/dev/null; then
    if [ "$ENV_TYPE" = "cloud" ]; then
        echo 'export PATH="/opt/google-cloud-sdk/bin:$PATH"' >> ~/.bashrc
    fi
fi

# Python ライブラリをインストール（GCP_PYTHON_LIBSが指定されていればそれを使用）
if [ -n "$GCP_PYTHON_LIBS" ]; then
    echo "Python GCPライブラリをインストール中..."
    pip3 install --quiet --ignore-installed $GCP_PYTHON_LIBS 2>/dev/null || true
else
    echo "Python GCPライブラリをインストール中（デフォルト）..."
    pip3 install --quiet --ignore-installed \
        google-cloud-storage \
        google-cloud-bigquery \
        google-cloud-secret-manager \
        google-cloud-functions \
        google-cloud-scheduler \
        google-cloud-logging \
        cffi \
        cryptography 2>/dev/null || true
fi

# サービスアカウントキーの設定
if [ "$ENV_TYPE" = "cloud" ]; then
    DEFAULT_KEY_PATH="/root/.config/gcloud/service-account-key.json"
else
    DEFAULT_KEY_PATH="$HOME/.config/gcloud/service-account-key.json"
fi
KEY_PATH="${GCP_KEY_PATH:-$DEFAULT_KEY_PATH}"
mkdir -p "$(dirname "$KEY_PATH")"

# 認証方法の決定
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then
    # 方法1: 環境変数からJSONを読み取る（主にWeb版）
    echo "環境変数からサービスアカウントキーを設定中..."
    echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" | sed "s/^'//; s/'$//" > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
    echo "✓ 環境変数からキーを設定しました"
    AUTH_METHOD="service_account"
elif [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    # 方法2: 既存のGOOGLE_APPLICATION_CREDENTIALS環境変数
    KEY_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
    echo "既存の認証情報を使用します: $KEY_PATH"
    AUTH_METHOD="service_account"
elif [ -f "$KEY_PATH" ]; then
    # 方法3: デフォルトパスにキーファイルが存在
    echo "既存のサービスアカウントキーを使用します: $KEY_PATH"
    AUTH_METHOD="service_account"
elif [ "$ENV_TYPE" = "local" ]; then
    # 方法4: ローカル環境でADC（Application Default Credentials）を確認
    if gcloud auth application-default print-access-token &>/dev/null; then
        echo "Application Default Credentials (ADC) を使用します"
        AUTH_METHOD="adc"
    else
        echo ""
        echo "認証情報が見つかりません。以下のいずれかを実行してください："
        echo ""
        echo "  1. gcloud auth login && gcloud auth application-default login"
        echo "  2. サービスアカウントキーを $KEY_PATH に配置"
        echo "  3. 環境変数 GOOGLE_APPLICATION_CREDENTIALS を設定"
        echo ""
        exit 1
    fi
else
    echo "エラー: サービスアカウントキーが見つかりません"
    echo ""
    echo "環境変数 GOOGLE_APPLICATION_CREDENTIALS_JSON にサービスアカウントキー（JSON）を設定してください"
    exit 1
fi

# 認証方法に応じた処理
if [ "$AUTH_METHOD" = "service_account" ]; then
    # 環境変数を設定
    export GOOGLE_APPLICATION_CREDENTIALS="$KEY_PATH"
    if ! grep -q 'GOOGLE_APPLICATION_CREDENTIALS' ~/.bashrc 2>/dev/null; then
        echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_PATH\"" >> ~/.bashrc
    fi

    # gcloud認証
    echo "gcloud 認証を実行中..."
    if gcloud auth activate-service-account --key-file="$KEY_PATH" 2>&1 | grep -q "Activated service account"; then
        echo "✓ サービスアカウント認証成功"
    else
        echo "警告: 認証に問題が発生した可能性があります"
    fi
else
    # ADC認証の場合
    echo "✓ ADC認証を使用中"
fi

# プロジェクトを設定（GCP_PROJECT_IDが指定されていればそれを使用）
if [ -n "$GCP_PROJECT_ID" ]; then
    PROJECT_ID="$GCP_PROJECT_ID"
    gcloud config set project "$PROJECT_ID" 2>/dev/null
    echo "✓ プロジェクトを設定しました: $PROJECT_ID"
else
    echo "注意: GCP_PROJECT_ID が設定されていません。プロジェクトは設定されていません。"
fi

# 認証情報を確認
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

echo ""
echo "=== セットアップ完了 ==="
echo "プロジェクト: ${CURRENT_PROJECT:-未設定}"
echo "サービスアカウント: $ACCOUNT"
echo ""
echo "利用可能なサービス:"
echo "  - gcloud CLI"
echo "  - gsutil (Cloud Storage)"
echo "  - bq (BigQuery)"
echo "  - Python GCP SDKs"
echo ""
