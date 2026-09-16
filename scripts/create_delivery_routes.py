import sqlite3
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
# CREATE DELIVERY ROUTES TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS delivery_routes (
    route_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_location_id INTEGER NOT NULL,
    to_location_id INTEGER NOT NULL,
    min_days INTEGER NOT NULL CHECK (min_days >= 0),
    max_days INTEGER NOT NULL CHECK (max_days >= min_days),

    FOREIGN KEY (from_location_id)
        REFERENCES locations(location_id),

    FOREIGN KEY (to_location_id)
        REFERENCES locations(location_id),

    UNIQUE(from_location_id, to_location_id)
)
""")


# ============================================================
# GET LOCATION IDS
# ============================================================

cursor.execute("""
SELECT location_id, location_name
FROM locations
""")

locations = {
    location_name: location_id
    for location_id, location_name in cursor.fetchall()
}


required_locations = [
    "Central Warehouse",
    "Astana Mega Silk Way",
    "Astana Khan Shatyr",
]

for location in required_locations:
    if location not in locations:
        raise ValueError(f"Location not found: {location}")


warehouse_id = locations["Central Warehouse"]
mega_id = locations["Astana Mega Silk Way"]
khan_shatyr_id = locations["Astana Khan Shatyr"]


# ============================================================
# CLEAR OLD ROUTES
# ============================================================

cursor.execute("DELETE FROM delivery_routes")


# ============================================================
# CREATE ROUTES
# ============================================================

routes = [
    # Warehouse → Mega Silk Way
    (warehouse_id, mega_id, 1, 2),

    # Warehouse → Khan Shatyr
    (warehouse_id, khan_shatyr_id, 2, 3),
]


cursor.executemany("""
INSERT INTO delivery_routes (
    from_location_id,
    to_location_id,
    min_days,
    max_days
)
VALUES (?, ?, ?, ?)
""", routes)


connection.commit()


# ============================================================
# SHOW ROUTES
# ============================================================

print("=" * 60)
print("DELIVERY ROUTES")
print("=" * 60)

cursor.execute("""
SELECT
    r.route_id,
    source.location_name,
    destination.location_name,
    r.min_days,
    r.max_days
FROM delivery_routes r
JOIN locations source
    ON r.from_location_id = source.location_id
JOIN locations destination
    ON r.to_location_id = destination.location_id
ORDER BY r.route_id
""")

for route_id, source, destination, min_days, max_days in cursor.fetchall():
    print(
        f"{source} -> {destination} | "
        f"{min_days}-{max_days} days"
    )


# ============================================================
# CLOSE DATABASE
# ============================================================

connection.close()

print()
print("=" * 60)
print("DONE")
print("=" * 60)
print(f"Database: {DB_PATH}")