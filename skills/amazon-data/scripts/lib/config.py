"""共通設定"""

from pathlib import Path

# SP-API
SP_API_ENDPOINT = "https://sellingpartnerapi-fe.amazon.com"
MARKETPLACE_ID = "A1VC38T7YXB528"  # 日本

# includedData: 商品情報フルセット
CATALOG_INCLUDED_DATA = [
    "summaries", "attributes", "dimensions", "identifiers",
    "images", "salesRanks", "relationships", "classifications",
]

# 画像: 商品ページに表示されるバリアントのみ取得
IMAGE_VARIANTS = ["MAIN", "PT01", "PT02", "PT03", "PT04", "PT05", "PT06", "PT07", "PT08"]

# データストア
DATA_ROOT = Path("C:/Users/ninni/data/amazon")
COMPETITORS_DIR = DATA_ROOT / "competitors"
BSR_MODEL_DIR = DATA_ROOT / "bsr_model"
INDEX_FILE = COMPETITORS_DIR / "index.json"

# Eagle: 競合データのルートフォルダ名
EAGLE_COMPETITOR_ROOT = "Amazon競合データ"

# レート制限: getCatalogItem 2 TPS
CATALOG_SLEEP_SEC = 1.5
