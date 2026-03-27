# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0", "numpy>=1.26.0"]
# ///
"""BSR → 推定月間販売数 変換スクリプト。

使い方:
  uv run bsr_to_sales.py estimate --bsr 500 --category baby_products
  uv run bsr_to_sales.py estimate --bsr 500 --category baby_products/diaper_bags
  uv run bsr_to_sales.py train
  uv run bsr_to_sales.py list-categories

モデル:
  販売数 ≈ exp(A) × BSR^B  （対数線形: log(販売数) = A + B * log(BSR)）
  カテゴリ別 + サブカテゴリ別の2階層。サブカテゴリがあれば優先使用。

学習データ:
  NocoDB の Amazon競合商品テーブル + Amazon販売推移テーブル
  → BSR × 月間販売数 のペアで回帰

係数保存先:
  C:/Users/ninni/data/amazon/bsr_model/coefficients.json
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from lib.config import BSR_MODEL_DIR

COEFFICIENTS_FILE = BSR_MODEL_DIR / "coefficients.json"

# NocoDB API設定（nocodb skillと同じ設定）
NOCODB_BASE_URL = "http://localhost:8080"
NOCODB_API_PATH = "/api/v1/db/data/noco"

# デフォルト係数（学習前の初期値 — 一般的なカテゴリの経験則）
DEFAULT_COEFFICIENTS = {
    "_default": {
        "A": 12.0,
        "B": -0.85,
        "n_samples": 0,
        "mape": None,
        "note": "初期デフォルト値（学習前）",
        "updated_at": None,
    }
}


def _load_coefficients() -> dict:
    if COEFFICIENTS_FILE.exists():
        return json.loads(COEFFICIENTS_FILE.read_text(encoding="utf-8"))
    return DEFAULT_COEFFICIENTS.copy()


def _save_coefficients(coefficients: dict) -> None:
    BSR_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    COEFFICIENTS_FILE.write_text(
        json.dumps(coefficients, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_coefficients_for_category(coefficients: dict, category: str) -> tuple[float, float, dict]:
    """カテゴリ階層でフォールバックしながら係数を取得"""
    # 完全一致
    if category in coefficients:
        c = coefficients[category]
        return c["A"], c["B"], c

    # 親カテゴリにフォールバック（例: baby_products/diaper_bags → baby_products）
    parts = category.rsplit("/", 1)
    if len(parts) > 1:
        parent = parts[0]
        if parent in coefficients:
            c = coefficients[parent]
            return c["A"], c["B"], {**c, "_fallback_from": parent}

    # デフォルト
    c = coefficients.get("_default", DEFAULT_COEFFICIENTS["_default"])
    return c["A"], c["B"], {**c, "_fallback_from": "_default"}


def cmd_estimate(args) -> dict:
    """BSRから推定月間販売数を計算"""
    bsr = args.bsr
    category = args.category

    if bsr <= 0:
        return {"error": "BSR は正の整数で指定してください"}

    coefficients = _load_coefficients()
    A, B, meta = _get_coefficients_for_category(coefficients, category)

    # 販売数 = exp(A) × BSR^B
    estimated = math.exp(A) * (bsr ** B)
    estimated = max(0, round(estimated))

    result = {
        "bsr": bsr,
        "category": category,
        "estimated_monthly_sales": estimated,
        "model": {
            "A": A,
            "B": B,
            "n_samples": meta.get("n_samples", 0),
            "mape": meta.get("mape"),
            "note": meta.get("note", ""),
        },
    }
    if "_fallback_from" in meta:
        result["model"]["fallback_from"] = meta["_fallback_from"]
        result["model"]["warning"] = f"カテゴリ '{category}' の係数なし → '{meta['_fallback_from']}' を使用"

    return result


def cmd_train(args) -> dict:
    """NocoDB の既存データで BSR→販売数 回帰モデルを学習"""
    try:
        import numpy as np
    except ImportError:
        return {"error": "numpy が必要です: uv add numpy"}

    try:
        import urllib.request
        import urllib.parse

        # NocoDB からトークンを取得して Amazon販売推移テーブルを読み込む
        # nocodb スキルと同じAPIを利用
        print("NocoDB からデータを取得中...", file=sys.stderr)

        # API token をSecret Managerから取得（またはローカル設定から）
        # まず手動でCSVファイルから読み込むフォールバックを提供
        csv_path = Path("tmp/bsr_training_data.csv")
        if not csv_path.exists():
            return {
                "error": "訓練データが見つかりません",
                "instructions": [
                    "1. NocoDBの「Amazon販売推移」テーブルをCSVエクスポート",
                    "2. tmp/bsr_training_data.csv として保存",
                    "   必須カラム: asin, bsr, monthly_sales, category",
                    "3. 再度 train を実行",
                ],
            }

        # CSV読み込み
        data_by_category: dict[str, list[tuple[float, float]]] = {}
        with open(csv_path, encoding="utf-8-sig") as f:
            import csv
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                try:
                    bsr = float(row.get("bsr", 0) or 0)
                    sales = float(row.get("monthly_sales", 0) or 0)
                    category = (row.get("category", "") or "baby_products").strip()
                    if bsr > 0 and sales > 0:
                        if category not in data_by_category:
                            data_by_category[category] = []
                        data_by_category[category].append((bsr, sales))
                        row_count += 1
                except (ValueError, KeyError):
                    continue

        print(f"  読み込み: {row_count}件 / {len(data_by_category)}カテゴリ", file=sys.stderr)

        if row_count == 0:
            return {"error": "有効なデータがありません（bsr > 0 かつ monthly_sales > 0 が必要）"}

        # カテゴリ別に回帰
        coefficients = _load_coefficients()
        results = {}

        for category, pairs in data_by_category.items():
            if len(pairs) < 3:
                print(f"  スキップ ({category}): データ {len(pairs)}件 < 3件", file=sys.stderr)
                continue

            bsr_arr = np.array([p[0] for p in pairs])
            sales_arr = np.array([p[1] for p in pairs])

            # 対数変換
            log_bsr = np.log(bsr_arr)
            log_sales = np.log(sales_arr)

            # 線形回帰: log_sales = A + B * log_bsr
            coeffs = np.polyfit(log_bsr, log_sales, 1)
            B = float(coeffs[0])
            A = float(coeffs[1])

            # MAPE計算
            predicted = np.exp(A) * bsr_arr ** B
            mape = float(np.mean(np.abs((sales_arr - predicted) / sales_arr)))

            coefficients[category] = {
                "A": round(A, 6),
                "B": round(B, 6),
                "n_samples": len(pairs),
                "mape": round(mape, 4),
                "note": f"NocoDB訓練データから生成",
                "updated_at": datetime.now().isoformat(),
            }

            print(f"  {category}: A={A:.3f}, B={B:.3f}, MAPE={mape:.1%}, n={len(pairs)}", file=sys.stderr)
            results[category] = {"A": round(A, 3), "B": round(B, 3), "mape": round(mape, 4), "n": len(pairs)}

        _save_coefficients(coefficients)
        print(f"\n係数を保存: {COEFFICIENTS_FILE}", file=sys.stderr)

        return {
            "trained_categories": len(results),
            "total_samples": row_count,
            "results": results,
            "file": str(COEFFICIENTS_FILE),
        }

    except Exception as e:
        return {"error": str(e)}


def cmd_list_categories(args) -> dict:
    """学習済みカテゴリ一覧を表示"""
    coefficients = _load_coefficients()
    categories = {
        k: {
            "n_samples": v.get("n_samples", 0),
            "mape": v.get("mape"),
            "updated_at": v.get("updated_at"),
        }
        for k, v in coefficients.items()
        if not k.startswith("_")
    }
    return {"categories": categories, "total": len(categories)}


# ============================================================
# CLI
# ============================================================

COMMANDS = {
    "estimate": cmd_estimate,
    "train": cmd_train,
    "list-categories": cmd_list_categories,
}


def main():
    parser = argparse.ArgumentParser(description="BSR → 推定月間販売数 変換")
    sub = parser.add_subparsers(dest="command")

    p_est = sub.add_parser("estimate", help="BSRから推定販売数を計算")
    p_est.add_argument("--bsr", type=int, required=True, help="ベストセラーランキング")
    p_est.add_argument("--category", default="_default",
                       help="カテゴリ（例: baby_products / baby_products/diaper_bags）")

    sub.add_parser("train", help="NocoDB データで係数を学習")
    sub.add_parser("list-categories", help="学習済みカテゴリ一覧")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        result = COMMANDS[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
