#!/bin/bash
# Amazon Ads APIスキーマ一覧を表示

SCHEMAS_DIR="/home/ninni/projects/.claude/skills/amazon-ads/models/amazon-ads-api/docs/schemas"

echo "=== Amazon Ads API スキーマ一覧 ==="
echo ""

for schema in "$SCHEMAS_DIR"/*.json; do
    if [ -f "$schema" ]; then
        name=$(basename "$schema" .json)
        # タイトルを抽出
        title=$(python3 -c "import json; d=json.load(open('$schema')); print(d.get('info',{}).get('title','N/A'))" 2>/dev/null || echo "N/A")
        echo "- $name: $title"
    fi
done
