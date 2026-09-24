import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "shop.db"


def search_products(
    max_price=None,
    min_ram=None,
    gpu_brand=None,
    min_ssd=None,
    brand=None,
    os=None,
    limit=20,
):
    """
    Search products in the SQLite catalog.

    Parameters:
        max_price: maximum product price
        min_ram: minimum RAM in GB
        gpu_brand: GPU manufacturer, e.g. NVIDIA
        min_ssd: minimum SSD capacity in GB
        brand: laptop brand, e.g. Dell
        os: operating system, e.g. Windows 11
        limit: maximum number of results
    """

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    query = """
        SELECT
            product_id,
            brand,
            product_name,
            price,
            processor,
            ram_gb,
            ram_max_gb,
            gpu_name,
            gpu_brand,
            gpu_vram_gb,
            ssd_gb,
            hdd_gb,
            os
        FROM products
        WHERE 1 = 1
    """

    parameters = []

    if max_price is not None:
        query += " AND price <= ?"
        parameters.append(max_price)

    if min_ram is not None:
        query += " AND ram_gb >= ?"
        parameters.append(min_ram)

    if gpu_brand is not None:
        query += " AND LOWER(gpu_brand) = LOWER(?)"
        parameters.append(gpu_brand)

    if min_ssd is not None:
        query += " AND ssd_gb >= ?"
        parameters.append(min_ssd)

    if brand is not None:
        query += " AND LOWER(brand) = LOWER(?)"
        parameters.append(brand)

    if os is not None:
        query += " AND LOWER(os) = LOWER(?)"
        parameters.append(os)

    query += " ORDER BY price ASC LIMIT ?"
    parameters.append(limit)

    cursor.execute(query, parameters)

    products = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return products

def get_product_details(product_id):
    """
    Get complete information about a single product.

    Parameters:
        product_id: unique product identifier, e.g. LAP0001

    Returns:
        Product details as a dictionary, or None if the product
        does not exist.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT
            product_id,
            brand,
            product_name,
            price,
            processor,
            processor_brand,
            cpu_ghz,
            ram_gb,
            ram_expandable,
            ram_max_gb,
            ram_type,
            display_type,
            display_inches,
            gpu_name,
            gpu_brand,
            gpu_vram_gb,
            ssd_gb,
            hdd_gb,
            adapter_w,
            battery_hours,
            os,
            raw_name
        FROM products
        WHERE product_id = ?
    """

    cursor.execute(query, (product_id,))
    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def check_store_stock(product_id, store_name=None):
    """
    Check product availability in physical stores.

    Parameters:
        product_id: unique product identifier, e.g. LAP0003
        store_name: optional store name

    Returns:
        List of stores with available stock.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT
            l.location_name,
            i.quantity
        FROM inventory i
        JOIN locations l
            ON i.location_id = l.location_id
        WHERE i.product_id = ?
          AND l.location_type = 'store'
          AND i.quantity > 0
    """

    parameters = [product_id]

    if store_name is not None:
        query += " AND LOWER(l.location_name) = LOWER(?)"
        parameters.append(store_name)

    cursor.execute(query, parameters)

    stores = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return stores


def check_warehouse_stock(product_id):
    """
    Check product availability in warehouses.

    Parameters:
        product_id: unique product identifier

    Returns:
        List of warehouses with available stock.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT
            l.location_name,
            i.quantity
        FROM inventory i
        JOIN locations l
            ON i.location_id = l.location_id
        WHERE i.product_id = ?
          AND l.location_type = 'warehouse'
          AND i.quantity > 0
    """

    cursor.execute(query, (product_id,))

    warehouses = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return warehouses


def get_delivery_time(product_id, destination_store):
    """
    Get estimated delivery time for a product from the warehouse
    to a specific store.

    Parameters:
        product_id: unique product identifier, e.g. LAP0003
        destination_store: destination store name

    Returns:
        Delivery information as a dictionary, or None if
        the product is unavailable or the route does not exist.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT
            p.product_id,
            source.location_name AS warehouse,
            destination.location_name AS destination,
            i.quantity,
            r.min_days,
            r.max_days
        FROM inventory i

        JOIN products p
            ON i.product_id = p.product_id

        JOIN locations source
            ON i.location_id = source.location_id

        JOIN delivery_routes r
            ON r.from_location_id = source.location_id

        JOIN locations destination
            ON r.to_location_id = destination.location_id

        WHERE i.product_id = ?
          AND source.location_type = 'warehouse'
          AND i.quantity > 0
          AND destination.location_type = 'store'
          AND LOWER(destination.location_name) = LOWER(?)
    """

    cursor.execute(
        query,
        (product_id, destination_store)
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)

def check_product_availability(product_id, destination_store=None):
    """
    Determine product availability using the store -> warehouse -> delivery workflow.

    If destination_store is specified:
        1. Check stock in that store.
        2. If unavailable there, check warehouse stock and transfer time
           to that store.

    If destination_store is None:
        1. Check stock in all stores.
        2. If the product is not in any store, check warehouse stock
           and transfer times to all stores.
    """

    # Step 1: check store stock
    store_stock = check_store_stock(
        product_id,
        store_name=destination_store
    )

    if store_stock and destination_store is not None:
        return {
            "status": "store_stock",
            "product_id": product_id,
            "stores": store_stock,
        }

    # Step 2: check warehouse stock
    warehouse_stock = check_warehouse_stock(product_id)

    if not warehouse_stock:
        return {
            "status": "unavailable",
            "product_id": product_id,
        }

    # Step 3: check warehouse-to-store transfer
    if destination_store is not None:
        delivery = get_delivery_time(
            product_id,
            destination_store
        )

        if delivery is None:
            return {
                "status": "warehouse_stock",
                "product_id": product_id,
                "warehouses": warehouse_stock,
                "delivery": None,
            }

        return {
            "status": "warehouse_delivery",
            "product_id": product_id,
            "warehouses": warehouse_stock,
            "delivery": delivery,
        }

    # No destination store specified:
    # check delivery routes to all stores
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = """
        SELECT
            p.product_id,
            source.location_name AS warehouse,
            destination.location_name AS destination,
            i.quantity,
            r.min_days,
            r.max_days
        FROM inventory i

        JOIN products p
            ON i.product_id = p.product_id

        JOIN locations source
            ON i.location_id = source.location_id

        JOIN delivery_routes r
            ON r.from_location_id = source.location_id

        JOIN locations destination
            ON r.to_location_id = destination.location_id

        WHERE i.product_id = ?
          AND source.location_type = 'warehouse'
          AND i.quantity > 0
          AND destination.location_type = 'store'
    """

    cursor.execute(query, (product_id,))

    deliveries = [dict(row) for row in cursor.fetchall()]

    connection.close()

    if not deliveries:
        return {
            "status": "warehouse_stock",
            "product_id": product_id,
            "warehouses": warehouse_stock,
            "delivery": [],
        }

    return {
        "status": "warehouse_delivery",
        "product_id": product_id,
        "warehouses": warehouse_stock,
        "delivery": deliveries,
    }

def compare_products(product_ids):
    """
    Compare multiple products by their specifications.

    Parameters:
        product_ids: list of product IDs, e.g.
            ["LAP0003", "LAP3706"]

    Returns:
        List of product details for comparison.
    """
    if not product_ids:
        return []

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    placeholders = ",".join("?" for _ in product_ids)

    query = f"""
        SELECT
            product_id,
            brand,
            product_name,
            price,
            processor,
            processor_brand,
            cpu_ghz,
            ram_gb,
            ram_max_gb,
            gpu_name,
            gpu_brand,
            gpu_vram_gb,
            ssd_gb,
            hdd_gb,
            display_inches,
            os
        FROM products
        WHERE product_id IN ({placeholders})
    """

    cursor.execute(query, product_ids)

    products = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return products