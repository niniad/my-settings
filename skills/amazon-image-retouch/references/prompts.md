# レタッチプロンプトテンプレート

## 目次
- [カテゴリ 1: メイン画像](#カテゴリ-1-メイン画像amazon規約準拠)
- [カテゴリ 2: 物撮り・ディテール](#カテゴリ-2-物撮りディテール白背景)
- [カテゴリ 3: ライフスタイル](#カテゴリ-3-ライフスタイル使用シーン)
- [カテゴリ 4: 人物 + 商品](#カテゴリ-4-人物--商品)
- [カテゴリ 5: 比較・問題提起](#カテゴリ-5-比較問題提起)
- [クイックレタッチ](#クイックレタッチカテゴリ不問)

---

## カテゴリ 1: メイン画像（Amazon規約準拠）

**用途**: Amazon商品ページの画像1。検索結果サムネイルに表示される最重要画像。

**Amazon規約の制約（メイン画像のみ）:**

| 項目           | 要件                                 |
| -------------- | ------------------------------------ |
| 背景           | 純白（RGB 255,255,255）必須          |
| 商品占有率     | フレームの85%以上                    |
| テキスト・ロゴ | 不可（商品本体に印刷されたものは可） |
| 影・反射       | 許可（自然な影はOK）                 |
| 人物・小道具   | 不可（商品のみ）                     |
| 解像度         | 長辺1,600px以上（ズーム有効化）      |

### ベースプロンプト

```
Premium Amazon main product image of [product description]
on pure white background.

BACKGROUND: Pure white (#FFFFFF) everywhere — completely seamless
and uniform. No gradient, no warm or cool color cast, no texture,
no visible horizon line. The white must be identical in all four
corners and behind the product.

SHADOW: Add a soft, tight contact shadow directly beneath the
product base. The shadow should NOT spread wide — it stays close
to the base edge, with heavily diffused edges that fade to pure
white within 2-3cm. Opacity around 15-25%. This grounds the product
on the surface without creating visual heaviness.
Do NOT add a mirror/glossy floor reflection unless specifically requested.

LIGHTING: Soft, even, diffused studio lighting from multiple angles
(key light upper-left, fill lights from right and below).
The product should be uniformly lit — no harsh shadows on any surface,
no dark patches, no uneven brightness across the product.
Add ONE subtle specular highlight on the upper-left area of the product
to reveal the material's finish and create natural three-dimensionality.
This highlight should be gentle and blended — never a sharp white glare.

SURFACE: The product surface must be absolutely flawless:
- Zero dust, fingerprints, scratches, lint, water spots, or blemishes.
- All textures must be crisp, clearly defined, and consistent.
- Labels, prints, logos, and patterns must be razor-sharp and vibrant.
- Edges must be perfectly clean — no color fringing, no white halos.
- Seams, stitching, joints must appear precise and uniform.
The overall finish should look like a high-end CGI product render
while still feeling completely photorealistic.

COLOR: True-to-life color accuracy. Neutral white balance (5500-6000K).
No warm orange cast, no cool blue cast.
Boost color vibrancy by +5-10% for Amazon thumbnail visibility,
but keep it believable — not oversaturated.

SHARPNESS: Tack-sharp focus across the entire product. Every detail
must be clearly resolved for Amazon's zoom-on-hover feature.

SHAPE & DIMENSIONALITY: Natural, convincing three-dimensionality
through subtle depth cues. The product should look like a real 3D
object, not a flat graphic cutout.

COMPOSITION: Product centered, filling approximately 80-85% of
the canvas. Equal margins on all sides. Balanced and stable.

PRODUCT-SPECIFIC NOTES:
[Add product-specific details here — material finish, key features
to emphasize, specific angle, etc.]

Output: 2000px+ on longest side, sRGB color space.
```

### オプション: 鏡面反射シャドウ

Apple・Dyson等の高級路線には接地影の代わりに鏡面反射も有効。上記の SHADOW セクションを以下に差し替え:

```
REFLECTION SHADOW: Add a glossy floor reflection directly beneath
the product. The reflection should be a subtle mirror image of
the bottom 15-20%, fading to pure white with about 30-40% opacity.
The reflection should be slightly blurred compared to the product.
```

### メイン画像の追加推奨加工

1. **エッジコントラスト強化**: 白背景と商品の境界を微強調。サムネイルで形状明確に
2. **彩度微調整**: +5-10%。サムネイルで目立たせる
3. **特徴ディテール強調**: USPに関わる部分の影を微強調
4. **解像度**: 2000px以上。ズーム機能で質感を伝えられる

---

## カテゴリ 2: 物撮り・ディテール（白背景）

**用途**: サブ画像・A+コンテンツ用の商品写真。全体写真、クローズアップ、質感ショット等。

**メイン画像との違い**: テキスト後載せOK、小道具OK、影の表現自由、複数商品配置OK。

### ベースプロンプト

```
Product photograph of [subject description] on pure white background
for Amazon product listing sub-image.

BACKGROUND: Pure white (#FFFFFF) seamless backdrop.
Clean, uniform, no shadows or marks on the background surface.

LIGHTING: Controlled studio lighting — soft diffused key light
from upper-left, fill light from right to eliminate harsh shadows.
Add subtle highlights on surfaces to show material finish and quality.
The lighting should reveal texture and dimension without creating
harsh contrast or deep shadows.

SURFACE: Make all product surfaces flawless:
- Remove dust, scratches, fingerprints, lint, and imperfections.
- Restore textures to look brand-new and pristine.
- Make material quality clearly visible
  (fabric weave, metal finish, coating sheen, etc.).

FOCUS: Tack-sharp across the entire product. Fine details must be
clearly resolved — texture, stitching, hardware, labels.

COLOR: Neutral white balance. Boost vibrancy slightly (+5-10%)
for on-screen visibility. True-to-life color accuracy.

Add a subtle drop shadow beneath the product for natural depth.

Professional e-commerce product photography, high detail.
```

### バリエーション: マクロ・クローズアップ

上記に追加:

```
Macro close-up perspective. Fill 90%+ of the frame with the detail area.
Show fine material texture, grain, and craftsmanship at high magnification.
Shallow depth of field is acceptable to draw attention to the key feature.
```

---

## カテゴリ 3: ライフスタイル（使用シーン）

**用途**: 商品を実際の生活空間で撮影した写真。温かく、清潔で、憧れを感じさせる空間演出。

### ベースプロンプト

```
[Subject description] in a [setting description].

ENVIRONMENT: Transform the background into a clean, bright, modern space:
- [Surface type] (e.g., white wooden table, light marble counter)
- Soft natural window light from the left side
- A hint of [background element] in the blurred background
  (e.g., green plant, bookshelf, kitchen items)
Warm, inviting tones throughout. Remove clutter and distractions.

PRODUCT: Make the product look pristine and new:
- Smooth surface, vibrant colors, no stains or wear marks.
- The product should be the clear focal point of the image.

MOOD: Premium, warm, and aspirational — like a lifestyle photo
from a high-end brand catalog. Not staged or artificial.

PHOTOGRAPHY STYLE:
- Professional lifestyle product photography
- Shallow depth of field (background softly blurred)
- Natural daylight feel, warm color temperature (5500K)
- [Framing] perspective
  (e.g., eye-level upper body, overhead flat-lay, 45-degree angle)
```

---

## カテゴリ 4: 人物 + 商品

**用途**: 専門家の推薦、使用者の体験、権威付けなどで人物が商品と一緒に写る写真。

### ベースプロンプト

```
[Person description] with [product description].

BACKGROUND: Replace background with pure white (#FFFFFF) seamless,
or a clean, softly blurred professional environment.
Remove all wall shadows, clutter, and distracting elements.

LIGHTING: Bright, even studio lighting — soft and flattering
for portrait. No harsh shadows on the face or body.
The lighting should make the person look professional, friendly,
and trustworthy.

PERSON: Clean up appearance naturally:
- Smooth clothing wrinkles.
- Even skin tone (natural, not over-retouched).
- Pleasant, confident expression.
Do NOT alter the person's features or body shape.

PRODUCT: The product should look pristine with vibrant colors.
It should be clearly visible and well-lit, not hidden in shadow.

STYLE: Professional portrait/product photography for e-commerce.
The image conveys trust, expertise, and endorsement.
```

---

## カテゴリ 5: 比較・問題提起

**用途**: Before/After、競合比較、問題点の可視化。「✕」側の写真を含む。

### ベースプロンプト

```
[Problem/comparison description].

BACKGROUND: Clean up to pure white or very light grey.
Remove distracting elements while keeping the scene authentic.

LIGHTING: Apply even studio lighting so the photo looks professional.
The lighting should make the [problem/comparison detail] clearly visible
and immediately obvious to the viewer.

AUTHENTICITY: Keep the problematic aspect realistic and authentic.
Do NOT fix the issue being demonstrated — that IS the point of the photo.
But make the photo ITSELF look professionally shot.

CONTRAST: Enhance visual contrast so the key detail
(damage, mess, problem) stands out clearly at thumbnail size.

STYLE: Product comparison photography.
Clean and professional execution, authentic subject matter.
```

---

## クイックレタッチ（カテゴリ不問）

カテゴリを選ばず、とにかくスマホ写真を素早くプロ品質にしたい場合:

```
Transform this photo into a premium Amazon product listing image
that matches the quality of top-selling brands (BOTANIST, Anker, etc.).

LIGHTING: Replace existing lighting with professional studio lighting —
soft, even, diffused illumination from multiple angles. Eliminate all
harsh shadows, uneven brightness, and mixed color temperatures.
Add one subtle specular highlight to show material finish and depth.

SURFACE: Make every visible product surface absolutely flawless:
- Remove all dust, scratches, fingerprints, lint, water spots, stains.
- Smooth out wrinkles, creases, and wear marks.
- Restore textures to look brand-new and pristine.
- Clean up edges — no fringing, halos, or cutout artifacts.

FOCUS: Tack-sharp across the entire product.

COLOR: Neutral white balance (5500-6000K). Boost vibrancy +5-10%.
No color cast. True-to-life accuracy.

BACKGROUND: If on white, make it pure seamless white (#FFFFFF).
If lifestyle/contextual, clean up and enhance the environment
to look bright, modern, and aspirational.

The final image should be indistinguishable from professional
studio photography.
```
