# ワイヤーフレーム作成（HTML/CSS）

## 基本原則

ワイヤーフレームは**白黒の構図設計図**。確定するのは配置・サイズ・レイヤーのみ。

- 色は使わない（白・黒・グレーのみ）
- 装飾は入れない（角丸・影・ボーダー不要）
- カード型コンテナは使わない（テキストと写真を分断するボックス禁止）

### 配置方法の使い分け

| 用途 | 方法 | 理由 |
|------|------|------|
| ページ全体の縦方向配分 | `Flex column` + `justify-content: space-between` | キャンバス高さ全体にコンテンツを均等配分 |
| セクション内の繰り返し要素（カラム列・リスト・グリッド） | `CSS Grid` or `Flexbox` + `gap` | 間隔の均等化・列揃えの保証 |
| 重ねて配置する要素（バッジ・吹き出し・寸法ラベル） | `position: absolute` | 写真の上にテキストを重ねる等 |

**ページ全体のレイアウトに `position: absolute` + 固定 `top` 値を使わない。** 縦2000pxのキャンバスに対して手動で `top` を計算すると、コンテンツが上半分に偏り下部に大きな空白が生じる。代わりにFlexラッパーで自動配分する。

**繰り返し要素を `position: absolute` で個別配置してはいけない**（位置ズレ・間隔不均等の原因）。

---

## HTMLベーステンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: 1600px;
    height: 2000px;
    font-family: 'Shin Retro Maru Gothic', 'Noto Sans JP', sans-serif;
    overflow: hidden;
    position: relative;
    background: #FFF;
  }
  /* ※キャンバスサイズはPhase 2開始前にユーザー確認済みの値を使用 */

  /* --- テキスト階層（スマホ1/4縮小を前提） --- */
  /* hero: スマホで30px相当 → 一番伝えたいキーワード */
  .hero { font-size: 120px; font-weight: 900; line-height: 1.15; color: #000; }
  /* heading: スマホで18px相当 → 見出し */
  .heading { font-size: 72px; font-weight: 900; line-height: 1.25; color: #000; }
  /* sub: スマホで12px相当 → サブテキスト */
  .sub { font-size: 48px; font-weight: 700; line-height: 1.4; color: #333; }
  /* body: スマホで10px相当 → 説明文 */
  .body { font-size: 40px; font-weight: 500; line-height: 1.5; color: #333; }
  /* caption: スマホで8px相当 → 注釈・最小テキスト */
  .caption { font-size: 32px; font-weight: 400; line-height: 1.4; color: #666; }

  /* テキスト内の強調（キーワードを大きく/太く） */
  .em { font-weight: 900; font-size: 1.4em; }

  /* 写真プレースホルダー（最小限のラベルのみ記載） */
  .photo {
    background: #DDD;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 24px;
    text-align: center;
    line-height: 1.5;
  }

  /* バッジ（浮き要素） */
  .badge {
    background: #333;
    color: #FFF;
    padding: 12px 32px;
    font-size: 36px;
    font-weight: 700;
  }

  /* アイコン */
  .icon-ng { color: #000; font-size: 48px; font-weight: 900; }
  .icon-ok { color: #000; font-size: 48px; font-weight: 900; }
</style>
</head>
<body>
  <!--
    ページ全体のレイアウト:
    Flexラッパーでキャンバス高さ全体にコンテンツを均等配分する。
    position:absolute は写真の上にバッジを重ねる等、限定的に使う。
  -->

  <!-- パターンA: テキストのみ or テキスト+写真が上下に並ぶ構図 -->
  <div style="position:absolute; top:0; left:48px; width:1504px; height:2000px;
              display:flex; flex-direction:column; justify-content:space-between;
              padding:60px 0;">
    <div><!-- 見出し --></div>
    <div><!-- メインコンテンツ（写真+テキスト） --></div>
    <div><!-- フッター --></div>
  </div>

  <!-- パターンB: 左写真+右テキストの構図 -->
  <!--
  <div class="photo" style="position:absolute; left:0; top:0; width:880px; height:2000px;">写真</div>
  <div style="position:absolute; left:920px; top:0; width:632px; height:2000px;
              display:flex; flex-direction:column; justify-content:space-between;
              padding:80px 0 60px;">
    <div>見出し</div>
    <div>特徴リスト</div>
    <div>フッター</div>
  </div>
  -->
</body>
</html>
```

### フォントサイズ早見表

1600pxキャンバス → スマホ表示で約1/4に縮小される前提。

| クラス | サイズ | スマホ換算 | 用途 | 使いどころ |
|--------|--------|-----------|------|-----------|
| `.hero` | 120px | 30px | 最重要キーワード | 1画像に1-2語のみ |
| `.heading` | 72px | 18px | 見出し | セクションタイトル |
| `.sub` | 48px | 12px | サブテキスト | 補足見出し・ポイント名 |
| `.body` | 40px | 10px | 説明文 | 特徴の詳細説明 |
| `.caption` | 32px | 8px | 注釈（最小） | 出典・注意書き |

**最小フォントサイズ: 32px**（これ以下はスマホで読めない）。
**`.em` クラス**: テキスト内のキーワードを1.4倍に拡大。例: `<span class="em">3大</span>お悩み`

---

## フォント

システムにインストール済みのフォントを使用する。Google Fonts CDNは不要。

| フォント | font-family | 用途 |
|---------|------------|------|
| Shin Retro Maru Gothic | `'Shin Retro Maru Gothic'` | **ベビー・キッズ用品のデフォルト**。やわらかい・親しみ |
| Noto Sans JP | `'Noto Sans JP'` | 汎用メインフォント。クリーン・モダン |
| Noto Serif JP | `'Noto Serif JP'` | フォーマル・高級感が必要な場合に明示的に指定 |

---

## 写真プレースホルダー

ワイヤーフレームでは写真エリアを `.photo` クラスのグレー矩形で表示する。
**ボーダーや枠線は付けない**（グレー背景だけで写真エリアだと分かる）。

```html
<!-- 写真は position:absolute で配置。キャンバスの60%以上を占めること。 -->
<!-- プレースホルダーには最小限のラベルのみ記載（AI画像生成で上書きする可能性があるため） -->
<div class="photo" style="position:absolute; left:0; top:0; width:880px; height:2000px;">
  商品着用写真
</div>
```

**詳細な写真プロンプト（被写体・構図・雰囲気・背景・調達方法）は訴求マップに記載する。**
ワイヤーフレームの `.photo` 内には「商品着用写真」「素材クローズアップ」等の短いラベルのみ。

---

## 構図のコツ

1. **Flexラッパーで全体を包む**: まず `display:flex; flex-direction:column; justify-content:space-between` のラッパーを作り、その中に見出し・コンテンツ・フッターを配置。キャンバス高さ全体にコンテンツが自動配分される。
2. **写真を先に置く**: 写真プレースホルダーを大きく配置。残りのスペースにテキストを配置。
3. **テキストは写真に寄せる**: テキストと写真の間に「空白の壁」を作らない。隣接か重なりで配置。
4. **キーワードを巨大にする**: 1画像で最も伝えたい1-2語は `.hero`（120px）で。残りは `.heading` 以下。
5. **端まで使う**: パディングは最小限（40-60px程度）。写真は端まで。

---

## デザイントーン: 高級感 × 安心感の両立

ベビー・マタニティ用品は「安心感」が必須だが、Amazon上で多くの競合が「安っぽい」ビジュアルに陥っている。以下の原則で差別化する。

### やるべきこと

1. **余白は品質の証**
   - テキストを詰め込まない。1画像1メッセージが理想
   - 余白が多いほど「自信がある商品」に見える
   - 写真とテキストの間にも呼吸空間を取る

2. **色数の制限**（ワイヤーフレームでは白黒だが、後工程のための設計指針）
   - 1画像あたり2〜3色まで（白・グレー除く）
   - 彩度を抑えたニュアンスカラーを使う
   - 原色パステル（ビビッドピンク・スカイブルー・レモンイエロー）は避ける

   **カテゴリ別推奨カラー方向性:**

   | カテゴリ | ベース | アクセント | 避けるべき色 |
   |---------|--------|-----------|------------|
   | ベビー・マタニティ | 暖色系オフホワイト、クリーム | セージグリーン、ダスティローズ、サンドベージュ | ビビッドピンク、原色ブルー |
   | ヘアケア・美容 | ダークトーン、チャコール | ゴールド、モーヴ、ディープグリーン | 蛍光色、原色 |
   | 食品・サプリ | ナチュラルホワイト、アイボリー | アースグリーン、テラコッタ | 人工的な彩度の高い色 |
   | テック・ガジェット | ピュアホワイト、ライトグレー | ネイビー、チャコール、アクセントブルー | パステル |

   **具体的なカラーパレットは訴求マップに定義する。**

3. **タイポグラフィの規律**
   - 1画像で使うフォントウェイトは2種まで（900 + 500 など）
   - heroテキストは思い切り大きく、残りは控えめに。中途半端なサイズを作らない
   - 丸ゴシック（Shin Retro Maru Gothic）で柔らかさを出しつつ、太字ウェイトでしっかり感を両立

4. **写真のクオリティ基準**
   - ライフスタイル写真: 自然光・ニュートラルトーン・生活感のある背景
   - 商品写真: 清潔な白背景・影あり・質感が伝わるクローズアップ
   - 「Amazonでよく見る」過度に明るい・彩度高い写真は避ける

5. **信頼シグナルのエレガントな表現**
   - 「保育士監修」は小さなバッジで控えめに（大きな★マーク＋数字は避ける）
   - データ（アンケート結果等）は数字を大きく、出典を小さく
   - 根拠の提示は必要だが、「売り込み感」を出さない

### やってはいけないこと（Amazon商品画像の典型的な安っぽさ）

- グラデーション背景
- テキストにドロップシャドウ
- 星型・爆発型の装飾（スターバースト）
- 「！！！」の多用
- 赤・黄色のセール風カラーリング
- クリップアート風アイコン
- テキストに蛍光色のハイライト/マーカー
- 1画像に3つ以上の訴求を詰め込む

---

## レイアウト品質ルール

HTMLを書く前・書いた後に必ず確認する。

### 1. グリッドシステム（固定マージン）

すべての要素は共通マージン内に収める。

| キャンバス | 左右マージン | コンテンツ幅 | 上下マージン |
|-----------|------------|------------|------------|
| 1600×2000px | 48px | 1504px | 最小 40px |
| 970×600px | 40px | 890px | 最小 20px |

```
コンテンツ左端: left: {マージン}px
コンテンツ右端: left + width ≤ キャンバス幅 - マージン
```

**横に並ぶ全セクション（見出し・写真列・比較表・フッター内要素）の左端と右端はこのマージンに揃える。**

### 2. 横幅の事前計算（見切れ防止）

要素を横に並べるときは、配置前に合計幅を計算する。

```
必要幅 = (要素幅 × 個数) + (gap × (個数 - 1))
必要幅 ≤ コンテンツ幅（= キャンバス幅 - 左右マージン × 2）
```

**計算が合わない場合は要素幅またはgapを調整する。見切れたまま出力しない。**

### 3. 繰り返し要素の間隔統一

同じ種類の要素（リスト項目・カラム・グリッドセル）は**CSS Grid/Flexbox + gap で間隔を指定**する。

```html
<!-- NG: absoluteで個別配置 → 間隔がバラつく -->
<div style="position:absolute; top:400px;">項目1</div>
<div style="position:absolute; top:640px;">項目2</div>

<!-- OK: Flexbox + gap → 間隔が自動で均等 -->
<div style="position:absolute; top:400px; display:flex; flex-direction:column; gap:40px;">
  <div>項目1</div>
  <div>項目2</div>
</div>
```

### 4. テキスト折り返し制御

| テキスト種類 | 対処法 |
|------------|--------|
| キャッチコピー・スローガン（1行に収めたい短文） | `white-space: nowrap` を指定。または明示的に `<br>` で改行位置を制御 |
| 複数行の説明文 | コンテナ幅内に収まることを確認（日本語1文字 ≈ font-size の幅） |

**目安: 日本語テキストの1行幅 ≈ 文字数 × font-size**
- 例: 8文字 × 40px = 320px → コンテナ幅が320px以上必要

### 5. 垂直方向の充填（余白の最小化）

コンテンツはキャンバス高さの**90%以上**を占めること。

**解決方法: Flexラッパーで自動配分する。**

```html
<!-- ページ全体を flex column で包み、space-between で均等配分 -->
<div style="position:absolute; top:0; left:48px; width:1504px; height:2000px;
            display:flex; flex-direction:column; justify-content:space-between;
            padding:60px 0;">
  <div><!-- 見出しブロック --></div>
  <div><!-- メインコンテンツ --></div>
  <div><!-- フッター --></div>
</div>
```

- `justify-content: space-between` でブロック間の余白が自動的に均等になる
- `position: absolute` + 固定 `top` 値でセクションを配置すると、手動計算のミスで下部に大きな空白が生じる → **禁止**
- 写真を大きくする / 要素間余白を増やす等の微調整は flex 内で行う
- **「配置が上半分に偏って下半分が空白」は禁止**

### 6. カラムの垂直整列

写真の上にテキスト見出し、写真の下に説明テキストを置く場合、**CSS Grid で列構造を定義**する。

```html
<!-- OK: CSS Gridでカラムを定義 → 写真とテキストが自動で揃う -->
<div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:20px; width:890px;">
  <div style="text-align:center;">
    <div class="photo" style="width:100%; aspect-ratio:1;">写真1</div>
    <div style="font-size:22px; font-weight:900; margin-top:12px;">タイトル1</div>
  </div>
  <!-- 残り3つも同じ構造 -->
</div>
```

**各カラムの幅は `1fr`（均等分割）を使い、個別に幅を指定しない。**

---

## レンダリング（任意）

ワイヤーフレームはブラウザで直接プレビュー可能。PNG/PDF出力が必要な場合:

```bash
# PNG出力（サブ画像）
python scripts/render_html.py input.html output.png --width 1600 --height 2000

# PDF出力（Affinity Designerでテキスト編集可能）
python scripts/render_html.py input.html output.pdf --width 1600 --height 2000

# A+（970×600 固定）
python scripts/render_html.py input.html output.pdf --width 970 --height 600
```
