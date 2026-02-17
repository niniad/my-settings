# ベンチマーク画像 タグ付けガイド

## 概要

ベンチマーク画像は「AIにデザインを生成させるための参考」ではなく「AIにレイアウト・構成設計を考えさせるための参考」として使う。タグ付けにより、訴求内容に合った構図パターンを効率的に検索できるようにする。

## NoCoDBテーブル設計

### テーブル名: `benchmarks`

| フィールド | タイプ | 必須 | 説明 |
|-----------|--------|------|------|
| id | AutoNumber | ○ | 自動採番 |
| image | Attachment | ○ | ベンチマーク画像ファイル |
| layout_type | SingleSelect | ○ | レイアウト構造タグ |
| appeal_type | SingleSelect | ○ | 訴求タイプタグ |
| category | SingleLineText | | 商品カテゴリ（Baby, Kitchen等） |
| source_asin | SingleLineText | | 参考元のASIN |
| memo | LongText | | 特徴メモ（カラー、フォント、気づき等） |
| created_at | DateTime | ○ | 登録日時（自動） |

### 運用方針: 最初は2軸だけで始める

最初から精緻なタグ体系を作っても使い始めると「この分類いらない」「この軸が足足りない」が出る。まず **layout_type** と **appeal_type** の2つだけでタグ付けし、20-30枚運用してからフィールド追加を検討する。

## タグ定義

### layout_type（レイアウト構造）

| タグ値 | 説明 | 典型的な構成 |
|--------|------|------------|
| `hero_text_side` | 大きな写真＋横にテキスト | 写真50%＋テキスト50%の左右分割 |
| `grid_comparison` | グリッド比較（✕ vs ◎） | 2列×N行の比較グリッド |
| `numbered_list` | ナンバリングリスト | 01/02/03の縦並びリスト |
| `spec_diagram` | 商品詳細図解 | 寸法線付き商品写真＋部位アップ |
| `endorsement` | 推薦者・権威 | 人物写真＋コメント |
| `variation_gallery` | バリエーション一覧 | N×Mのカラバリ/セット一覧 |
| `before_after` | Before/After | 左右 or 上下の変化比較 |
| `feature_callout` | 機能コールアウト | 写真に吹き出し的にテキスト配置 |
| `full_photo` | 写真メイン | テキスト最小限、写真で魅せる |
| `text_heavy` | テキスト主体 | 情報量が多い文章中心 |

### appeal_type（訴求タイプ）

| タグ値 | 説明 | 例 |
|--------|------|-----|
| `problem_agitation` | 問題提起・お悩み共感 | 「こんなお悩みありませんか？」 |
| `feature_benefit` | 機能→ベネフィット | 「3Dポケットで食べこぼしキャッチ」 |
| `competitive_advantage` | 比較優位 | 「従来品との違い」 |
| `authority` | 権威付け | 「保育士推薦」「受賞」 |
| `spec_detail` | スペック詳細 | 寸法、素材、重量 |
| `usage_scene` | 使用シーン | ライフスタイル写真中心 |
| `social_proof` | 社会証明 | レビュー、販売実績 |
| `brand_story` | ブランドストーリー | 開発背景、想い |

## ベンチマーク画像の収集方法

### 収集元

1. **Amazon BSR上位商品**: 同カテゴリのBSRトップ20-30のサブ画像
2. **楽天・Yahoo!ショッピング**: 他ECの同カテゴリ上位商品
3. **Pinterest**: インフォグラフィック系ボード

### 収集時の注意

- 他社画像の保存・利用は構図パターンの参考目的に限定する
- デザインを模倣する（レイアウトをコピーしてテキスト差し替え等）のはNG
- あくまで「このレイアウトパターンが効果的」という知見の蓄積

### 収集の目安

1カテゴリあたり20-30枚を目標。各layout_typeに最低2-3枚ずつあると検索時に選択肢がある。

## NocoDB APIでの検索

### 検索例

```bash
# レイアウト=grid_comparison かつ 訴求=problem_agitation のベンチマークを検索
curl "http://localhost:8080/api/v1/db/data/noco/{org}/{project}/benchmarks?where=(layout_type,eq,grid_comparison)~and(appeal_type,eq,problem_agitation)" \
  -H "xc-auth: YOUR_TOKEN"
```

### Pythonでの検索

```python
import requests

NOCODB_URL = "http://localhost:8080"
API_TOKEN = "YOUR_TOKEN"

def search_benchmarks(layout_type=None, appeal_type=None):
    params = {}
    conditions = []
    if layout_type:
        conditions.append(f"(layout_type,eq,{layout_type})")
    if appeal_type:
        conditions.append(f"(appeal_type,eq,{appeal_type})")
    if conditions:
        params["where"] = "~and".join(conditions)

    resp = requests.get(
        f"{NOCODB_URL}/api/v1/db/data/noco/org/project/benchmarks",
        headers={"xc-auth": API_TOKEN},
        params=params
    )
    return resp.json()["list"]
```

## タグ体系の拡張（将来）

20-30枚運用して必要性を感じたら、以下のフィールドを追加検討:

| フィールド | タイプ | 説明 |
|-----------|--------|------|
| color_palette | SingleSelect | warm / cool / pastel / monochrome |
| photo_ratio | SingleSelect | photo_heavy / text_heavy / balanced |
| decoration_density | SingleSelect | minimal / moderate / rich |
| target_audience | SingleSelect | baby / kitchen / beauty / general |
| effectiveness_score | Number | 主観的な「良いデザイン」スコア(1-5) |

NoCoDB上でフィールド追加は簡単にできるので、過剰設計より段階的拡張を推奨。
