# Phase 4: デザイン生成（HTML/CSS → PNG）

## 目的

Phase 2のワイヤーフレームとPhase 3の素材を使い、HTML/CSSでデザインを組み立て、Puppeteerで高解像度PNGとして出力する。

## 基本方針

Amazon商品画像の本質は「エディトリアルレイアウト」。画像生成AIではなくHTML/CSSで組み立てる理由:

- 日本語テキストが1文字の誤りもなく正確にレンダリングされる
- フォントサイズ・ウェイト・行間を正確にコントロールできる
- テキスト修正がHTML編集→再レンダリングの数秒で完了する
- テンプレート化すれば同シリーズ商品に即座に横展開できる

## HTMLテンプレートの基本構造

### 共通ベーステンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Zen+Kurenaido&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: {{WIDTH}}px;
    height: {{HEIGHT}}px;
    font-family: 'Noto Sans JP', sans-serif;
    overflow: hidden;
    background: {{BG_COLOR}};
  }

  .container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: {{PADDING}}px;
  }

  /* テキストヒエラルキー */
  .heading-xl { font-size: 64px; font-weight: 900; line-height: 1.3; }
  .heading-lg { font-size: 48px; font-weight: 700; line-height: 1.3; }
  .heading-md { font-size: 36px; font-weight: 700; line-height: 1.4; }
  .body-lg    { font-size: 28px; font-weight: 500; line-height: 1.6; }
  .body-md    { font-size: 24px; font-weight: 400; line-height: 1.6; }
  .caption    { font-size: 18px; font-weight: 400; line-height: 1.5; color: #666; }
  .handwritten {
    font-family: 'Zen Kurenaido', sans-serif;
    font-size: 28px;
    line-height: 1.5;
  }

  /* よく使う装飾 */
  .badge {
    display: inline-block;
    background: #E85B2A;
    color: white;
    padding: 8px 24px;
    border-radius: 4px;
    font-weight: 700;
  }

  .number-circle {
    width: 60px; height: 60px;
    border-radius: 50%;
    background: #E85B2A;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 900;
  }

  .icon-ng { color: #CC3333; font-size: 36px; font-weight: 900; }
  .icon-ok { color: #339933; font-size: 36px; font-weight: 900; }

  img { max-width: 100%; height: auto; object-fit: contain; }
</style>
</head>
<body>
  <div class="container">
    <!-- コンテンツここに -->
  </div>
</body>
</html>
```

### テンプレート変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `{{WIDTH}}` | 2000 | 画像幅（px） |
| `{{HEIGHT}}` | 2000 | 画像高さ（px） |
| `{{BG_COLOR}}` | #FFFFFF | 背景色 |
| `{{PADDING}}` | 60 | 外側パディング |

## レイアウトパターン別HTML構造

### hero_text_side（写真＋横テキスト）

```html
<div class="container">
  <!-- 上部見出し -->
  <div style="text-align: center; margin-bottom: 40px;">
    <span class="badge">POINT 02</span>
    <h1 class="heading-lg" style="margin-top: 16px;">食べこぼしをしっかりキャッチ</h1>
  </div>

  <!-- メインコンテンツ：写真＋テキスト横並び -->
  <div style="display: flex; gap: 40px; flex: 1;">
    <div style="flex: 1;">
      <img src="materials/product/pocket_closeup.png" alt="">
    </div>
    <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 32px;">
      <div>
        <h2 class="heading-md" style="color: #E85B2A;">3Dポケット</h2>
        <p class="body-md">立体的なポケットが食べこぼしをしっかりキャッチ</p>
      </div>
      <div>
        <h2 class="heading-md" style="color: #E85B2A;">体にフィット</h2>
        <p class="body-md">柔らかい素材が体に沿ってフィット</p>
      </div>
    </div>
  </div>
</div>
```

### grid_comparison（✕ vs ◎ 比較）

```html
<div class="container">
  <h1 class="heading-lg" style="text-align: center; margin-bottom: 40px;">
    他社との違い
  </h1>

  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2px; background: #ddd;">
    <!-- ヘッダー行 -->
    <div style="background: #f5f5f5; padding: 24px; text-align: center;">
      <span class="icon-ng">✕</span>
      <span class="body-lg">従来品</span>
    </div>
    <div style="background: #FFF8F0; padding: 24px; text-align: center;">
      <span class="icon-ok">◎</span>
      <span class="body-lg">当社製品</span>
    </div>

    <!-- 比較行1 -->
    <div style="background: #fff; padding: 24px;">
      <img src="materials/comparison/old_flat.png" style="width: 100%; margin-bottom: 16px;">
      <p class="body-md">平面的で食べこぼしがこぼれる</p>
    </div>
    <div style="background: #FFF8F0; padding: 24px;">
      <img src="materials/comparison/new_3d.png" style="width: 100%; margin-bottom: 16px;">
      <p class="body-md">3Dポケットでしっかりキャッチ</p>
    </div>
  </div>
</div>
```

### numbered_list（ナンバリング）

```html
<div class="container">
  <p class="handwritten" style="text-align: center; margin-bottom: 16px;">
    お食事エプロンってどうやって選べばいいの？
  </p>
  <h1 class="heading-lg" style="text-align: center; margin-bottom: 48px;">
    100人のパパママに聞いた<br>お悩みポイント3選
  </h1>

  <div style="display: flex; flex-direction: column; gap: 32px;">
    <!-- 項目1 -->
    <div style="display: flex; align-items: center; gap: 24px; background: #fff; border-radius: 16px; padding: 32px;">
      <div class="number-circle">01</div>
      <img src="materials/lifestyle/crying_baby.png" style="width: 200px; height: 200px; object-fit: cover; border-radius: 12px;">
      <div>
        <h2 class="heading-md">子供が付けるのを嫌がる!!</h2>
        <p class="body-md" style="color: #666;">首回りの素材が硬くて不快に感じてしまう</p>
      </div>
    </div>

    <!-- 項目2, 3 は同構造で繰り返し -->
  </div>
</div>
```

## フォント選定ガイド

### 日本語フォント（Google Fonts）

| フォント | 用途 | 印象 |
|---------|------|------|
| Noto Sans JP | メインフォント（万能） | モダン・信頼感 |
| Zen Maru Gothic | 柔らかい見出し | やさしい・親しみ |
| Zen Kurenaido | 手書き風テキスト | ナチュラル・共感 |
| M PLUS Rounded 1c | 丸ゴシック | かわいい・ベビー用品向き |
| Klee One | きれいめ手書き | 上品・清潔感 |

### フォントウェイトの使い分け

| ウェイト | 用途 |
|---------|------|
| 900 (Black) | 最重要キーワード（「嫌がる!!」「吸水性抜群」） |
| 700 (Bold) | 見出し |
| 500 (Medium) | 本文（やや強調） |
| 400 (Regular) | 通常テキスト・キャプション |

## カラーパレット設計

### ベビー用品向けデフォルトパレット

```css
:root {
  --primary: #E85B2A;       /* 暖色オレンジ：CTA・バッジ・強調 */
  --primary-light: #FFF3EC; /* 薄いオレンジ：背景 */
  --accent: #4A9B8E;        /* ティール：信頼感・サブカラー */
  --text-dark: #333333;     /* メインテキスト */
  --text-gray: #666666;     /* サブテキスト */
  --bg-warm: #FAF7EB;       /* 暖かい背景色 */
  --bg-white: #FFFFFF;      /* 白背景 */
  --ng-red: #CC3333;        /* NG表示 */
  --ok-green: #339933;      /* OK表示 */
}
```

商品やブランドに合わせてカスタマイズする。パレットは訴求マップ設計時にユーザーと確認。

## Puppeteerでのレンダリング

`scripts/render_html.py` を使用してHTMLをPNGに変換する。

### 基本的な使い方

```bash
python scripts/render_html.py input.html output.png --width 2000 --height 2000
```

### レンダリング時の注意点

1. **フォント読み込み待ち**: Google Fontsの読み込みを待つため、`waitUntil: 'networkidle0'` を使用
2. **高DPI対応**: `deviceScaleFactor: 2` でRetina相当の高解像度出力も可能
3. **背景透過**: 必要に応じて背景を透過PNGにできる
4. **クリッピング**: 指定サイズぴったりで切り出し

## テンプレートの管理と再利用

### テンプレートの保存

完成したHTMLテンプレートは以下の構造で保存:

```
templates/
├── sub_image/           # サブ画像用テンプレート
│   ├── hero_text_side.html
│   ├── grid_comparison.html
│   ├── numbered_list.html
│   ├── endorsement.html
│   ├── spec_diagram.html
│   └── feature_callout.html
└── aplus/               # A+モジュール用テンプレート
    ├── standard_image_text.html
    ├── comparison_table.html
    └── four_images_text.html
```

### テンプレートのカスタマイズ

新商品に適用する際:
1. テンプレートをコピー
2. テキスト・画像パスを差し替え
3. カラーパレットを調整
4. レンダリング

テンプレートの構造（HTML構造・CSS Grid/Flexbox設定）はそのまま使えることが多いため、テキストと素材の差し替えだけで80%は完成する。
