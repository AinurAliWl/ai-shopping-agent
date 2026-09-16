import sqlite3
import random
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "shop.db"


if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")


# ============================================================
# DATABASE CONNECTION
# ============================================================

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


# ============================================================
# CREATE LOCATIONS TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    location_type TEXT NOT NULL CHECK (
        location_type IN ('store', 'warehouse')
    )
)
""")


# ============================================================
# CREATE INVENTORY TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    
    FOREIGN KEY (product_id)
        REFERENCES products(product_id),
    
    FOREIGN KEY (location_id)
        REFERENCES locations(location_id),
    
    UNIQUE(product_id, location_id)
)
""")


# ============================================================
# CREATE LOCATIONS
# ============================================================

locations = [
    ("Astana Mega Silk Way", "store"),
    ("Astana Khan Shatyr", "store"),
    ("Central Warehouse", "warehouse"),
]


# Clear old locations/inventory if script is run again
cursor.execute("DELETE FROM inventory")
cursor.execute("DELETE FROM locations")


for location_name, location_type in locations:
    cursor.execute(
        """
        INSERT INTO locations (location_name, location_type)
        VALUES (?, ?)
        """,
        (location_name, location_type)
    )


# ============================================================
# GET LOCATION IDS
# ============================================================

cursor.execute("""
SELECT location_id, location_name, location_type
FROM locations
""")

location_rows = cursor.fetchall()

location_ids = {
    location_type: []
    for location_type in ("store", "warehouse")
}

for location_id, location_name, location_type in location_rows:
    location_ids[location_type].append(location_id)


# ============================================================
# GET PRODUCTS
# ============================================================

cursor.execute("""
SELECT product_id
FROM products
""")

products = cursor.fetchall()

print("=" * 60)
print("CREATING INVENTORY")
print("=" * 60)
print(f"Products found: {len(products)}")


# ============================================================
# GENERATE SYNTHETIC INVENTORY
# ============================================================

random.seed(42)

inventory_records = []

for (product_id,) in products:

    # --------------------------------------------------------
    # STORES
    # --------------------------------------------------------

    for location_id in location_ids["store"]:

        # Not every product is available in every store
        if random.random() < 0.35:
            quantity = random.randint(1, 3)

            inventory_records.append(
                (product_id, location_id, quantity)
            )

    # --------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------

    # Most products can be available in the warehouse
    if random.random() < 0.70:
        quantity = random.randint(1, 10)

        inventory_records.append(
            (
                product_id,
                location_ids["warehouse"][0],
                quantity
            )
        )


# ============================================================
# INSERT INVENTORY
# ============================================================

cursor.executemany(
    """
    INSERT INTO inventory (
        product_id,
        location_id,
        quantity
    )
    VALUES (?, ?, ?)
    """,
    inventory_records
)


connection.commit()


# ============================================================
# SHOW RESULTS
# ============================================================

cursor.execute("SELECT COUNT(*) FROM locations")
location_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM inventory")
inventory_count = cursor.fetchone()[0]


print()
print("=" * 60)
print("LOCATIONS")
print("=" * 60)

cursor.execute("""
SELECT location_id, location_name, location_type
FROM locations
ORDER BY location_id
""")

for row in cursor.fetchall():
    print(row)


print()
print("=" * 60)
print("INVENTORY")
print("=" * 60)
print(f"Inventory records: {inventory_count}")


# ============================================================
# SHOW SAMPLE INVENTORY
# ============================================================

print()
print("=" * 60)
print("SAMPLE INVENTORY")
print("=" * 60)

cursor.execute("""
SELECT
    p.product_id,
    p.product_name,
    l.location_name,
    l.location_type,
    i.quantity
FROM inventory i
JOIN products p
    ON i.product_id = p.product_id
JOIN locations l
    ON i.location_id = l.location_id
ORDER BY p.product_id
LIMIT 10
""")

for row in cursor.fetchall():
    print(row)


# ============================================================
# CLOSE DATABASE
# ============================================================

connection.close()

print()
print("=" * 60)
print("DONE")
print("=" * 60)
print(f"Database: {DB_PATH}")
print(f"Locations: {location_count}")
print(f"Inventory records: {inventory_count}")