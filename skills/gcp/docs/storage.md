# Cloud Storage

## 基本操作

### バケット一覧
```bash
gsutil ls
```

### ファイルアップロード
```bash
gsutil cp local-file.txt gs://bucket-name/
gsutil -m cp -r local-dir/ gs://bucket-name/  # 並列・再帰
```

### ファイルダウンロード
```bash
gsutil cp gs://bucket-name/file.txt ./
gsutil -m cp -r gs://bucket-name/dir/ ./  # 並列・再帰
```

### ファイル一覧
```bash
gsutil ls gs://bucket-name/
gsutil ls -l gs://bucket-name/  # 詳細
```

### ファイル削除
```bash
gsutil rm gs://bucket-name/file.txt
gsutil -m rm -r gs://bucket-name/dir/  # 再帰削除
```

## Python SDK

```python
from google.cloud import storage

client = storage.Client()

# バケット一覧
for bucket in client.list_buckets():
    print(bucket.name)

# アップロード
bucket = client.bucket("bucket-name")
blob = bucket.blob("file.txt")
blob.upload_from_filename("local-file.txt")

# ダウンロード
blob.download_to_filename("downloaded-file.txt")
```

## よくあるエラー

### AccessDeniedException
```
権限不足。サービスアカウントにStorage権限を付与：
- roles/storage.objectViewer（読み取り）
- roles/storage.objectAdmin（読み書き）
```

### BucketNotFoundException
```
バケットが存在しない、またはアクセス権がない。
gsutil ls でバケット一覧を確認。
```
