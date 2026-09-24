from product_search import check_product_availability


PRODUCT_ID = "LAP0279"


print("=" * 60)
print("SPECIFIC STORE: ASTANA MEGA SILK WAY")
print("=" * 60)

result = check_product_availability(
    PRODUCT_ID,
    "Astana Mega Silk Way"
)

print(result)


print("\n" + "=" * 60)
print("SPECIFIC STORE: ASTANA KHAN SHATYR")
print("=" * 60)

result = check_product_availability(
    PRODUCT_ID,
    "Astana Khan Shatyr"
)

print(result)


print("\n" + "=" * 60)
print("NO STORE SPECIFIED")
print("=" * 60)

result = check_product_availability(
    PRODUCT_ID
)

print(result)