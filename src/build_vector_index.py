import ctypes
import sqlite3
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_DIR / "shop.db"
INDEX_PATH = DATABASE_DIR / "products.index"
IDS_PATH = DATABASE_DIR / "product_ids.npy"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_short_directory_path(path):
    """Convert an existing Windows directory path to its short 8.3 representation."""
    buffer = ctypes.create_unicode_buffer(1024)

    result = ctypes.windll.kernel32.GetShortPathNameW(
        str(path),
        buffer,
        len(buffer)
    )

    if result == 0:
        raise OSError(f"Failed to get short path for: {path}")

    return buffer.value


def load_products():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
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
    """)

    products = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return products


def product_to_text(product):
    return (
        f"{product['brand']} {product['product_name']}. "
        f"Processor: {product['processor']}. "
        f"Processor brand: {product['processor_brand']}. "
        f"RAM: {product['ram_gb']} GB. "
        f"Maximum RAM: {product['ram_max_gb']} GB. "
        f"GPU: {product['gpu_name']}. "
        f"GPU brand: {product['gpu_brand']}. "
        f"GPU VRAM: {product['gpu_vram_gb']} GB. "
        f"SSD: {product['ssd_gb']} GB. "
        f"HDD: {product['hdd_gb']} GB. "
        f"Display: {product['display_inches']} inches. "
        f"Operating system: {product['os']}. "
        f"Price: ${product['price']:.2f}."
    )


def main():
    print("Loading products...")

    products = load_products()

    print(f"Products loaded: {len(products)}")

    texts = [
        product_to_text(product)
        for product in products
    ]

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    print(f"Embeddings shape: {embeddings.shape}")

    print("Building FAISS index...")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print(f"FAISS index size: {index.ntotal}")

    product_ids = np.array(
        [product["product_id"] for product in products]
    )

    # Use Windows 8.3 paths to avoid Unicode path issues in FAISS.
    short_database_dir = get_short_directory_path(DATABASE_DIR)

    index_path = str(
        Path(short_database_dir) / "products.index"
    )

    ids_path = str(
        Path(short_database_dir) / "product_ids.npy"
    )

    print(f"Saving FAISS index to: {index_path}")
    faiss.write_index(index, index_path)

    print(f"Saving product IDs to: {ids_path}")
    np.save(ids_path, product_ids)

    print()
    print("=" * 60)
    print("VECTOR INDEX CREATED")
    print("=" * 60)
    print(f"Index: {INDEX_PATH}")
    print(f"Product IDs: {IDS_PATH}")
    print(f"Products indexed: {index.ntotal}")
    print(f"Embedding dimension: {dimension}")


if __name__ == "__main__":
    main()