# BigQuery

## 基本操作

### データセット一覧
```bash
bq ls
bq ls project-id:
```

### テーブル一覧
```bash
bq ls dataset_name
```

### クエリ実行
```bash
bq query --use_legacy_sql=false 'SELECT * FROM `project.dataset.table` LIMIT 10'
```

### テーブルスキーマ確認
```bash
bq show --schema --format=prettyjson project:dataset.table
```

### CSVからテーブル作成
```bash
bq load --autodetect --source_format=CSV dataset.table gs://bucket/file.csv
```

### テーブルをCSVにエクスポート
```bash
bq extract project:dataset.table gs://bucket/output.csv
```

## Python SDK

```python
from google.cloud import bigquery

client = bigquery.Client()

# クエリ実行
query = """
SELECT *
FROM `project.dataset.table`
LIMIT 10
"""
results = client.query(query).result()
for row in results:
    print(row)

# DataFrameに変換
df = client.query(query).to_dataframe()

# テーブルにデータ挿入
table_id = "project.dataset.table"
rows = [{"column1": "value1", "column2": 123}]
client.insert_rows_json(table_id, rows)
```

## よくあるエラー

### Access Denied
```
権限不足。サービスアカウントにBigQuery権限を付与：
- roles/bigquery.dataViewer（読み取り）
- roles/bigquery.dataEditor（読み書き）
- roles/bigquery.jobUser（クエリ実行）
```

### Not found: Dataset/Table
```
データセットまたはテーブルが存在しない。
bq ls でデータセット一覧を確認。
```

### Query exceeded resource limits
```
クエリが大きすぎる。LIMIT句を追加するか、パーティションを指定。
```
