#!/usr/bin/env python3
"""
render_html.py - HTML/CSSデザインをPNG画像としてレンダリングする

使い方:
    python render_html.py input.html output.png [--width 2000] [--height 2000] [--scale 1]

依存:
    - Node.js
    - puppeteer (npm install puppeteer)

引数:
    input.html  : レンダリングするHTMLファイルのパス
    output.png  : 出力PNG画像のパス
    --width     : 画像幅（px）。デフォルト: 2000
    --height    : 画像高さ（px）。デフォルト: 2000
    --scale     : デバイススケール。2にするとRetina相当の高解像度。デフォルト: 1
    --wait      : フォント読み込み待ち時間（ms）。デフォルト: 2000
    --transparent: 背景を透過にする
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile


def create_puppeteer_script(html_path: str, output_path: str,
                             width: int, height: int, scale: int,
                             wait_ms: int, transparent: bool) -> str:
    """Puppeteerスクリプト（JavaScript）を生成する"""

    html_abs = os.path.abspath(html_path)
    output_abs = os.path.abspath(output_path)

    # Windows対応: バックスラッシュをエスケープ
    html_url = f"file://{html_abs}".replace("\\", "/")

    script = f"""
const puppeteer = require('puppeteer');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
    }});

    const page = await browser.newPage();

    await page.setViewport({{
        width: {width},
        height: {height},
        deviceScaleFactor: {scale}
    }});

    // HTMLを読み込み
    await page.goto('{html_url}', {{
        waitUntil: 'networkidle0',
        timeout: 30000
    }});

    // フォント読み込みを待機
    await page.evaluateHandle('document.fonts.ready');
    await new Promise(r => setTimeout(r, {wait_ms}));

    // スクリーンショット撮影
    await page.screenshot({{
        path: '{output_abs}',
        type: 'png',
        clip: {{
            x: 0,
            y: 0,
            width: {width},
            height: {height}
        }},
        omitBackground: {'true' if transparent else 'false'}
    }});

    await browser.close();

    console.log(JSON.stringify({{
        success: true,
        output: '{output_abs}',
        dimensions: {{ width: {width} * {scale}, height: {height} * {scale} }},
        scale: {scale}
    }}));
}})().catch(err => {{
    console.error(JSON.stringify({{ success: false, error: err.message }}));
    process.exit(1);
}});
"""
    return script


def render(html_path: str, output_path: str,
           width: int = 2000, height: int = 2000,
           scale: int = 1, wait_ms: int = 2000,
           transparent: bool = False) -> dict:
    """HTMLをPNGにレンダリングする

    Returns:
        dict: {success: bool, output: str, dimensions: {width, height}, scale: int}
    """

    if not os.path.exists(html_path):
        return {"success": False, "error": f"HTML file not found: {html_path}"}

    # 出力ディレクトリを作成
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Puppeteerスクリプトを生成
    script = create_puppeteer_script(
        html_path, output_path, width, height, scale, wait_ms, transparent
    )

    # 一時ファイルにスクリプトを書き出し
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        # Node.jsでPuppeteerスクリプトを実行
        result = subprocess.run(
            ['node', script_path],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            try:
                error_data = json.loads(error_msg)
                return error_data
            except json.JSONDecodeError:
                return {"success": False, "error": error_msg}

        # 結果をパース
        output = result.stdout.strip()
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            if os.path.exists(output_path):
                return {
                    "success": True,
                    "output": output_path,
                    "dimensions": {"width": width * scale, "height": height * scale},
                    "scale": scale
                }
            return {"success": False, "error": f"Unexpected output: {output}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Rendering timed out (60s)"}
    except FileNotFoundError:
        return {"success": False, "error": "Node.js not found. Install Node.js and run: npm install puppeteer"}
    finally:
        os.unlink(script_path)


def main():
    parser = argparse.ArgumentParser(
        description="HTML/CSSデザインをPNG画像としてレンダリングする"
    )
    parser.add_argument("input", help="入力HTMLファイルのパス")
    parser.add_argument("output", help="出力PNGファイルのパス")
    parser.add_argument("--width", type=int, default=2000, help="画像幅（px）。デフォルト: 2000")
    parser.add_argument("--height", type=int, default=2000, help="画像高さ（px）。デフォルト: 2000")
    parser.add_argument("--scale", type=int, default=1, help="デバイススケール（1 or 2）。デフォルト: 1")
    parser.add_argument("--wait", type=int, default=2000, help="フォント読み込み待ち（ms）。デフォルト: 2000")
    parser.add_argument("--transparent", action="store_true", help="背景を透過にする")

    args = parser.parse_args()

    result = render(
        html_path=args.input,
        output_path=args.output,
        width=args.width,
        height=args.height,
        scale=args.scale,
        wait_ms=args.wait,
        transparent=args.transparent
    )

    if result.get("success"):
        dims = result.get("dimensions", {})
        print(f"✅ レンダリング完了: {result['output']}")
        print(f"   サイズ: {dims.get('width', '?')}×{dims.get('height', '?')}px (scale: {result.get('scale', 1)})")
    else:
        print(f"❌ エラー: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
