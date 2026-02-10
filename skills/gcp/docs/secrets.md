# Secret Manager

## 基本操作

### シークレット一覧
```bash
gcloud secrets list
```

### シークレット作成
```bash
echo -n "secret-value" | gcloud secrets create my-secret --data-file=-
```

### シークレット取得
```bash
gcloud secrets versions access latest --secret=my-secret
```

### シークレット更新（新バージョン追加）
```bash
echo -n "new-value" | gcloud secrets versions add my-secret --data-file=-
```

### シークレット削除
```bash
gcloud secrets delete my-secret
```

## Python SDK

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
project_id = "main-project-477501"

# シークレット取得
name = f"projects/{project_id}/secrets/my-secret/versions/latest"
response = client.access_secret_version(request={"name": name})
secret_value = response.payload.data.decode("UTF-8")

# シークレット作成
parent = f"projects/{project_id}"
client.create_secret(
    request={
        "parent": parent,
        "secret_id": "my-secret",
        "secret": {"replication": {"automatic": {}}},
    }
)

# バージョン追加
parent = f"projects/{project_id}/secrets/my-secret"
client.add_secret_version(
    request={"parent": parent, "payload": {"data": b"secret-value"}}
)
```

## よくあるエラー

### Permission denied
```
権限不足。サービスアカウントに権限を付与：
- roles/secretmanager.secretAccessor（読み取り）
- roles/secretmanager.admin（管理）
```

### Secret not found
```
シークレットが存在しない。
gcloud secrets list で一覧を確認。
```
