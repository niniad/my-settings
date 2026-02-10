---
name: amazon-ads
description: Amazon Advertising API（Amazon Ads API）の開発支援。Sponsored Products、Sponsored Brands、Sponsored Display、Amazon DSPの広告管理・レポート取得をサポート。OpenAPI仕様を参照して正確なコード生成を行う。
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Amazon Advertising API 開発支援

## 概要

Amazon Advertising API（Amazon Ads API）を使用した広告管理アプリケーション開発を支援します。

## API仕様の参照

OpenAPIスキーマは以下に保存されています：
```
/home/ninni/projects/.claude/skills/amazon-ads/models/amazon-ads-api/docs/schemas/
```

### 主要API一覧

| API | スキーマファイル | 用途 |
|-----|----------------|------|
| Sponsored Products | `sponsored-products.json` | 商品広告の管理 |
| Sponsored Brands | `sponsored-brands.json` | ブランド広告の管理 |
| Sponsored Display | `sponsored-display.json` | ディスプレイ広告の管理 |
| Amazon DSP | `dsp.json` | プログラマティック広告 |
| DSP Reports | `dsp-reports.json` | DSPレポート取得 |
| Attribution | `attribution.json` | アトリビューション計測 |
| Brand Metrics | `brand-metrics.json` | ブランド指標 |
| Audiences | `common-audiences.json` | オーディエンス管理 |

### 補助スキーマ

| スキーマ | 用途 |
|---------|------|
| `authorization-profiles.json` | 認証プロファイル |
| `common-billing.json` | 請求情報 |
| `common-insights.json` | インサイト |
| `common-eligibility.json` | 適格性確認 |

## 使用例

### Sponsored Products キャンペーン作成
```
Amazon Ads APIでSponsored Productsキャンペーンを作成するコードを書いて
```

### レポート取得
```
過去30日間のSponsored Products広告パフォーマンスレポートを取得するコードを書いて
```

### DSP広告管理
```
Amazon DSPでオーディエンスを作成するコードを書いて
```

## ガイドライン

### コード生成時の原則

1. **必ずOpenAPIスキーマを参照**: コード生成前に該当APIのJSONファイルを読み込む
2. **認証処理を含める**: Amazon Ads APIはLWA（Login with Amazon）認証が必要
3. **マーケットプレイス指定**: リージョンごとにエンドポイントが異なる
4. **レート制限を考慮**: API呼び出しにはスロットリングがある

### エンドポイント（リージョン別）

| リージョン | エンドポイント |
|-----------|---------------|
| 北米 (NA) | `advertising-api.amazon.com` |
| 欧州 (EU) | `advertising-api-eu.amazon.com` |
| 極東 (FE) | `advertising-api-fe.amazon.com` |

### 認証フロー

```
1. Client ID/Secret でLWA認証
2. Access Token取得
3. Authorization: Bearer {access_token} ヘッダー付与
4. Amazon-Advertising-API-ClientId ヘッダー付与
5. Amazon-Advertising-API-Scope（プロファイルID）ヘッダー付与
```

### 推奨ライブラリ

- **ad-api-client**: Python用Amazon Ads APIクライアント
- **requests**: 直接API呼び出し時

## 公式リソース

- [Amazon Ads API ドキュメント](https://advertising.amazon.com/API/docs)
- [API Overview](https://advertising.amazon.com/API/docs/en-us/reference/api-overview)
- [Release Notes](https://advertising.amazon.com/API/docs/en-us/release-notes/index)
