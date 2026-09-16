from product_search import (
    check_store_stock,
    check_warehouse_stock,
)


product_id = "LAP0003"


print("=" * 60)
print("STORE STOCK")
print("=" * 60)

stores = check_store_stock(product_id)

for store in stores:
    print(
        f"{store['location_name']} | "
        f"Quantity: {store['quantity']}"
    )


print()
print("=" * 60)
print("WAREHOUSE STOCK")
print("=" * 60)

warehouses = check_warehouse_stock(product_id)

for warehouse in warehouses:
    print(
        f"{warehouse['location_name']} | "
        f"Quantity: {warehouse['quantity']}"
    )