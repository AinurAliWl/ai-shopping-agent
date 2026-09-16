from product_search import get_delivery_time


product_id = "LAP0003"
destination = "Astana Mega Silk Way"


delivery = get_delivery_time(
    product_id,
    destination
)


print("=" * 60)
print("DELIVERY INFORMATION")
print("=" * 60)

if delivery is None:
    print("Delivery is not available.")
else:
    for key, value in delivery.items():
        print(f"{key}: {value}")