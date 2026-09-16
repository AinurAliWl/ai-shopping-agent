from product_search import search_products


# Test scenario:
# Laptop for ML
# Budget: up to $1000
# RAM: at least 16 GB
# GPU: NVIDIA

results = search_products(
    max_price=1000,
    min_ram=16,
    gpu_brand="NVIDIA",
)


print("=" * 60)
print("SEARCH RESULTS")
print("=" * 60)

print(f"Found: {len(results)} products")
print()


for product in results:
    print(
        f"{product['product_id']} | "
        f"{product['brand']} {product['product_name']} | "
        f"${product['price']:.2f} | "
        f"RAM: {product['ram_gb']:.0f} GB | "
        f"GPU: {product['gpu_name']}"
    )