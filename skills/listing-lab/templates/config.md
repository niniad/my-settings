# exp-{NNN}: {手法名}

## メタ情報
- **実験番号**: exp-{NNN}
- **手法名**: {method-name}
- **対象スロット**: {slot}（例: sub_02, aplus_01）
- **日付**: {YYYY-MM-DD}
- **ステータス**: draft | running | completed

## 仮説
（前回の実験結果から何を変えて、何が改善されると期待するか）

前回: なし（初回ベースライン）
変更点: なし
期待: ベースラインスコアの計測

## 手法の詳細

### 使用ツール
- **生成方法**: html-puppeteer | gemini-direct | gemini-hybrid | other
- **ソースファイル**: src/（HTMLファイルまたはプロンプトJSON）
- **評価プロンプト**: prompts/evaluate-v1.md（スキル内）

### 再現手順

```bash
# Step 1: 画像生成（手法に応じて変更）
uv run python listings/scripts/render_html.py \
  listings/lab/{product}/experiments/exp-{NNN}_{method}/src/design.html \
  listings/lab/{product}/experiments/exp-{NNN}_{method}/output/{slot}.png \
  --width 1600 --height 2000

# Step 2: 評価（listing-lab スキルが自動実行）
# listing-lab exp-{NNN}
```

### 変更点（前回実験との差分）
- なし（初回ベースライン）

## コスト記録（実験完了後に記入）
- 生成コスト:
- 評価コスト（subagent×3）:
- 合計:
