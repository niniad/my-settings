#!/bin/bash
# GCP認証修復スクリプト

echo "=== GCP認証修復 ==="
echo ""

# 環境検出
if [ "$EUID" -eq 0 ]; then
    ENV_TYPE="cloud"
    DEFAULT_KEY_PATH="/root/.config/gcloud/service-account-key.json"
else
    ENV_TYPE="local"
    DEFAULT_KEY_PATH="$HOME/.config/gcloud/service-account-key.json"
fi

echo "環境: $ENV_TYPE"
echo ""

# 現在の認証状態確認
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -n "$CURRENT_ACCOUNT" ]; then
    echo "現在のアカウント: $CURRENT_ACCOUNT"
    echo ""
    read -p "再認証しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "キャンセルしました"
        exit 0
    fi
fi

# 認証方法の選択
echo ""
echo "認証方法を選択してください:"
echo "  1) サービスアカウントキー（推奨）"
echo "  2) ユーザー認証（gcloud auth login）"
echo ""
read -p "選択 (1/2): " -n 1 -r AUTH_METHOD
echo ""

case $AUTH_METHOD in
    1)
        # サービスアカウントキー認証
        KEY_PATH="${GOOGLE_APPLICATION_CREDENTIALS:-$DEFAULT_KEY_PATH}"

        if [ -f "$KEY_PATH" ]; then
            echo "キーファイル: $KEY_PATH"
        else
            echo "キーファイルが見つかりません: $KEY_PATH"
            read -p "キーファイルのパスを入力: " KEY_PATH
            if [ ! -f "$KEY_PATH" ]; then
                echo "エラー: ファイルが存在しません"
                exit 1
            fi
        fi

        echo "認証中..."
        if gcloud auth activate-service-account --key-file="$KEY_PATH"; then
            echo "✓ サービスアカウント認証成功"
            export GOOGLE_APPLICATION_CREDENTIALS="$KEY_PATH"

            # .bashrcに追加
            if ! grep -q 'GOOGLE_APPLICATION_CREDENTIALS' ~/.bashrc 2>/dev/null; then
                echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$KEY_PATH\"" >> ~/.bashrc
                echo "✓ 環境変数を.bashrcに追加しました"
            fi
        else
            echo "✗ 認証失敗"
            exit 1
        fi
        ;;
    2)
        # ユーザー認証
        if [ "$ENV_TYPE" = "cloud" ]; then
            echo "エラー: クラウド環境ではユーザー認証は使用できません"
            exit 1
        fi

        echo "ブラウザで認証を行ってください..."
        gcloud auth login
        gcloud auth application-default login
        echo "✓ ユーザー認証完了"
        ;;
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac

# プロジェクト設定確認
echo ""
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT" ] || [ "$PROJECT" = "(unset)" ]; then
    read -p "プロジェクトIDを入力 (空白でスキップ): " PROJECT_ID
    if [ -n "$PROJECT_ID" ]; then
        gcloud config set project "$PROJECT_ID"
        echo "✓ プロジェクトを設定しました: $PROJECT_ID"
    fi
fi

echo ""
echo "=== 認証修復完了 ==="
echo ""
echo "確認:"
gcloud auth list
