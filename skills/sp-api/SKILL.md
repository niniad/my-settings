---
name: sp-api
description: Amazon Selling Partner API（SP-API）の開発支援。注文管理、商品カタログ、レポート、在庫管理などのAPI操作をサポート。OpenAPI仕様を参照して正確なコード生成を行う。
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Amazon SP-API 開発支援

## 概要

Amazon Selling Partner API（SP-API）を使用したアプリケーション開発を支援します。

## API仕様の参照

OpenAPI仕様は以下に保存されています：
```
C:\Users\ninni\projects\my-settings\skills\sp-api\models\
```

### 主要API一覧

| API | フォルダ | 用途 |
|-----|---------|------|
| Orders API | `orders-api-model/` | 注文情報の取得・管理 |
| Catalog Items API | `catalog-items-api-model/` | 商品カタログ情報 |
| Reports API | `reports-api-model/` | レポート生成・取得 |
| Feeds API | `feeds-api-model/` | データ送信（価格・在庫更新） |
| Inventory API | `fba-inventory-api-model/` | FBA在庫管理 |
| Finances API | `finances-api-model/` | 財務情報 |
| Notifications API | `notifications-api-model/` | イベント通知 |
| Listings API | `listings-items-api-model/` | 出品情報管理 |

## 使用例

### 注文一覧取得のコードを生成
```
SP-APIで過去7日間の注文を取得するPythonコードを書いて
```

### 特定APIの仕様を確認
```
Reports APIで利用可能なレポートタイプを教えて
```

### 在庫更新フィードを作成
```
FBA在庫を更新するFeedsAPIのコードを書いて
```

## ガイドライン

### コード生成時の原則

1. **必ずOpenAPI仕様を参照**: コード生成前に該当APIのJSONファイルを読み込む
2. **認証処理を含める**: SP-APIはLWA（Login with Amazon）認証が必要
3. **レート制限を考慮**: API呼び出しにはスロットリングがある
4. **エラーハンドリング**: APIエラーレスポンスを適切に処理

### 推奨ライブラリ

- **python-amazon-sp-api**: Python用SP-APIラッパー
- **requests**: 直接API呼び出し時

### 認証情報

SP-API認証には以下が必要：
- **Client ID / Client Secret**: LWAアプリ認証情報
- **Refresh Token**: アクセストークン更新用
- **AWS Access Key / Secret Key**: リクエスト署名用

## API仕様の読み方

各APIフォルダには以下のファイルが含まれます：

```
orders-api-model/
├── ordersV0.json       # OpenAPI仕様（メイン）
└── ...
```

### 仕様確認コマンド

特定APIのエンドポイント一覧：
```bash
cat C:\Users\ninni\projects\my-settings\skills\sp-api\models\orders-api-model/ordersV0.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('\n'.join(d.get('paths',{}).keys()))"
```

## トラブルシューティング

### よくあるエラー

| エラー | 原因 | 対処 |
|--------|------|------|
| `Unauthorized` | 認証トークン期限切れ | Refresh Tokenで再取得 |
| `QuotaExceeded` | レート制限超過 | 待機後リトライ |
| `InvalidInput` | パラメータ不正 | API仕様を再確認 |

### 公式ドキュメント

- [SP-API公式ドキュメント](https://developer-docs.amazon.com/sp-api/docs/welcome)
- [APIリファレンス](https://developer-docs.amazon.com/sp-api/docs)
