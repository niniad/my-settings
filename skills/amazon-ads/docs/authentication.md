# Amazon Ads API 認証ガイド

## 認証フロー概要

Amazon Ads APIはLWA（Login with Amazon）OAuth 2.0認証を使用します。

```
1. Authorization Code取得（初回のみ）
2. Refresh Token → Access Token取得
3. Profile ID取得
4. API呼び出し（Access Token + Profile ID）
```

## 必要な認証情報

| 項目 | 説明 | 取得場所 |
|------|------|---------|
| Client ID | LWAアプリID | Amazon Developer Console |
| Client Secret | LWAアプリシークレット | Amazon Developer Console |
| Refresh Token | アクセストークン更新用 | OAuth認可フロー |
| Profile ID | 広告アカウントID | Profiles API |

## エンドポイント

### LWA Token エンドポイント
```
POST https://api.amazon.com/auth/o2/token
```

### 広告APIエンドポイント（リージョン別）

| リージョン | マーケットプレイス | エンドポイント |
|-----------|------------------|---------------|
| 北米 (NA) | US, CA, MX, BR | `advertising-api.amazon.com` |
| 欧州 (EU) | UK, DE, FR, IT, ES, NL, AE, PL, TR, EG, SA, SE, BE | `advertising-api-eu.amazon.com` |
| 極東 (FE) | JP, AU, SG, IN | `advertising-api-fe.amazon.com` |

## Python実装例

### Access Token取得

```python
import requests

def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Refresh TokenからAccess Tokenを取得"""
    response = requests.post(
        'https://api.amazon.com/auth/o2/token',
        data={
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
        }
    )
    response.raise_for_status()
    return response.json()['access_token']
```

### Profile ID取得

```python
def get_profiles(access_token: str, client_id: str, region: str = 'na') -> list:
    """広告プロファイル一覧を取得"""
    endpoints = {
        'na': 'https://advertising-api.amazon.com',
        'eu': 'https://advertising-api-eu.amazon.com',
        'fe': 'https://advertising-api-fe.amazon.com',
    }

    response = requests.get(
        f'{endpoints[region]}/v2/profiles',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': client_id,
        }
    )
    response.raise_for_status()
    return response.json()
```

### API呼び出し

```python
def call_ads_api(
    endpoint: str,
    access_token: str,
    client_id: str,
    profile_id: str,
    method: str = 'GET',
    data: dict = None
) -> dict:
    """Amazon Ads API呼び出し"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': str(profile_id),
        'Content-Type': 'application/json',
    }

    response = requests.request(
        method=method,
        url=endpoint,
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()
```

## 環境変数設定

```bash
export AMAZON_ADS_CLIENT_ID="your_client_id"
export AMAZON_ADS_CLIENT_SECRET="your_client_secret"
export AMAZON_ADS_REFRESH_TOKEN="your_refresh_token"
export AMAZON_ADS_PROFILE_ID="your_profile_id"
export AMAZON_ADS_REGION="fe"  # na, eu, fe
```

## トラブルシューティング

### よくあるエラー

| エラー | 原因 | 対処 |
|--------|------|------|
| `401 Unauthorized` | Access Token期限切れ | Refresh Tokenで再取得 |
| `403 Forbidden` | Profile IDが不正またはアクセス権なし | Profiles APIで確認 |
| `429 Too Many Requests` | レート制限超過 | 待機後リトライ |

### デバッグ用ヘッダー

レスポンスヘッダーで確認：
- `x-amz-rid`: リクエストID（サポート問い合わせ時に使用）
- `x-amzn-RateLimit-Limit`: レート制限値
