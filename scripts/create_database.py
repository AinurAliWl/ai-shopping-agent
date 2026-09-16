import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "data" / "laptops_clean.csv"
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "shop.db"


# ============================================================
# CHECK INPUT FILE
# ============================================================

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"Clean CSV file not found: {CSV_PATH}"
    )


# ============================================================
# CREATE DATABASE DIRECTORY
# ============================================================

DB_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD CSV
# ============================================================

df = pd.read_csv(CSV_PATH)

print("=" * 60)
print("LOADING DATA")
print("=" * 60)
print(f"CSV: {CSV_PATH}")
print(f"Products loaded: {len(df)}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "product_id",
    "brand",
    "product_name",
    "price",
    "processor",
    "processor_brand",
    "cpu_ghz",
    "ram_gb",
    "ram_expandable",
    "ram_max_gb",
    "ram_type",
    "display_type",
    "display_inches",
    "gpu_name",
    "gpu_brand",
    "gpu_vram_gb",
    "ssd_gb",
    "hdd_gb",
    "adapter_w",
    "battery_hours",
    "os",
    "raw_name"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns in CSV: {missing_columns}"
    )

df = df[required_columns]


# ============================================================
# DATA PREPARATION
# ============================================================

# SQLite stores booleans as INTEGER:
# True  -> 1
# False -> 0
df["ram_expandable"] = df["ram_expandable"].astype(int)

# Pandas NaN -> Python None
# SQLite will store None as NULL
df = df.where(pd.notna(df), None)


# ============================================================
# CONNECT TO SQLITE
# ============================================================

connection = sqlite3.connect(DB_PATH)

cursor = connection.cursor()


# ============================================================
# CREATE PRODUCTS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,

    brand TEXT NOT NULL,
    product_name TEXT NOT NULL,
    price REAL NOT NULL,

    processor TEXT NOT NULL,
    processor_brand TEXT NOT NULL,
    cpu_ghz REAL,

    ram_gb REAL NOT NULL,
    ram_expandable INTEGER NOT NULL,
    ram_max_gb REAL NOT NULL,
    ram_type TEXT,

    display_type TEXT,
    display_inches REAL,

    gpu_name TEXT,
    gpu_brand TEXT,
    gpu_vram_gb REAL,

    ssd_gb REAL NOT NULL,
    hdd_gb REAL NOT NULL,

    adapter_w REAL,
    battery_hours REAL,

    os TEXT,

    raw_name TEXT NOT NULL
)
""")


# ============================================================
# INSERT PRODUCTS
# ============================================================

placeholders = ", ".join(["?"] * len(required_columns))

columns_sql = ", ".join(required_columns)

insert_query = f"""
INSERT OR REPLACE INTO products (
    {columns_sql}
)
VALUES (
    {placeholders}
)
"""


for row in df.itertuples(index=False, name=None):
    cursor.execute(insert_query, row)


# ============================================================
# COMMIT CHANGES
# ============================================================

connection.commit()


# ============================================================
# VERIFY DATABASE
# ============================================================

cursor.execute("SELECT COUNT(*) FROM products")

product_count = cursor.fetchone()[0]

print()
print("=" * 60)
print("DATABASE CREATED")
print("=" * 60)
print(f"Database: {DB_PATH}")
print(f"Products in database: {product_count}")


# ============================================================
# SHOW SAMPLE
# ============================================================

cursor.execute("""
SELECT
    product_id,
    brand,
    product_name,
    price,
    ram_gb,
    gpu_brand,
    gpu_name,
    ssd_gb
FROM products
LIMIT 5
""")

rows = cursor.fetchall()

print()
print("FIRST 5 PRODUCTS")
print("=" * 60)

for row in rows:
    print(row)


# ============================================================
# DATABASE SCHEMA
# ============================================================

cursor.execute("""
PRAGMA table_info(products)
""")

schema = cursor.fetchall()

print()
print("PRODUCTS TABLE")
print("=" * 60)

for column in schema:
    column_id = column[0]
    column_name = column[1]
    column_type = column[2]

    print(
        f"{column_id:2} | "
        f"{column_name:20} | "
        f"{column_type}"
    )


# ============================================================
# CLOSE CONNECTION
# ============================================================

connection.close()

print()
print("=" * 60)
print("DONE")
print("=" * 60)
