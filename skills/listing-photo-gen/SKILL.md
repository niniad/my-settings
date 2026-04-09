# listing-photo-gen スキル

Gemini API で商品写真を生成し、Evaluator Agent で自動評価するスキル。
Generator + Evaluator ループ（最大3回）でベスト画像を選定する。

## 前提条件

- `/listing-infographic`（Phase 2: デザイン制作）が完了していること
- `ec/products/{slug}/appeal-map.md` の写真素材指示を確認すること
- Eagle が起動していること（画像ストア = Eagle Library）

## 写真プロンプト準備

プロンプトは `ec/products/{slug}/prompts/` に JSON 形式で保存する。
スキーマ: `ec/listings/brand/photo-prompts.md` 参照。

## ループ生成コマンド（推奨）

```bash
cd C:/Users/ninni/projects/ec/listings

uv run python scripts/generate_loop.py \
  --product mothers-backpack \
  --slot sub_02_2000x2000 \
  --prompt ../../products/mothers-backpack/prompts/sub02_pattern1.json \
  --inputs product_photo:ASSET_ID \
  --criteria "評価基準テキスト" \
  --max-iterations 3 \
  --threshold 28
```

## 単発生成コマンド

```bash
cd C:/Users/ninni/projects/ec/listings

uv run python scripts/generate.py \
  --product mothers-backpack \
  --slot sub_02_2000x2000 \
  --prompt ../../products/mothers-backpack/prompts/sub02_pattern1.json \
  --inputs product_photo:ASSET_ID
```

## 画像編集コマンド（生成済み画像の部分修正）

既存画像の特定部分だけを変更したい場合に使う。Evaluator ループ付き。

```bash
cd C:/Users/ninni/projects/ec/listings

# Eagle item ID を直接指定（推奨）
uv run python scripts/edit_image.py \
  --source MNJGWHGBVE7L0 \
  --instruction "ペットボトルをリュックの半分の高さに縮小。それ以外は変更しない" \
  --product mothers-backpack \
  --slot sub_02_2000x2000 \
  --criteria "ペットボトルがリュックより明らかに小さいか。その他の要素が変わっていないか" \
  --max-iterations 3 \
  --threshold 28

# asset_id（8文字hex）でも指定可
uv run python scripts/edit_image.py \
  --source 7b1465ce \
  --instruction "..." \
  --product mothers-backpack \
  --slot sub_02_2000x2000

# 追加参照画像あり（背景色の参照など）
uv run python scripts/edit_image.py \
  --source MNJGWHGBVE7L0 \
  --instruction "背景色を参照画像のトーンに合わせて" \
  --inputs tone_reference:7390b656 \
  --product mothers-backpack \
  --slot sub_02_2000x2000
```

### --source に指定できる値
| 形式 | 例 | 説明 |
|------|-----|------|
| Eagle item ID | `MNJGWHGBVE7L0` | Eagle の item ID（大文字英数字） |
| asset_id | `7b1465ce` | 8文字の小文字 hex |
| ファイルパス | `C:/path/to/image.jpg` | ローカルファイルパス |

### 生成との使い分け
- **部分的な修正**（サイズ・色・特定オブジェクトの変更）→ `edit_image.py`
- **構図・コンセプトの変更**（ポーズ・背景・エフェクトの全面変更）→ `generate_loop.py`

## アセット取り込み（実写真を Eagle に登録）

```bash
cd C:/Users/ninni/projects/ec/listings

uv run python scripts/import_asset.py \
  --product mothers-backpack \
  --file C:/path/to/photo.jpg \
  --slot product_photo
```

## Evaluator 評価4軸（各10点・合計40点・閾値28点）

| # | 軸 | チェック内容 |
|---|-----|-------------|
| 1 | ディテール忠実度 | 商品の形状・色・素材感が正確か |
| 2 | AI感のなさ | 自然な写真に見えるか（合成感・不自然さがないか） |
| 3 | テキスト品質 | 文字が含まれる場合、誤字・ぼけがないか |
| 4 | 構図・雰囲気 | appeal-map.md の指示と一致しているか |

## 生成履歴確認

```bash
cd C:/Users/ninni/projects/ec/listings

uv run python scripts/show_lineage.py \
  --product mothers-backpack \
  --slot sub_02_2000x2000
```

## 完了後・次工程

ベスト画像を appeal-map.md の写真素材 ASSET_ID として記録する。

**次工程 → `/listing-infographic`（Phase 4: HTML に写真挿入 → PNG 出力）**

## 参照ファイル

- `ec/listings/brand/photo-prompts.md` — プロンプトテンプレート集
- `ec/products/{slug}/prompts/` — 商品別プロンプト
- `ec/products/{slug}/slots/` — スロット別生成履歴
