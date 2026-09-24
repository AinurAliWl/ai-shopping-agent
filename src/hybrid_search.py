import sqlite3
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from product_search import search_products
from query_parser import parse_query


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"

DB_PATH = DATABASE_DIR / "shop.db"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_short_directory_path(path):
    import ctypes

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
    if not product_ids:
        return []

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    placeholders = ",".join(
        "?" for _ in product_ids
    )

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

    cursor.execute(
        query,
        product_ids
    )

    products = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    products_by_id = {
        product["product_id"]: product
        for product in products
    }

    return [
        products_by_id[product_id]
        for product_id in product_ids
        if product_id in products_by_id
    ]


def semantic_search(
    query,
    candidate_ids,
    top_k=5
):
    """
    Run semantic search only on products
    that passed the structured SQL filters.
    """

    if not candidate_ids:
        return []

    model = SentenceTransformer(
        MODEL_NAME
    )

    index, product_ids = load_index()

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    # Search more candidates globally because
    # we will keep only IDs allowed by SQL.
    search_k = len(product_ids)

    scores, indices = index.search(
        query_embedding,
        search_k
    )

    candidate_ids = set(candidate_ids)

    results = []

    for score, index_position in zip(
        scores[0],
        indices[0]
    ):
        if index_position == -1:
            continue

        product_id = str(
            product_ids[index_position]
        )

        if product_id not in candidate_ids:
            continue

        results.append({
            "product_id": product_id,
            "score": float(score)
        })

        if len(results) >= top_k:
            break

    result_ids = [
        result["product_id"]
        for result in results
    ]

    products = get_products_by_ids(
        result_ids
    )

    products_by_id = {
        product["product_id"]: product
        for product in products
    }

    for result in results:
        result["product"] = products_by_id.get(
            result["product_id"]
        )

    return results


def hybrid_search(query, top_k=5):
    """
    Combine structured filtering and semantic search.
    """

    requirements = parse_query(query)

    print()
    print("=" * 70)
    print("EXTRACTED REQUIREMENTS")
    print("=" * 70)

    for key, value in requirements.items():
        print(f"{key}: {value}")

    # Step 1:
    # Exact filtering with SQLite.
    candidates = search_products(
        max_price=requirements["max_price"],
        min_ram=requirements["min_ram"],
        gpu_brand=requirements["gpu_brand"],
        min_ssd=requirements["min_ssd"],
        brand=requirements["brand"],
        os=requirements["os"],
        limit=1000
    )

    candidate_ids = [
        product["product_id"]
        for product in candidates
    ]

    print()
    print(f"SQL candidates: {len(candidate_ids)}")

    # Step 2:
    # Semantic ranking among valid candidates.
    results = semantic_search(
        requirements["semantic_query"],
        candidate_ids,
        top_k=top_k
    )

    return results

def hybrid_search_products(query, top_k=20):
    """
    Return hybrid search results as plain product dictionaries
    for the agent.
    """

    results = hybrid_search(
        query,
        top_k=top_k
    )

    products = []

    for result in results:
        product = result.get("product")

        if product is None:
            continue

        products.append(product)

    return products


def main():
    query = (
        "I need a laptop for machine learning, "
        "minimum 16 GB RAM, NVIDIA GPU, under $600"
    )

    print("=" * 70)
    print("HYBRID PRODUCT SEARCH")
    print("=" * 70)

    print()
    print(f"Query: {query}")

    results = hybrid_search(
        query,
        top_k=5
    )

    print()
    print("=" * 70)
    print("HYBRID SEARCH RESULTS")
    print("=" * 70)

    if not results:
        print()
        print("No matching products found.")
        return

    for rank, result in enumerate(
        results,
        start=1
    ):
        product = result["product"]

        print()
        print(f"#{rank}")
        print(
            f"Product ID: "
            f"{product['product_id']}"
        )
        print(
            f"Name: "
            f"{product['brand']} "
            f"{product['product_name']}"
        )
        print(
            f"Price: "
            f"${product['price']:.2f}"
        )
        print(
            f"CPU: "
            f"{product['processor']}"
        )
        print(
            f"RAM: "
            f"{product['ram_gb']} GB"
        )
        print(
            f"GPU: "
            f"{product['gpu_name']}"
        )
        print(
            f"SSD: "
            f"{product['ssd_gb']} GB"
        )
        print(
            f"Similarity: "
            f"{result['score']:.4f}"
        )


if __name__ == "__main__":
    main()