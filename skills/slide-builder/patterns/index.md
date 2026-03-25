# Slide Builder パターンカタログ

26種のスライドパターンと選定フローチャート。
フェーズ3aでこのフローチャートを使い、各スライドにパターンを割り当てる。

---

## パターン選定フローチャート

```
Q1: スライドの役割は？
├─ 表紙・タイトル              → title-cover
├─ 目次・アジェンダ            → agenda
├─ セクション区切り            → section-divider
├─ キーメッセージ（1文強調）    → key-message
├─ まとめ・総括               → summary
├─ CTA・次のステップ           → cta-closing
├─ 終了・Q&A                  → thankyou-qa
└─ コンテンツスライド          → Q2へ

Q2: コンテンツの主な種類は？
├─ テキスト中心               → Q3へ
├─ 数値・データ               → Q4へ
├─ 比較                      → Q5へ
├─ プロセス・手順              → Q6へ
├─ 構造・関係性               → Q7へ
└─ 引用・証言・コメント        → quote

Q3: テキストの構成は？
├─ 箇条書き（順序なし）        → bullets
├─ 手順・ステップ（順序あり）  → numbered-list
├─ テキスト＋図・画像          → text-image
├─ 2つの並列トピック           → two-column-text
└─ 3つの並列トピック           → three-column

Q4: データの見せ方は？
├─ 2〜4個のKPI・指標          → kpi-stats
├─ 表形式（行×列）            → table
└─ グラフ・棒グラフ            → chart-bar
   ※折れ線・円グラフはchart-barのバリエーション注記で対応

Q5: 比較の種類は？
├─ A vs B（2つの選択肢）       → comparison
├─ 変化前後（Before/After）    → before-after
└─ メリット・デメリット        → pros-cons

Q6: プロセスの種類は？
├─ 直線的なステップ            → process-linear
├─ 時間軸・ロードマップ        → timeline
└─ チェックリスト・タスク      → checklist

Q7: 構造の種類は？
├─ 2x2マトリクス（象限）       → matrix-2x2
├─ 循環・ループ                → cycle
├─ 階層・優先度（ピラミッド）  → pyramid
└─ 絞り込み・段階的縮小        → funnel
```

---

## パターンカタログ（26種）

### カテゴリ1: 構造的（Structural）- 7種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| title-cover | structural/title-cover.html | 表紙・タイトルスライド | 最小（タイトル＋サブタイトル＋著者） |
| agenda | structural/agenda.html | 目次・アジェンダ | 小（3〜6項目） |
| section-divider | structural/section-divider.html | セクション区切り | 最小（番号＋タイトル） |
| key-message | structural/key-message.html | 1文強調メッセージ | 最小（20〜40字） |
| summary | structural/summary.html | まとめ・総括 | 小（3〜5ポイント） |
| cta-closing | structural/cta-closing.html | CTA・次のステップ | 小（アクション1〜3個） |
| thankyou-qa | structural/thankyou-qa.html | 終了・Q&A | 最小 |

### カテゴリ2: コンテンツ（Content）- 5種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| bullets | content/bullets.html | 箇条書きリスト | 中（4〜7項目、1項目20字以内） |
| numbered-list | content/numbered-list.html | 番号付き手順 | 中（4〜6ステップ） |
| text-image | content/text-image.html | テキスト＋図/画像 | 中（本文3〜5行＋画像プレースホルダー） |
| two-column-text | content/two-column-text.html | 2列並列テキスト | 中（各列3〜5項目） |
| three-column | content/three-column.html | 3列並列 | 小（各列タイトル＋2〜3行） |

### カテゴリ3: データ（Data）- 3種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| kpi-stats | data/kpi-stats.html | KPI・数値指標 | 最小（2〜4個の数値＋ラベル） |
| table | data/table.html | データテーブル | 中（最大6列×8行） |
| chart-bar | data/chart-bar.html | 棒グラフ（CSS） | 小（4〜6本の棒） |

### カテゴリ4: 比較（Comparison）- 3種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| comparison | comparison/comparison.html | A vs B比較 | 中（各側3〜5ポイント） |
| before-after | comparison/before-after.html | 変化前後 | 中（各側3〜4項目） |
| pros-cons | comparison/pros-cons.html | メリット・デメリット | 中（各側3〜5項目） |

### カテゴリ5: プロセス（Process）- 3種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| process-linear | process/process-linear.html | 直線フロー | 小（3〜5ステップ） |
| timeline | process/timeline.html | 時間軸 | 小（4〜6イベント） |
| checklist | process/checklist.html | チェックリスト | 中（5〜10項目） |

### カテゴリ6: 図解（Diagram）- 4種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| matrix-2x2 | diagram/matrix-2x2.html | 2x2象限マトリクス | 小（軸ラベル＋各象限1〜2行） |
| cycle | diagram/cycle.html | 循環プロセス | 最小（3〜5ステップ） |
| pyramid | diagram/pyramid.html | 階層・優先度 | 小（3〜5層、各層10字以内） |
| funnel | diagram/funnel.html | 漏斗・絞り込み | 小（3〜5段階） |

### カテゴリ7: その他（Other）- 1種

| パターン名 | ファイル | 用途 | テキスト量 |
|-----------|---------|------|-----------|
| quote | other/quote.html | 引用・証言 | 最小（引用文50〜100字＋出典） |

---

## テーマ別ディレクトリ

```
patterns/
├── clean-light/   ← Clean Light テーマ（白背景＋青アクセント）
│   ├── structural/
│   ├── content/
│   ├── data/
│   ├── comparison/
│   ├── process/
│   ├── diagram/
│   └── other/
└── bw-swiss/      ← B&W Swiss テーマ（スイス国際タイポグラフィ）
    ├── structural/
    ├── content/
    ├── data/
    ├── comparison/
    ├── process/
    ├── diagram/
    └── other/
```

---

## 削除したパターンと理由

| パターン | 削除理由 | 代替 |
|---------|---------|------|
| chart-line | CSS-onlyの折れ線グラフは不安定 | chart-bar に注記で対応 |
| chart-pie | CSS-onlyの円グラフは脆弱 | chart-bar または kpi-stats |
| hub-spoke | CSSで正確な放射配置が困難 | cycle の変形として対応 |
| venn | CSS-onlyのベン図は脆弱 | matrix-2x2 で概念的に代替 |
| team-grid | three-column のバリアント | three-column |
| profile | quote のバリアント | quote |
