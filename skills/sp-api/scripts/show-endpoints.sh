#!/bin/bash
# 指定したAPIのエンドポイント一覧を表示
# 使用法: ./show-endpoints.sh orders-api-model

MODELS_DIR="/home/ninni/projects/docs/sp-api-models/models"
API_NAME="${1:-orders-api-model}"

API_DIR="$MODELS_DIR/$API_NAME"

if [ ! -d "$API_DIR" ]; then
    echo "エラー: $API_NAME が見つかりません"
    echo "利用可能なAPI:"
    ls "$MODELS_DIR"
    exit 1
fi

echo "=== $API_NAME エンドポイント一覧 ==="
echo ""

for json_file in "$API_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        echo "ファイル: $(basename "$json_file")"
        echo "---"
        python3 -c "
import json
with open('$json_file') as f:
    d = json.load(f)
    paths = d.get('paths', {})
    for path, methods in paths.items():
        for method in methods.keys():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                summary = methods[method].get('summary', methods[method].get('operationId', 'N/A'))
                print(f'{method.upper():6} {path}')
                print(f'       {summary}')
                print()
" 2>/dev/null
    fi
done
