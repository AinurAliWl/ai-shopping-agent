from product_search import get_product_details


product_id = "LAP3706"

product = get_product_details(product_id)


print("=" * 60)
print("PRODUCT DETAILS")
print("=" * 60)

if product is None:
    print(f"Product {product_id} not found.")
else:
    for key, value in product.items():
        print(f"{key}: {value}")