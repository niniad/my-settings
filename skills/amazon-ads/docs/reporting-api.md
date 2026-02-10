# Amazon Ads Reporting API ガイド

## 概要

Amazon Ads Reporting APIは非同期レポート生成方式を採用しています。

```
1. POST /reporting/reports でレポートリクエスト作成
2. GET /reporting/reports/{reportId} でステータス確認（ポーリング）
3. COMPLETED後、レポートURLからダウンロード
```

## バージョン

| バージョン | 用途 | 状態 |
|-----------|------|------|
| v3 | Sponsored Products/Brands/Display | 現行 |
| v1 (beta) | 統合レポーティング | ベータ |
| DSP Reports | Amazon DSP専用 | 現行 |

## Reporting API v3

### エンドポイント

```
POST https://advertising-api.amazon.com/reporting/reports
GET  https://advertising-api.amazon.com/reporting/reports/{reportId}
```

### リクエストヘッダー

```http
Content-Type: application/vnd.createasyncreportrequest.v3+json
Amazon-Advertising-API-ClientId: {client_id}
Amazon-Advertising-API-Scope: {profile_id}
Authorization: Bearer {access_token}
```

### リクエストボディ

```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "configuration": {
    "adProduct": "SPONSORED_PRODUCTS",
    "groupBy": ["campaign", "adGroup"],
    "columns": [
      "date",
      "campaignId",
      "campaignName",
      "adGroupId",
      "adGroupName",
      "impressions",
      "clicks",
      "cost",
      "attributedSales14d",
      "attributedConversions14d"
    ],
    "reportTypeId": "spCampaigns",
    "timeUnit": "DAILY",
    "format": "GZIP_JSON"
  }
}
```

### adProduct 値

| 値 | 対象 |
|----|------|
| `SPONSORED_PRODUCTS` | Sponsored Products |
| `SPONSORED_BRANDS` | Sponsored Brands |
| `SPONSORED_DISPLAY` | Sponsored Display |

### 主要なカラム

#### 共通
- `date`, `campaignId`, `campaignName`, `adGroupId`, `adGroupName`
- `impressions`, `clicks`, `cost`, `costPerClick`

#### コンバージョン（14日アトリビューション）
- `attributedSales14d`, `attributedConversions14d`
- `attributedUnitsOrdered14d`

#### Sponsored Products固有
- `keywordId`, `keyword`, `keywordType`
- `advertisedAsin`, `purchasedAsin`

### レスポンス（レポート作成）

```json
{
  "reportId": "amzn1.clicksAPI.v1.p1.XXXXXXXX",
  "status": "PENDING"
}
```

### レスポンス（ステータス確認）

```json
{
  "reportId": "amzn1.clicksAPI.v1.p1.XXXXXXXX",
  "status": "COMPLETED",
  "url": "https://...",
  "urlExpiresAt": "2024-01-15T12:00:00Z"
}
```

## Reporting API v1 (Beta) - 統合レポーティング

2025年11月に発表された統合レポーティング機能。Sponsored AdsとDSPのメトリクスを統合。

### 特徴

- Sponsored Ads + DSPの統合ビュー
- 28マーケットで利用可能
- Report Builder UI / API / Amazon Marketing Stream対応

### 対応リージョン

- 北米: US, CA, MX
- 南米: BR
- 欧州: DE, UK, FR, ES, IT, NL, PL, SE, BE, TR
- 中東: AE, SA, EG
- アジア太平洋: JP, AU, IN, SG

## Python実装例

### レポート作成

```python
import requests
import time

def create_report(
    access_token: str,
    client_id: str,
    profile_id: str,
    start_date: str,
    end_date: str,
    ad_product: str = "SPONSORED_PRODUCTS",
    region: str = "fe"
) -> str:
    """レポートリクエストを作成"""
    endpoints = {
        'na': 'https://advertising-api.amazon.com',
        'eu': 'https://advertising-api-eu.amazon.com',
        'fe': 'https://advertising-api-fe.amazon.com',
    }

    response = requests.post(
        f'{endpoints[region]}/reporting/reports',
        headers={
            'Content-Type': 'application/vnd.createasyncreportrequest.v3+json',
            'Amazon-Advertising-API-ClientId': client_id,
            'Amazon-Advertising-API-Scope': str(profile_id),
            'Authorization': f'Bearer {access_token}',
        },
        json={
            'startDate': start_date,
            'endDate': end_date,
            'configuration': {
                'adProduct': ad_product,
                'groupBy': ['campaign'],
                'columns': [
                    'date', 'campaignId', 'campaignName',
                    'impressions', 'clicks', 'cost',
                    'attributedSales14d', 'attributedConversions14d'
                ],
                'reportTypeId': 'spCampaigns',
                'timeUnit': 'DAILY',
                'format': 'GZIP_JSON'
            }
        }
    )
    response.raise_for_status()
    return response.json()['reportId']
```

### レポート取得（ポーリング）

```python
def wait_for_report(
    report_id: str,
    access_token: str,
    client_id: str,
    profile_id: str,
    region: str = "fe",
    max_wait: int = 300
) -> str:
    """レポート完了を待機してURLを返す"""
    endpoints = {
        'na': 'https://advertising-api.amazon.com',
        'eu': 'https://advertising-api-eu.amazon.com',
        'fe': 'https://advertising-api-fe.amazon.com',
    }

    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(
            f'{endpoints[region]}/reporting/reports/{report_id}',
            headers={
                'Amazon-Advertising-API-ClientId': client_id,
                'Amazon-Advertising-API-Scope': str(profile_id),
                'Authorization': f'Bearer {access_token}',
            }
        )
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'COMPLETED':
            return data['url']
        elif data['status'] == 'FAILURE':
            raise Exception(f"Report failed: {data}")

        time.sleep(10)  # 10秒待機

    raise TimeoutError("Report generation timed out")
```

## トラブルシューティング

### レポートがPENDINGのまま

- 期間が長すぎる場合は分割する
- リトライ間隔を長くする（10-30秒）

### 空のレポート

- 期間内にデータが存在しない
- Profile IDが正しいか確認

### 429 Too Many Requests

- ポーリング間隔を広げる
- 同時リクエスト数を制限

## 参考リンク

- [Reporting API v3 Overview](https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/overview)
- [DSP Reports](https://advertising.amazon.com/API/docs/en-us/guides/reporting/dsp/creating-reports)
- [Python Amazon Ad API](https://python-amazon-ad-api.readthedocs.io/)
