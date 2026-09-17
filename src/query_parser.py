import re


def parse_query(query):
    """
    Extract structured requirements from a natural-language query.
    """

    text = query.lower()

    requirements = {
        "max_price": None,
        "min_ram": None,
        "min_ssd": None,
        "gpu_brand": None,
        "brand": None,
        "os": None,
        "semantic_query": query,
    }

    # RAM
    ram_match = re.search(
        r"(?:at least|min(?:imum)?|>=?)\s*(\d+)\s*gb\s*(?:ram|memory)"
        r"|(\d+)\s*gb\s*(?:of\s*)?(?:ram|memory)",
        text
    )

    if ram_match:
        value = next(
            group for group in ram_match.groups()
            if group is not None
        )
        requirements["min_ram"] = int(value)

    # SSD
    ssd_match = re.search(
        r"(?:at least|min(?:imum)?|>=?)\s*(\d+)\s*gb\s*ssd"
        r"|(\d+)\s*gb\s*ssd",
        text
    )

    if ssd_match:
        value = next(
            group for group in ssd_match.groups()
            if group is not None
        )
        requirements["min_ssd"] = int(value)

    # NVIDIA
    if "nvidia" in text:
        requirements["gpu_brand"] = "NVIDIA"

    # AMD
    elif re.search(r"\bamd\b|radeon|ryzen", text):
        requirements["gpu_brand"] = "AMD"

    # Apple
    elif "apple" in text:
        requirements["gpu_brand"] = "Apple"

    # Price in USD
    price_match = re.search(
        r"(?:under|below|less than|up to|max(?:imum)?)\s*\$?\s*([\d,]+)",
        text
    )

    if price_match:
        value = price_match.group(1).replace(",", "")
        requirements["max_price"] = float(value)

    # Brand
    brands = [
        "asus",
        "lenovo",
        "dell",
        "hp",
        "msi",
        "acer",
        "apple",
    ]

    for brand in brands:
        if re.search(rf"\b{brand}\b", text):
            requirements["brand"] = brand.title()
            break

    # OS
    if "windows 11" in text:
        requirements["os"] = "Windows 11"
    elif "windows 10" in text:
        requirements["os"] = "Windows 10"
    elif "macos" in text or "mac os" in text:
        requirements["os"] = "macOS"
    elif "linux" in text:
        requirements["os"] = "Linux"

    return requirements


def main():
    query = (
        "I need a laptop for machine learning, "
        "minimum 16 GB RAM, NVIDIA GPU, under $600"
    )

    requirements = parse_query(query)

    print("=" * 60)
    print("QUERY")
    print("=" * 60)
    print(query)

    print()
    print("=" * 60)
    print("EXTRACTED REQUIREMENTS")
    print("=" * 60)

    for key, value in requirements.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()