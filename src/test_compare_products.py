from product_search import compare_products


product_ids = [
    "LAP0003",
    "LAP3706",
]

products = compare_products(product_ids)

print("=" * 60)
print("PRODUCT COMPARISON")
print("=" * 60)

for product in products:
    print()
    print(f"ID: {product['product_id']}")
    print(f"Name: {product['brand']} {product['product_name']}")
    print(f"Price: ${product['price']:.2f}")
    print(f"CPU: {product['processor']}")
    print(f"RAM: {product['ram_gb']} GB")
    print(f"GPU: {product['gpu_name']}")
    print(f"SSD: {product['ssd_gb']} GB")
    print(f"Display: {product['display_inches']} inches")
    print(f"OS: {product['os']}")