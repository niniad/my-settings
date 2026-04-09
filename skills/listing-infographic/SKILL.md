# listing-infographic スキル

HTML/CSS で商品画像デザインを制作し、PNG として出力するスキル。
**Phase 2**（デザイン制作）と **Phase 4**（写真挿入・最終PNG出力）の2回呼び出される。

---

## Phase 2: デザイン制作

### 前提

- `/listing-appeal-map` が完了し、`ec/products/{slug}/appeal-map.md` が承認済みであること

### 手順

1. `appeal-map.md` の各Sub・A+ 仕様を読み込む
2. テンプレート（`ec/listings/templates/`）を起点に HTML/CSS を作成
3. 写真エリアは仮プレースホルダー（背景色 or テキスト）で埋める
4. ブラウザ確認 → フィードバック → 修正ループ
5. 承認後、Phase 3（写真生成）へ

出力先: `ec/products/{slug}/html/sub_XX.html` など

### HTML/CSS ルール

**キャンバスサイズ**

| タイプ | サイズ | 用途 |
|--------|--------|------|
| メイン画像 | 2000×2500px (4:5) | メイン商品画像 |
| サブ画像 | 2000×2000px (1:1) | サブ画像デフォルト |
| A+標準 | 970×600px | A+ 標準画像＋テキスト |

**テキスト階層**（スマホ1/4縮小前提）

| クラス | サイズ | スマホ換算 | 用途 |
|--------|--------|-----------|------|
| `.hero` | 120px | 30px | 最重要キーワード |
| `.heading` | 72px | 18px | 見出し |
| `.sub` | 48px | 12px | サブテキスト |
| `.body` | 40px | 10px | 説明文 |
| `.caption` | 32px | 8px | 注釈・最小テキスト |

最小フォントサイズ: **32px**（これ以下はスマホで読めない）

**レイアウト原則**
- 写真がキャンバスの60%以上を占める
- Flex ラッパー: `display:flex; flex-direction:column; justify-content:space-between`
- グリッドマージン: 左右48px（2000px幅）
- 禁止: `position:absolute` で全体構造配置、下部大空白、グラデーション背景

**ブランドカラー（Ufa）**

| 用途 | Hex |
|------|-----|
| 背景ベース（暖色系オフホワイト） | #FBF8F3 |
| テキスト（ダークチャコール） | #2D2A26 |
| アクセント（ゴールド） | #B08D57 |
| サブテキスト（ウォームグレー） | #6B635A |

**フォント**
- `ec/listings/brand/fonts/SHOWG.ttf` — ベビー・キッズ用品デフォルト
- `ec/listings/brand/fonts/NOTO SANS JP-*.ttf` — 汎用・モダン

### Phase 2 完了後・次工程

HTML（プレースホルダー入り）をユーザーが確認・承認したら:

**次工程 → `/listing-photo-gen`（Phase 3: 写真生成）**

---

## Phase 4: PNG レンダリング

### 前提

- `/listing-photo-gen` が完了し、HTML に実写真（Eagle からの画像 or AI生成画像）が挿入済みであること

### コマンド

```bash
cd C:/Users/ninni/projects/ec/listings

# サブ画像 PNG (2000×2000)
uv run python scripts/render_html.py \
  ../../products/{slug}/html/sub_02.html \
  ../../products/{slug}/current/sub_02.png \
  --width 2000 --height 2000

# メイン画像 PNG (2000×2500)
uv run python scripts/render_html.py \
  ../../products/{slug}/html/main.html \
  ../../products/{slug}/current/main.png \
  --width 2000 --height 2500

# A+ PNG (970×600)
uv run python scripts/render_html.py \
  ../../products/{slug}/html/aplus_01.html \
  ../../products/{slug}/current/aplus_01.png \
  --width 970 --height 600
```

### 出品可能レベルの判定基準

1. テキストが全てスマホ（1/4スケール）で読める
2. 商品写真のディテールが正確（形状・サイズ比・素材感）
3. ブランドカラーが統一されている
4. 競合 BSR Top 10 と並べて見劣りしない
5. AI感がない（写真が自然）
6. Amazon規約に準拠

### Amazon規約: 禁止表現

| NG表現 | 理由 |
|--------|------|
| 最高、最強、No.1 | 主観的・証明不可 |
| 激安、最安値 | 価格変動するため |
| 送料無料 | Amazon配送条件次第 |
| 他社ブランド名 | 商標権侵害 |
| 治る、痩せる | 薬機法・景品表示法違反 |
| 永久保証 | 消費者契約法上の問題 |
| 価格表示（¥xxx） | 価格変動時に画像更新が必要 |

### Phase 4 完了後・次工程

PNG が出品可能レベルに達したら Amazon セラーセントラルへアップロード。

**次工程 → 出品（セラーセントラル）。以降は `/ec-analytics` で効果測定。**

---

## 参照ファイル

- `ec/listings/brand/design-system.md` — カラー・タイポグラフィ詳細
- `ec/listings/templates/` — ベーステンプレート群
- `ec/products/{slug}/appeal-map.md` — 各画像の仕様
