#!/usr/bin/env python3
"""
render_html.py - HTML/CSSデザインをPNGまたはPDFとしてレンダリングする

使い方:
    python render_html.py input.html output.png [--width 2000] [--height 2000] [--scale 1]
    python render_html.py input.html output.pdf [--width 2000] [--height 2000]

出力形式は拡張子で自動判定する。.pdf ならPDF、それ以外はPNG。

依存:
    - Node.js
    - puppeteer (npm install puppeteer)

引数:
    input       : レンダリングするHTMLファイルのパス
    output      : 出力ファイルのパス（.pdfまたは.png）
    --width     : 画像幅（px）。デフォルト: 2000
    --height    : 画像高さ（px）。デフォルト: 2000
    --scale     : デバイススケール（PNG時のみ有効）。デフォルト: 1
    --wait      : フォント読み込み待ち時間（ms）。デフォルト: 2000
    --transparent: 背景を透過にする（PNG時のみ有効）
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile


def create_puppeteer_script(html_path: str, output_path: str,
                             width: int, height: int, scale: int,
                             wait_ms: int, transparent: bool,
                             output_format: str) -> str:
    """Puppeteerスクリプト（JavaScript）を生成する"""

    html_abs = os.path.abspath(html_path)
    output_abs = os.path.abspath(output_path)

    # Windows対応: バックスラッシュをエスケープ
    html_url = f"file://{html_abs}".replace("\\", "/")
    output_js = output_abs.replace("\\", "/")

    if output_format == "pdf":
        render_command = f"""
    // PDF出力
    await page.pdf({{
        path: '{output_js}',
        width: '{width}px',
        height: '{height}px',
        printBackground: true,
        margin: {{ top: 0, right: 0, bottom: 0, left: 0 }}
    }});"""
    else:
        render_command = f"""
    // PNG出力
    await page.screenshot({{
        path: '{output_js}',
        type: 'png',
        clip: {{
            x: 0,
            y: 0,
            width: {width},
            height: {height}
        }},
        omitBackground: {'true' if transparent else 'false'}
    }});"""

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
{render_command}

    await browser.close();

    console.log(JSON.stringify({{
        success: true,
        output: '{output_js}',
        format: '{output_format}',
        dimensions: {{ width: {width}{f' * {scale}' if output_format == 'png' else ''}, height: {height}{f' * {scale}' if output_format == 'png' else ''} }},
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
    """HTMLをPNGまたはPDFにレンダリングする

    出力形式はoutput_pathの拡張子で自動判定。

    Returns:
        dict: {success: bool, output: str, format: str, dimensions: {width, height}, scale: int}
    """

    if not os.path.exists(html_path):
        return {"success": False, "error": f"HTML file not found: {html_path}"}

    # 出力形式を拡張子から判定
    _, ext = os.path.splitext(output_path)
    output_format = "pdf" if ext.lower() == ".pdf" else "png"

    # 出力ディレクトリを作成
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Puppeteerスクリプトを生成
    script = create_puppeteer_script(
        html_path, output_path, width, height, scale, wait_ms, transparent, output_format
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
                    "format": output_format,
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
        description="HTML/CSSデザインをPNGまたはPDFとしてレンダリングする"
    )
    parser.add_argument("input", help="入力HTMLファイルのパス")
    parser.add_argument("output", help="出力ファイルのパス（.pdfまたは.png）")
    parser.add_argument("--width", type=int, default=2000, help="画像幅（px）。デフォルト: 2000")
    parser.add_argument("--height", type=int, default=2000, help="画像高さ（px）。デフォルト: 2000")
    parser.add_argument("--scale", type=int, default=1, help="デバイススケール（PNG時のみ）。デフォルト: 1")
    parser.add_argument("--wait", type=int, default=2000, help="フォント読み込み待ち（ms）。デフォルト: 2000")
    parser.add_argument("--transparent", action="store_true", help="背景を透過にする（PNG時のみ）")

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
        fmt = result.get("format", "png").upper()
        dims = result.get("dimensions", {})
        print(f"  {fmt}レンダリング完了: {result['output']}")
        print(f"   サイズ: {dims.get('width', '?')}×{dims.get('height', '?')}px")
    else:
        print(f"  エラー: {result.get('error', 'Unknown error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
