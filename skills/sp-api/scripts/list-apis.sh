#!/bin/bash
# SP-API一覧を表示

MODELS_DIR="/home/ninni/projects/docs/sp-api-models/models"

echo "=== Amazon SP-API 一覧 ==="
echo ""

for dir in "$MODELS_DIR"/*/; do
    api_name=$(basename "$dir")
    # JSONファイルを探す
    json_file=$(find "$dir" -name "*.json" -type f | head -1)
    if [ -n "$json_file" ]; then
        # APIタイトルを抽出
        title=$(python3 -c "import json; d=json.load(open('$json_file')); print(d.get('info',{}).get('title','N/A'))" 2>/dev/null || echo "N/A")
        echo "- $api_name: $title"
    fi
done
