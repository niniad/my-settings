# トラブルシューティング

## 診断スクリプト

問題発生時はまず診断スクリプトを実行：
```bash
bash .claude/skills/gcp/scripts/diagnose.sh
```

## よくある問題と解決策

### 1. 認証エラー

**症状:**
```
ERROR: (gcloud) You do not currently have an active account selected.
```

**解決策:**
```bash
# 診断
gcloud auth list

# 修復（ローカル環境）
gcloud auth login
gcloud auth application-default login

# 修復（サービスアカウント）
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
```

または自動修復スクリプト：
```bash
bash .claude/skills/gcp/scripts/fix-auth.sh
```

### 2. プロジェクト未設定

**症状:**
```
ERROR: (gcloud) The project property is not set.
```

**解決策:**
```bash
# プロジェクト一覧
gcloud projects list

# プロジェクト設定
gcloud config set project main-project-477501
```

### 3. 権限エラー

**症状:**
```
ERROR: (gcloud) Permission denied
```

**解決策:**
```bash
# 現在のアカウント確認
gcloud auth list

# 必要な権限をIAMで確認
gcloud projects get-iam-policy PROJECT_ID
```

### 4. APIが有効化されていない

**症状:**
```
ERROR: API [SERVICE_API] not enabled on project
```

**解決策:**
```bash
# API有効化
gcloud services enable storage.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 5. ネットワークエラー

**症状:**
```
ERROR: Network connectivity issues
```

**解決策:**
```bash
# 接続テスト
curl -I https://storage.googleapis.com
```

## 環境リセット

問題が解決しない場合：
```bash
# 再セットアップ
bash .claude/skills/gcp/setup.sh
```
