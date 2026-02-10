# SP-API 認証ガイド

## 認証フロー概要

SP-APIはLWA（Login with Amazon）+ AWS Signature V4の二重認証が必要。

```
1. Refresh Token → LWA → Access Token取得
2. Access Token + AWS署名 → API呼び出し
```

## 必要な認証情報

| 項目 | 説明 | 取得場所 |
|------|------|---------|
| Client ID | LWAアプリID | Seller Central > アプリ開発 |
| Client Secret | LWAアプリシークレット | Seller Central > アプリ開発 |
| Refresh Token | アクセストークン更新用 | アプリ認可時に発行 |
| AWS Access Key | AWS IAMアクセスキー | AWS IAM |
| AWS Secret Key | AWS IAMシークレット | AWS IAM |
| Role ARN | IAMロールARN（オプション） | AWS IAM |

## Python実装例

### python-amazon-sp-api使用（推奨）

```python
from sp_api.api import Orders
from sp_api.base import Marketplaces

# 認証情報（環境変数から取得推奨）
credentials = {
    'refresh_token': 'YOUR_REFRESH_TOKEN',
    'lwa_app_id': 'YOUR_CLIENT_ID',
    'lwa_client_secret': 'YOUR_CLIENT_SECRET',
    'aws_access_key': 'YOUR_AWS_ACCESS_KEY',
    'aws_secret_key': 'YOUR_AWS_SECRET_KEY',
}

# Orders APIクライアント
orders_api = Orders(
    credentials=credentials,
    marketplace=Marketplaces.JP  # 日本マーケットプレイス
)

# 注文取得
response = orders_api.get_orders(CreatedAfter='2024-01-01')
print(response.payload)
```

### 環境変数設定

```bash
export SP_API_REFRESH_TOKEN="your_refresh_token"
export LWA_APP_ID="your_client_id"
export LWA_CLIENT_SECRET="your_client_secret"
export SP_API_ACCESS_KEY="your_aws_access_key"
export SP_API_SECRET_KEY="your_aws_secret_key"
```

## マーケットプレイスID

| 地域 | マーケットプレイス | ID |
|------|------------------|-----|
| 日本 | amazon.co.jp | A1VC38T7YXB528 |
| 米国 | amazon.com | ATVPDKIKX0DER |
| 英国 | amazon.co.uk | A1F83G8C2ARO7P |
| ドイツ | amazon.de | A1PA6795UKMFR9 |

## トラブルシューティング

### Access Denied
- IAMロールの権限を確認
- マーケットプレイスへのアクセス権限を確認

### Invalid Grant
- Refresh Tokenの有効期限を確認
- 再認可が必要な場合がある
