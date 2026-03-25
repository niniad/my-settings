---
name: slide-builder
description: ビジネスプレゼンテーション資料を4フェーズ（ヒアリング→構成設計→デザイン割当→HTML作成）で段階的に作成するスキル。26種のスライドパターンライブラリとフローチャートによる決定論的パターン選択。HTML/PDF/PPTX出力対応。トリガー：「プレゼン作って」「スライド作成」「資料を作りたい」「slide-builder」
---

# Slide Builder

ビジネスプレゼンテーション資料を段階的に作成するスキル。26種のスライドパターンライブラリと決定論的なパターン選定ロジックにより、デザイン品質を担保しながら内容に集中できる。

## 出力仕様

| 項目 | 仕様 |
|------|------|
| スライドサイズ | 960px × 540px（16:9） |
| CSS | インラインCSS（外部依存なし） |
| フォント | Arial, Helvetica, sans-serif（システムフォント） |
| 出力形式 | HTML（デフォルト）/ PDF / PPTX |
| 出力先 | `tmp/presentation.html`（プロジェクトの tmp/ ）|

---

## デザインシステム定数

### Theme A: Clean Light（ビジネス・社内資料向け）

```
背景:         #FFFFFF
アクセント:    #0055CC（青）
見出し色:     #111111
本文色:       #333333
カード背景:    #F5F5F5
ボーダー:     #EEEEEE
サブテキスト:  #888888
上部バー:     4px solid #0055CC
ページ番号:   11px, #CCCCCC, 右下40px
内容エリア:   left: 60px, top: 50px, width: 840px
```

### Theme B: B&W Swiss（タイポグラフィ重視・ミニマル）

```
背景:         #FFFFFF（コンテンツ）/ #000000（左バンド）
アクセント:   なし（白黒のみ）
見出し色:     #000000, uppercase, letter-spacing: -1.5px
本文色:       #000000 / #555555
サブテキスト: #666666
左バンド:     50px, #000000, 縦書き白ラベル
内容エリア:   left: 80px
```

### テーマ選定ロジック

```
ユーザー指定あり → 指定テーマ
ユーザー指定なし:
  ビジネス・社内資料・データ重視 → Clean Light
  シンプル・タイポグラフィ重視・コンセプト系 → B&W Swiss
  判断できない → Clean Light（デフォルト）
```

---

## フェーズ1: コンテキスト収集

以下をユーザーにヒアリングする。まとめて聞いて構わない。

**必須項目:**
- **対象者**: 誰に向けて？（社内/社外、上司/顧客/投資家等）
- **関係性**: 発表者と聴衆の関係（初対面/継続取引/社内報告等）
- **目的**: この資料で何を達成したいか？（意思決定/情報共有/提案/説明等）
- **主張**: 1文で言うと何を伝えたいか？
- **発表時間**: 何分？（目安: 1分/スライド）
- **形式**: 口頭発表 / 配布資料 / 両方？
- **言語**: 日本語 / 英語 / 他？

**任意項目:**
- 既存素材（資料、データ、画像等）
- テーマ指定（Clean Light / B&W Swiss）
- 特別なデザイン制約

→ **収集後、サマリーをユーザーに提示し承認を得る。承認後フェーズ2へ。**

---

## フェーズ2: コンテンツ構成設計

フェーズ1の情報を基に、スライド構成を設計する。

**設計原則:**
- 論理的フロー: 導入（なぜ重要か）→ 本論（何をどうするか）→ 結論（次のアクション）
- 1スライド1メッセージ
- 発表時間に合わせたスライド枚数（口頭: 1分/枚 目安）
- 情報量の適正化: スライドに詰め込みすぎない

**成果物: スライド構成表をMarkdown表で提示**

| # | タイトル | 内容概要 | 想定情報量 |
|---|--------|---------|---------|
| 1 | 表紙 | 資料名、発表者、日付 | 最小 |
| 2 | アジェンダ | 3〜5項目 | 小 |
| ... | ... | ... | ... |

→ **構成表をユーザーに提示し承認を得る。承認後フェーズ3aへ。**

---

## フェーズ3a: デザインパターン割当

`patterns/index.md` のフローチャートを参照し、各スライドにパターンを割り振る。

**手順:**
1. `C:/Users/ninni/.claude/skills/slide-builder/patterns/index.md` を読み込む
2. フローチャートに従い各スライドのパターンを決定
3. マッピング表を提示

**マッピング表:**

| # | タイトル | パターン | 理由 |
|---|--------|---------|------|
| 1 | 表紙 | title-cover | Q1: 表紙 |
| 2 | アジェンダ | agenda | Q1: 目次 |
| ... | ... | ... | ... |

→ **マッピング表をユーザーに提示し承認を得る。承認後フェーズ3bへ。**

---

## フェーズ3b: HTMLスライド作成

1. **テーマ決定**: フェーズ1の情報に基づきテーマを選定
2. **パターンHTML読込**: 各スライドについて対応するHTMLを読み込む
   - パス: `C:/Users/ninni/.claude/skills/slide-builder/patterns/{theme}/{category}/{pattern}.html`
   - theme: `clean-light` または `bw-swiss`
3. **コンテンツ差替**: プレースホルダーを実コンテンツに置き換え
4. **テキスト量調整**: 各パターン冒頭のコメントに記載されたガイドラインに従う
5. **全スライド統合**: 下記のナビエンジンHTML骨格に全スライドを組み込む
6. **出力**: `tmp/presentation.html` に保存

→ **完成したHTMLのパスをユーザーに提示し承認を得る。**

---

## フェーズ4: QAチェック＋改善

以下の観点で生成したHTMLをチェックし、問題があれば自動修正する。

| チェック項目 | 確認内容 |
|-----------|--------|
| レイアウト | overflow（テキストがはみ出ていないか）|
| 余白 | 適切な空間確保（窮屈でないか）|
| 一貫性 | フォントサイズ・色・間隔が統一されているか |
| 内容 | 論理的矛盾・誤字・表記ゆれ |

- 問題があれば自動修正して最終版を提示
- 修正要望があれば → Phase 3b または Phase 4 内で対応

---

## ナビゲーションエンジン（HTML骨格）

フェーズ3bで全スライドを統合する際、以下のHTML骨格を使用する:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>プレゼンテーションタイトル</title>
<style>
/* ==================== NAVIGATION ENGINE ==================== */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  width: 100%; height: 100%;
  overflow: hidden;
  background: #1a1a1a;
  font-family: Arial, Helvetica, sans-serif;
}

.stage {
  width: 100vw; height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.scaler {
  width: 960px; height: 540px;
  position: relative;
  transform-origin: center center;
}

section {
  position: absolute;
  top: 0; left: 0;
  width: 960px; height: 540px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}

section.active {
  opacity: 1;
  pointer-events: auto;
}

.nav-hint {
  position: fixed;
  bottom: 14px; right: 18px;
  font-size: 11px;
  color: rgba(255,255,255,0.25);
  z-index: 999;
  font-family: monospace;
  pointer-events: none;
}

.progress {
  position: fixed;
  bottom: 0; left: 0;
  height: 3px;
  background: rgba(255,255,255,0.35);
  transition: width 0.3s ease;
  z-index: 999;
}

/* ==================== SLIDE STYLES ==================== */
/* 各スライドのスタイルをここに追加。クラス名を slide-N-xxx 形式で一意にする */

</style>
</head>
<body>

<div class="stage">
  <div class="scaler" id="scaler">

    <section class="active" id="slide-1">
      <!-- スライド1のコンテンツ -->
    </section>

    <section id="slide-2">
      <!-- スライド2のコンテンツ -->
    </section>

    <!-- 以降のスライドを追加 -->

  </div>
</div>

<div class="progress" id="progress"></div>
<div class="nav-hint">← → Space</div>

<script>
(function() {
  const scaler = document.getElementById('scaler');
  const sections = Array.from(document.querySelectorAll('section'));
  const progress = document.getElementById('progress');
  let current = 0;

  function resize() {
    const sx = window.innerWidth  / 960;
    const sy = window.innerHeight / 540;
    scaler.style.transform = 'scale(' + Math.min(sx, sy) + ')';
  }
  window.addEventListener('resize', resize);
  resize();

  function go(n) {
    sections[current].classList.remove('active');
    current = Math.max(0, Math.min(n, sections.length - 1));
    sections[current].classList.add('active');
    progress.style.width = ((current + 1) / sections.length * 100) + '%';
    location.hash = current + 1;
  }

  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') { e.preventDefault(); go(current + 1); }
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')                    { e.preventDefault(); go(current - 1); }
    if (e.key === 'Home') go(0);
    if (e.key === 'End')  go(sections.length - 1);
  });

  let tx = 0;
  document.addEventListener('touchstart', e => { tx = e.touches[0].clientX; });
  document.addEventListener('touchend',   e => {
    const dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 60) go(dx < 0 ? current + 1 : current - 1);
  });

  const h = parseInt(location.hash.slice(1));
  if (h >= 1 && h <= sections.length) go(h - 1);
  progress.style.width = (1 / sections.length * 100) + '%';
})();
</script>
</body>
</html>
```

**IMPORTANT**: 複数スライドのCSSを統合する際はクラス名が衝突しないようにスライド番号をプレフィックスに付ける（例: `.s1-title`, `.s2-bullets`）。または各スライドをインラインスタイルで記述する。

---

## PDF変換パイプライン

各スライドを個別HTMLとして `tmp/slides/` に保存し、Playwright でPDF化する。

```javascript
// tmp/export-pdf.js
'use strict';
const { chromium } = require('C:/Users/ninni/.claude/skills/pptx/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const slideDir = 'C:/Users/ninni/projects/[project]/tmp/slides';
const outDir  = slideDir;

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const files = fs.readdirSync(slideDir)
    .filter(f => f.endsWith('.html'))
    .sort()
    .map(f => path.join(slideDir, f).split('\\').join('/'));
  const page = await context.newPage();

  for (let i = 0; i < files.length; i++) {
    await page.goto('file:///' + files[i]);
    await page.waitForLoadState('networkidle');
    const pdf = await page.pdf({ width: '1280px', height: '720px', printBackground: true });
    fs.writeFileSync(path.join(outDir, `slide${i+1}-tmp.pdf`), pdf);
  }
  await browser.close();
  console.log('done');
})();
```

```python
# uv run --with pypdf python tmp/merge-pdf.py
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pypdf import PdfWriter
import glob, os

writer = PdfWriter()
for f in sorted(glob.glob('tmp/slides/slide*-tmp.pdf')):
    writer.append(f)
with open('tmp/presentation.pdf', 'wb') as out:
    writer.write(out)
for f in sorted(glob.glob('tmp/slides/slide*-tmp.pdf')):
    os.remove(f)
print('saved: tmp/presentation.pdf')
```

## PPTX変換

`/pptx` スキルの "Creating a new PowerPoint presentation without a template" セクションに従って実行。

```javascript
const SKILL_DIR = 'C:/Users/ninni/.claude/skills/pptx';
const pptxgen = require(`${SKILL_DIR}/node_modules/pptxgenjs`);
const html2pptx = require(`${SKILL_DIR}/scripts/html2pptx.js`);
```
