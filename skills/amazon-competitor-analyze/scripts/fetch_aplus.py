# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0"]
# ///
"""Amazon.co.jp A+コンテンツ取得スクリプト（agent-browser使用）。

使い方:
  uv run fetch_aplus.py --asins B000PARENT1 B000PARENT2 --product マザーズリュック

前提:
  - agent-browser の amazon-jp セッションが確立済みであること
    （初回: npx.cmd agent-browser --session-name amazon-jp open https://www.amazon.co.jp でログイン）
  - 親ASINを渡すことを推奨（Amazon が自動的にデフォルトバリエーションにリダイレクトする）

出力:
  Eagle: Amazon競合データ/{product}/{親ASIN}/ に aplus JSON + A+画像を登録
  ※ローカルファイルは一時作成後に自動削除

A+画像のタグ:
  type:image, parent_asin:{ASIN}, child_asin:{ASIN}（親と同値）,
  variant:APLUS_01, variant:APLUS_02 ..., captured:{YYYYMM}
"""

import argparse
import json
import random
import subprocess
import sys
import sys as _sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from lib.eagle_integration import download_and_register, eagle_available, register_file

SELECTORS_FILE = _SCRIPT_DIR / "selectors" / "amazon_jp.json"
AGENT_BROWSER = "npx.cmd" if _sys.platform == "win32" else "npx"
AGENT_BROWSER_ARGS = ["agent-browser", "--session-name", "amazon-jp"]


def _load_selectors() -> dict:
    return json.loads(SELECTORS_FILE.read_text(encoding="utf-8"))


def _ab_eval(js: str) -> str:
    cmd = [AGENT_BROWSER] + AGENT_BROWSER_ARGS + ["eval", "--stdin"]
    result = subprocess.run(
        cmd, input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return result.stdout.strip()


def _ab_open(url: str) -> None:
    cmd = [AGENT_BROWSER] + AGENT_BROWSER_ARGS + ["open", url]
    subprocess.run(cmd, capture_output=True, timeout=30)


def _ab_scroll_to_aplus() -> None:
    """A+コンテンツエリアまでスクロールしてlazy-load画像を読み込ませる"""
    js = """
(function() {
  const el = document.querySelector('#aplus') || document.querySelector('#aplus_feature_div');
  if (el) {
    el.scrollIntoView({behavior: 'instant'});
  } else {
    window.scrollTo(0, document.body.scrollHeight * 0.7);
  }
  return true;
})()
"""
    cmd = [AGENT_BROWSER] + AGENT_BROWSER_ARGS + ["eval", "--stdin"]
    subprocess.run(cmd, input=js, capture_output=True, text=True, encoding="utf-8", timeout=30)


_PLACEHOLDER_PATTERNS = ["grey-pixel", "transparent-pixel", "grey_pixel", "1x1.gif"]


def _extract_aplus_js(selectors: dict) -> str:
    containers = selectors["aplus"]["container"]
    text_sels = selectors["aplus"]["text_sections"]

    return f"""
(function() {{
  const containers = {json.dumps(containers)};
  const textSels = {json.dumps(text_sels)};
  const PLACEHOLDERS = {json.dumps(_PLACEHOLDER_PATTERNS)};

  let container = null;
  for (const sel of containers) {{
    container = document.querySelector(sel);
    if (container) break;
  }}
  if (!container) return {{found: false}};

  // テキスト抽出
  let texts = [];
  for (const sel of textSels) {{
    const els = container.querySelectorAll(sel);
    if (els.length > 0) {{
      texts = Array.from(els).map(el => el.innerText.trim()).filter(t => t.length > 0);
      break;
    }}
  }}
  if (texts.length === 0) {{
    texts = [container.innerText.trim()];
  }}

  // 画像URL抽出（lazy-load対応）
  // data-old-hires / data-src / data-a-dynamic-image を優先、なければ src
  const allImgs = Array.from(container.querySelectorAll('img'));
  const imageUrls = [];
  for (const img of allImgs) {{
    let url = img.getAttribute('data-old-hires')
      || img.getAttribute('data-src')
      || img.src
      || '';
    // data-a-dynamic-image はJSON({{url: [w,h], ...}})→最大サイズのURLを取得
    const dynImg = img.getAttribute('data-a-dynamic-image');
    if (dynImg && dynImg.startsWith('{{')) {{
      try {{
        const map = JSON.parse(dynImg);
        let bestUrl = '', bestArea = 0;
        for (const [u, dims] of Object.entries(map)) {{
          const area = dims[0] * dims[1];
          if (area > bestArea) {{ bestArea = area; bestUrl = u; }}
        }}
        if (bestUrl) url = bestUrl;
      }} catch(e) {{}}
    }}
    if (!url || !url.startsWith('http')) continue;
    if (PLACEHOLDERS.some(p => url.includes(p))) continue;
    imageUrls.push(url);
  }}

  return {{found: true, texts, imageUrls}};
}})()
"""


def _fetch_aplus_for_asin(asin: str, product_name: str, selectors: dict) -> dict:
    """親ASINのA+コンテンツを取得（Amazonがデフォルトバリエーションにリダイレクト）"""
    url = f"https://www.amazon.co.jp/dp/{asin}"
    print(f"  ページ開く: {url}", file=sys.stderr)
    _ab_open(url)
    time.sleep(2)

    # A+コンテンツはページ下部→スクロールしてlazy-load画像を読み込ませる
    print(f"  A+エリアへスクロール中...", file=sys.stderr)
    _ab_scroll_to_aplus()
    time.sleep(2)  # lazy-load発動待機

    raw = _ab_eval(_extract_aplus_js(selectors))
    try:
        data = json.loads(raw) if raw and raw.startswith("{") else {"found": False}
    except Exception:
        data = {"found": False, "error": raw}

    if not data.get("found"):
        print(f"  A+コンテンツ未検出: {asin}", file=sys.stderr)
        return {"asin": asin, "found": False, "texts": [], "images": []}

    texts = data.get("texts", [])
    image_urls = data.get("imageUrls", [])
    print(f"  テキスト: {len(texts)}セクション, 画像: {len(image_urls)}枚", file=sys.stderr)

    # A+画像をEagleに登録（parent_asin単位、child_asinは親と同値）
    eagle_images = []
    if image_urls and eagle_available():
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            for idx, img_url in enumerate(image_urls):
                variant = f"APLUS_{idx+1:02d}"
                result = download_and_register(
                    url=img_url,
                    parent_asin=asin,
                    variant=variant,
                    product_name=product_name,
                    tmp_dir=tmp,
                    child_asin=None,  # A+は親ASIN単位なのでchild_asin=None（親と同値で登録）
                )
                eagle_images.append(result)
            time.sleep(max(3, len(image_urls) * 0.2))  # Eagle が非同期コピーを完了するまで待機（画像数に比例）

    return {
        "asin": asin,
        "found": True,
        "texts": texts,
        "full_text": "\n\n".join(texts),
        "image_urls": image_urls,
        "eagle_images": eagle_images,
    }


def _register_aplus_eagle(
    file_path: Path, parent_asin: str, product_name: str
) -> str | None:
    """A+コンテンツJSONをEagleに登録"""
    if not eagle_available():
        return None

    captured = datetime.now().strftime("%Y%m")
    tags = [
        "type:aplus",
        f"parent_asin:{parent_asin}",
        f"captured:{captured}",
    ]
    return register_file(
        file_path=file_path,
        parent_asin=parent_asin,
        product_name=product_name,
        tags=tags,
        name=file_path.name,
    )


def cmd_fetch(args):
    selectors = _load_selectors()
    product_name = args.product or "unknown"
    results = {"success": [], "failed": []}

    for i, asin in enumerate(args.asins):
        print(f"[{i+1}/{len(args.asins)}] {asin} A+取得中...", file=sys.stderr)

        try:
            data = _fetch_aplus_for_asin(asin, product_name, selectors)

            # Eagle登録（tmpに書いて登録後に削除）
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"aplus_{date_str}.json"
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / filename
                tmp_path.write_text(
                    json.dumps({"fetched_at": datetime.now().isoformat(), **data},
                               ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                _register_aplus_eagle(tmp_path, asin, product_name)
                time.sleep(2)  # Eagle が JSON コピーを完了するまで待機

            print(f"  ✓ {asin}", file=sys.stderr)
            results["success"].append({"asin": asin})

        except Exception as e:
            print(f"  ✗ {asin}: {e}", file=sys.stderr)
            results["failed"].append({"asin": asin, "error": str(e)})

        if i < len(args.asins) - 1:
            time.sleep(random.uniform(3, 5))

    return results


def main():
    parser = argparse.ArgumentParser(description="Amazon.co.jp A+コンテンツ取得")
    parser.add_argument("--asins", nargs="+", required=True,
                        help="ASINリスト（親ASINを推奨）")
    parser.add_argument("--product", required=True,
                        help="Eagleフォルダ名（例: マザーズリュック）")
    args = parser.parse_args()

    try:
        result = cmd_fetch(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
