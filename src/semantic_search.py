import ctypes
import sqlite3
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"

DB_PATH = DATABASE_DIR / "shop.db"
INDEX_PATH = DATABASE_DIR / "products.index"
IDS_PATH = DATABASE_DIR / "product_ids.npy"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_short_directory_path(path):
    buffer = ctypes.create_unicode_buffer(1024)

    result = ctypes.windll.kernel32.GetShortPathNameW(
        str(path),
        buffer,
        len(buffer)
    )

    if result == 0:
        raise OSError(f"Failed to get short path for: {path}")

    return buffer.value


def load_index():
    short_database_dir = get_short_directory_path(DATABASE_DIR)

    index_path = str(
        Path(short_database_dir) / "products.index"
    )

    ids_path = str(
        Path(short_database_dir) / "product_ids.npy"
    )

    index = faiss.read_index(index_path)
    product_ids = np.load(
        ids_path,
        allow_pickle=True
    )

    return index, product_ids


def get_products_by_ids(product_ids):
    if len(product_ids) == 0:
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

    cursor.execute(query, list(product_ids))

    products = [dict(row) for row in cursor.fetchall()]

    connection.close()

    # Preserve FAISS ranking order.
    products_by_id = {
        product["product_id"]: product
        for product in products
    }

    return [
        products_by_id[product_id]
        for product_id in product_ids
        if product_id in products_by_id
    ]


def semantic_search(query, top_k=5):
    print(f"Query: {query}")

    model = SentenceTransformer(MODEL_NAME)

    index, product_ids = load_index()

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, index_position in zip(
        scores[0],
        indices[0]
    ):
        if index_position == -1:
            continue

        product_id = product_ids[index_position]

        results.append({
            "product_id": str(product_id),
            "score": float(score)
        })

    result_ids = [
        result["product_id"]
        for result in results
    ]

    products = get_products_by_ids(result_ids)

    products_by_id = {
        product["product_id"]: product
        for product in products
    }

    for result in results:
        product = products_by_id.get(result["product_id"])

        if product:
            result["product"] = product

    return results


def main():
    query = "powerful gaming laptop with RTX 4070 and 32 GB RAM"

    results = semantic_search(
        query,
        top_k=5
    )

    print()
    print("=" * 70)
    print("SEMANTIC SEARCH RESULTS")
    print("=" * 70)

    for rank, result in enumerate(results, start=1):
        product = result["product"]

        print()
        print(f"#{rank}")
        print(f"Product ID: {product['product_id']}")
        print(f"Name: {product['brand']} {product['product_name']}")
        print(f"Price: ${product['price']:.2f}")
        print(f"CPU: {product['processor']}")
        print(f"RAM: {product['ram_gb']} GB")
        print(f"GPU: {product['gpu_name']}")
        print(f"SSD: {product['ssd_gb']} GB")
        print(f"Similarity: {result['score']:.4f}")


if __name__ == "__main__":
    main()