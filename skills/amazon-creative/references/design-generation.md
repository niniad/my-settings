# ワイヤーフレーム作成（HTML/CSS）

## 基本原則

ワイヤーフレームは**白黒の構図設計図**。確定するのは配置・サイズ・レイヤーのみ。

- 色は使わない（白・黒・グレーのみ）
- 装飾は入れない（角丸・影・ボーダー不要）
- カード型コンテナは使わない（テキストと写真を分断するボックス禁止）

### 配置方法の使い分け

| 用途 | 方法 | 理由 |
|------|------|------|
| メインセクションの配置（見出し・写真エリア・フッター） | `position: absolute` | 自由なレイヤード構図 |
| セクション内の繰り返し要素（カラム列・リスト・グリッド） | `CSS Grid` or `Flexbox` + `gap` | 間隔の均等化・列揃えの保証 |

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
    width: 2000px;
    height: 2000px;
    font-family: 'Noto Sans JP', sans-serif;
    overflow: hidden;
    position: relative;
    background: #FFF;
  }

  /* --- テキスト階層（スマホ1/4縮小を前提） --- */
  /* hero: スマホで30-40px相当 → 一番伝えたいキーワード */
  .hero { font-size: 140px; font-weight: 900; line-height: 1.15; color: #000; }
  /* heading: スマホで18-22px相当 → 見出し */
  .heading { font-size: 80px; font-weight: 900; line-height: 1.25; color: #000; }
  /* sub: スマホで12-15px相当 → サブテキスト */
  .sub { font-size: 52px; font-weight: 700; line-height: 1.4; color: #333; }
  /* body: スマホで10-12px相当 → 説明文 */
  .body { font-size: 44px; font-weight: 500; line-height: 1.5; color: #333; }
  /* caption: スマホで8-9px相当 → 注釈・最小テキスト */
  .caption { font-size: 36px; font-weight: 400; line-height: 1.4; color: #666; }

  /* テキスト内の強調（キーワードを大きく/太く） */
  .em { font-weight: 900; font-size: 1.4em; }

  /* 写真プレースホルダー */
  .photo {
    background: #DDD;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #999;
    font-size: 28px;
    text-align: center;
    line-height: 1.5;
  }

  /* バッジ（浮き要素） */
  .badge {
    background: #333;
    color: #FFF;
    padding: 12px 32px;
    font-size: 40px;
    font-weight: 700;
  }

  /* アイコン */
  .icon-ng { color: #000; font-size: 56px; font-weight: 900; }
  .icon-ok { color: #000; font-size: 56px; font-weight: 900; }
</style>
</head>
<body>
  <!-- position: absolute で各要素を配置 -->
</body>
</html>
```

### フォントサイズ早見表

2000pxキャンバス → スマホ表示で約1/4に縮小される前提。

| クラス | サイズ | スマホ換算 | 用途 | 使いどころ |
|--------|--------|-----------|------|-----------|
| `.hero` | 140px | 35px | 最重要キーワード | 1画像に1-2語のみ |
| `.heading` | 80px | 20px | 見出し | セクションタイトル |
| `.sub` | 52px | 13px | サブテキスト | 補足見出し・ポイント名 |
| `.body` | 44px | 11px | 説明文 | 特徴の詳細説明 |
| `.caption` | 36px | 9px | 注釈（最小） | 出典・注意書き |

**最小フォントサイズ: 36px**（これ以下はスマホで読めない）。
**`.em` クラス**: テキスト内のキーワードを1.4倍に拡大。例: `<span class="em">3大</span>お悩み`

---

## フォント

システムにインストール済みのフォントを使用する。Google Fonts CDNは不要。

| フォント | font-family | 用途 |
|---------|------------|------|
| Noto Sans JP | `'Noto Sans JP'` | メインフォント |
| Noto Serif JP | `'Noto Serif JP'` | フォーマル・高級感 |
| Shin Retro Maru Gothic | `'Shin Retro Maru Gothic'` | やわらかい・レトロ |

---

## 写真プレースホルダー

ワイヤーフレームでは写真エリアを `.photo` クラスのグレー矩形で表示する。
**ボーダーや枠線は付けない**（グレー背景だけで写真エリアだと分かる）。

```html
<!-- 写真は position:absolute で配置。キャンバスの60%以上を占めること。 -->
<div class="photo" style="position:absolute; left:0; top:0; width:1100px; height:2000px;">
  赤ちゃんが笑顔で<br>エプロンを着けている写真
</div>
```

プレースホルダー内のテキストは撮影指示メモとして残す。

---

## 構図のコツ

1. **写真を先に置く**: まず写真プレースホルダーを大きく配置。残りのスペースにテキストを配置。
2. **テキストは写真に寄せる**: テキストと写真の間に「空白の壁」を作らない。隣接か重なりで配置。
3. **キーワードを巨大にする**: 1画像で最も伝えたい1-2語は `.hero`（140px）で。残りは `.heading` 以下。
4. **端まで使う**: パディングは最小限（40-80px程度）。写真は端まで。

---

## レイアウト品質ルール

HTMLを書く前・書いた後に必ず確認する。

### 1. グリッドシステム（固定マージン）

すべての要素は共通マージン内に収める。

| キャンバス | 左右マージン | コンテンツ幅 | 上下マージン |
|-----------|------------|------------|------------|
| 2000×2000px | 60px | 1880px | 最小 40px |
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

例: 970pxキャンバスに4つの220px要素を並べる場合
```
(220 × 4) + (gap × 3) ≤ 890
880 + gap × 3 ≤ 890
gap ≤ 3.3px ← 収まらない → 要素幅を210pxに縮小、gap=10pxに
```

**計算が合わない場合は要素幅またはgapを調整する。見切れたまま出力しない。**

### 3. 繰り返し要素の間隔統一

同じ種類の要素（リスト項目・カラム・グリッドセル）は**CSS Grid/Flexbox + gap で間隔を指定**する。

```html
<!-- NG: absoluteで個別配置 → 間隔がバラつく -->
<div style="position:absolute; top:400px;">項目1</div>
<div style="position:absolute; top:640px;">項目2</div>
<div style="position:absolute; top:860px;">項目3</div>

<!-- OK: Flexbox + gap → 間隔が自動で均等 -->
<div style="position:absolute; top:400px; display:flex; flex-direction:column; gap:40px;">
  <div>項目1</div>
  <div>項目2</div>
  <div>項目3</div>
</div>
```

### 4. テキスト折り返し制御

| テキスト種類 | 対処法 |
|------------|--------|
| キャッチコピー・スローガン（1行に収めたい短文） | `white-space: nowrap` を指定。または明示的に `<br>` で改行位置を制御 |
| 複数行の説明文 | コンテナ幅内に収まることを確認（日本語1文字 ≈ font-size の幅） |

```html
<!-- NG: コンテナ幅が足りず意図しない位置で改行 -->
<div style="width:400px; font-size:44px;">やっと見つけた。</div>
<!-- 「やっと見つけ」+改行+「た。」になる可能性 -->

<!-- OK: nowrapで1行を保証 -->
<div style="font-size:44px; white-space:nowrap;">やっと見つけた。</div>

<!-- OK: 明示的に改行位置を指定 -->
<div style="font-size:44px;">やっと見つけた。<br>嫌がらないエプロン。</div>
```

**目安: 日本語テキストの1行幅 ≈ 文字数 × font-size**
- 例: 8文字 × 44px = 352px → コンテナ幅が352px以上必要

### 5. 垂直方向の充填（余白の最小化）

コンテンツはキャンバス高さの**90%以上**を占めること。

- フッターがある場合は `bottom: 0` に固定
- 下部に空白が生じた場合: 写真の高さを拡大する / 要素間余白を均等に再分配する / フッターを大きくする
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
# PNG出力
python scripts/render_html.py input.html output.png --width 2000 --height 2000

# PDF出力（Affinity Designerでテキスト編集可能）
python scripts/render_html.py input.html output.pdf --width 2000 --height 2000
```
