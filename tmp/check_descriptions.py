import sys
sys.stdout.reconfigure(encoding='utf-8')

descriptions = {
    "agent-browser": (
        "Browser automation for AI agents. Use for website interactions: navigate, fill forms, "
        "click, screenshot, scrape data, or test web apps. "
        "Triggers: 'open website', 'fill form', 'automate browser'."
    ),
    "deep-research": (
        "Enterprise-grade research with multi-source synthesis and verification. "
        "Use for 10+ source analysis or comparison. "
        "Triggers: 'deep research', 'research report', 'compare X vs Y', 'analyze trends'."
    ),
    "doc-coauthoring": (
        "Structured workflow for co-authoring docs. Use when user wants to write documentation, "
        "proposals, technical specs, or decision docs. "
        "Triggers: writing docs, creating proposals, drafting specs."
    ),
    "docx": (
        "Work with .docx files: create documents, edit content, tracked changes, add comments, "
        "extract text, preserve formatting. Use whenever a .docx file is involved."
    ),
    "factory-chatlog": (
        "1688工場チャットログの解析・NocoDB登録。テキスト/スクリーンショットからQ&Aを抽出しNocoDBに反映。"
        "トリガー：工場チャット貼り付け、スクリーンショット共有、「チャットログ登録」「やり取りを記録」等の依頼。"
    ),
    "life-session": (
        "ライフセッション（ヒアリング・相談）の運用スキル。lifeプロジェクトから呼び出される。"
        "トリガー：「セッション開始」「スタート」「相談したい」「ヒアリング」。"
    ),
    "pdf": (
        "PDF manipulation: extract text/tables, create PDFs, merge/split documents, handle forms. "
        "Use when filling PDF forms or processing, generating, or analyzing PDF files."
    ),
    "pptx": (
        "Work with .pptx files: create presentations, edit content, modify layouts, "
        "add speaker notes or comments. Use whenever a .pptx file is involved."
    ),
    "skill-creator": (
        "Guide for creating and updating Claude skills. Use when user wants to create or update "
        "a skill that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations."
    ),
    "xlsx": (
        "Work with spreadsheets (.xlsx, .xlsm, .csv, .tsv): create with formulas/formatting, "
        "read/analyze data, edit preserving formulas, data visualization, recalculate formulas."
    ),
}

print(f"{'スキル':<20} {'文字数':>6} {'状態'}")
print("-" * 40)
all_ok = True
for name, desc in descriptions.items():
    length = len(desc)
    status = "✅" if length <= 200 else f"❌ {length}文字"
    if length > 200:
        all_ok = False
    print(f"{name:<20} {length:>6}  {status}")

print()
print("全て200文字以内:" if all_ok else "⚠️ オーバーあり")
