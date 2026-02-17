# Phase 3: 素材準備

## 目的

Phase 2のワイヤーフレームで必要とされる写真・イラスト素材を準備する。

## 素材リストの作成

ワイヤーフレームの「必要素材」欄から、全画像分の素材を一覧化する。各素材について以下を判定:

| 素材 | 入手方法 | 処理 |
|------|----------|------|
| 商品写真（白背景） | ユーザー提供 | 背景除去・色調補正 |
| 商品写真（部位アップ） | ユーザー提供 | トリミング・明るさ調整 |
| ライフスタイル写真 | AI生成 or ストック | プロンプト作成→生成 |
| 人物写真（推薦者等） | ユーザー提供 | 切り抜き・レタッチ |
| アイコン・バッジ | 自作 | SVG or HTML/CSSで作成 |
| 装飾要素 | 自作 | SVG or CSS |

## 1. 商品写真レタッチ

### 背景除去

```python
from rembg import remove
from PIL import Image

input_img = Image.open("product_photo.jpg")
output_img = remove(input_img)
output_img.save("product_nobg.png")
```

### 色調補正

```python
from PIL import Image, ImageEnhance

img = Image.open("product_nobg.png")

# 明るさ調整
enhancer = ImageEnhance.Brightness(img)
img = enhancer.enhance(1.1)  # 10%明るく

# コントラスト調整
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.15)  # 15%コントラスト強化

# 彩度調整
enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(1.1)  # 10%鮮やかに

img.save("product_enhanced.png")
```

### 影付け（ドロップシャドウ）

白背景に浮かぶ商品に自然な影をつける場合:

```python
from PIL import Image, ImageFilter

def add_shadow(img, offset=(10, 10), shadow_color=(0, 0, 0, 80), blur_radius=15):
    # 影用レイヤーを作成
    shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    # 商品のアルファチャンネルから影の形を取得
    alpha = img.split()[3]
    shadow_layer = Image.new('RGBA', img.size, shadow_color)
    shadow_layer.putalpha(alpha)
    # ぼかし
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    # 合成
    result = Image.new('RGBA', (img.width + abs(offset[0]) + blur_radius*2,
                                 img.height + abs(offset[1]) + blur_radius*2),
                        (255, 255, 255, 0))
    result.paste(shadow_layer, (offset[0] + blur_radius, offset[1] + blur_radius))
    result.paste(img, (blur_radius, blur_radius), img)
    return result
```

## 2. ライフスタイル素材のAI生成

### プロンプト設計のガイドライン

Amazon商品画像用のAI生成素材は以下に注意:

- **日本人モデル**: ベビー用品なら「Japanese mother」「Japanese toddler」を明示
- **自然な設定**: 過度にスタジオ感のない自然な家庭環境
- **商品は含めない**: 商品自体はAI生成しない（実物写真を使う）。あくまで背景・シーン・人物のみ生成
- **高解像度**: 最低1024×1024px以上で生成

### 典型的なプロンプト例

**泣いている赤ちゃん（お悩みシーン）**:
```
A Japanese toddler (around 1-2 years old) crying while sitting in a high chair,
messy food on the table, natural home kitchen setting, warm lighting,
photorealistic, high resolution
```

**洗濯シーン**:
```
A Japanese woman in her 30s putting laundry into a washing machine,
bright modern laundry room, natural daylight, photorealistic
```

**使用中の赤ちゃん（笑顔）**:
```
A happy Japanese toddler eating food while wearing a bib,
sitting in a high chair, natural home dining setting, warm lighting
```

### 生成後の処理

1. 不自然な部分がないか確認（指の本数、文字化け等）
2. 必要に応じてトリミング
3. 商品画像のカラートーンに合わせて色調補正
4. ワイヤーフレームの配置に合わせてリサイズ

## 3. アイコン・バッジの作成

### HTML/CSSで作成可能なもの

以下はPhase 4でHTML内に直接記述するため、素材としての準備は不要:

- ✕アイコン（問題提起用）
- ◎アイコン（解決策用）
- 番号バッジ（01, 02, 03）
- POINTバッジ
- 矢印（→, >>>）
- 星評価（★★★★☆）

### SVG or 画像として準備が必要なもの

- ブランドロゴ（Ufaロゴ等）→ ユーザーから提供を受ける
- 複雑なイラストアイコン
- キラキラ・手描き風の装飾

## 4. 手書き風テキスト画像

HTMLで再現困難な手書き風テキストへの対処:

### 方法A: Google Fontsの手書き風フォントを使用（推奨）

以下のフォントはHTML/CSSから直接使える:
- **Zen Kurenaido**: ナチュラルな手書き風
- **Yuji Syuku**: 筆書き風
- **Kaisei Opti**: 丸みのある手書き風
- **Klee One**: きれいな手書き風

```css
@import url('https://fonts.googleapis.com/css2?family=Zen+Kurenaido&display=swap');

.handwritten {
    font-family: 'Zen Kurenaido', sans-serif;
    font-size: 28px;
    color: #333;
}
```

### 方法B: 画像として生成

Google Fontsでは表現できないレベルの手書き感が必要な場合、テキスト画像をAIで生成するか、Canva等で手動作成する。

## 素材の管理

### ディレクトリ構造

```
project_name/
├── materials/
│   ├── product/          # 商品写真（原本・レタッチ済み）
│   │   ├── original/
│   │   └── processed/
│   ├── lifestyle/        # ライフスタイル素材
│   ├── icons/            # アイコン・バッジ
│   ├── decorations/      # 装飾要素
│   └── brand/            # ロゴ等ブランド素材
├── html/                 # Phase 4のHTMLファイル
└── output/               # 最終出力PNG
```

### ファイル命名規則

```
[画像番号]_[用途]_[説明].[拡張子]

例:
03_lifestyle_crying_baby.png
05_product_pocket_closeup.png
07_spec_front_dimensions.png
```
