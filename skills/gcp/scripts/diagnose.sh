#!/bin/bash
# GCP環境診断スクリプト

echo "=== GCP環境診断 ==="
echo ""

# 1. gcloud CLI確認
echo "[1] gcloud CLI"
if command -v gcloud &> /dev/null; then
    echo "  ✓ インストール済み: $(gcloud --version 2>/dev/null | head -1)"
else
    echo "  ✗ 未インストール"
    echo "  → bash .claude/skills/gcp/setup.sh を実行してください"
fi
echo ""

# 2. 認証状態確認
echo "[2] 認証状態"
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
if [ -n "$ACCOUNT" ]; then
    echo "  ✓ アクティブアカウント: $ACCOUNT"
else
    echo "  ✗ 認証されていません"
    echo "  → bash .claude/skills/gcp/scripts/fix-auth.sh を実行してください"
fi
echo ""

# 3. プロジェクト確認
echo "[3] プロジェクト設定"
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT" ] && [ "$PROJECT" != "(unset)" ]; then
    echo "  ✓ プロジェクト: $PROJECT"
else
    echo "  ✗ プロジェクト未設定"
    echo "  → gcloud config set project PROJECT_ID を実行してください"
fi
echo ""

# 4. 環境変数確認
echo "[4] 環境変数"
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "  ✓ GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
    else
        echo "  ✗ GOOGLE_APPLICATION_CREDENTIALS: ファイルが存在しません"
    fi
else
    echo "  - GOOGLE_APPLICATION_CREDENTIALS: 未設定（ADC使用の可能性）"
fi
echo ""

# 5. サービス接続テスト
echo "[5] サービス接続テスト"

# Cloud Storage
if gsutil ls &>/dev/null; then
    echo "  ✓ Cloud Storage: 接続OK"
else
    echo "  ✗ Cloud Storage: 接続失敗"
fi

# BigQuery
if bq ls &>/dev/null; then
    echo "  ✓ BigQuery: 接続OK"
else
    echo "  ✗ BigQuery: 接続失敗"
fi

echo ""
echo "=== 診断完了 ==="
