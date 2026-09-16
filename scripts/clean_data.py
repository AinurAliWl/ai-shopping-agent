import pandas as pd
import numpy as np
import re


# ============================================================
# 1. LOAD DATA
# ============================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data"

INPUT_FILE = DATASET_DIR / "laptop.csv"
OUTPUT_FILE = DATASET_DIR / "laptops_clean.csv"

df = pd.read_csv(INPUT_FILE)

print("=" * 60)
print("ORIGINAL DATA")
print("=" * 60)
print("Shape:", df.shape)
print("Columns:", list(df.columns))


# ============================================================
# 2. BASIC CLEANING
# ============================================================

# Remove old Kaggle index
if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

# Strip whitespace from all string cells
for col in df.select_dtypes(include=["str", "object"]).columns:
    df[col] = df[col].astype(str).str.strip()

# Convert common missing-value strings to NaN
MISSING_VALUES = {
    "",
    "nan",
    "NaN",
    "none",
    "None",
    "null",
    "NULL",
    "N/A",
    "n/a",
    "-"
}

for col in df.select_dtypes(include=["str", "object"]).columns:
    df[col] = df[col].replace(list(MISSING_VALUES), np.nan)


# ============================================================
# 3. PRODUCT NAME
# ============================================================

# Keep the original name before modifying it
df["raw_name"] = df["Name"]

# Some names contain "::"
# Keep only the actual product name before "::"
df["product_name"] = (
    df["Name"]
    .astype(str)
    .str.split("::")
    .str[0]
    .str.strip()
)

# Restore NaN if Name was missing
df.loc[df["Name"].isna(), "product_name"] = np.nan


# ============================================================
# 4. BRAND
# ============================================================

def normalize_brand(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    mapping = {
        "hp": "HP",
        "lenovo": "Lenovo",
        "dell": "Dell",
        "asus": "ASUS",
        "acer": "Acer",
        "msi": "MSI",
        "apple": "Apple",
        "samsung": "Samsung",
        "lg": "LG",
        "microsoft": "Microsoft",
        "xiaomi": "Xiaomi",
        "huawei": "Huawei",
        "avita": "Avita",
        "realme": "Realme",
        "infinix": "Infinix",
        "chuwi": "Chuwi",
        "fujitsu": "Fujitsu",
        "toshiba": "Toshiba",
    }

    return mapping.get(value.lower(), value)


df["brand"] = df["Brand"].apply(normalize_brand)


# ============================================================
# 5. PRICE
# ============================================================

# The source dataset uses Indian Rupees (INR).
# Convert prices to USD for the project.
INR_PER_USD = 95.9


def parse_price(value):
    if pd.isna(value):
        return np.nan

    value = str(value)

    # Keep digits and decimal separator
    value = re.sub(r"[^\d.]", "", value)

    if not value:
        return np.nan

    try:
        price_inr = float(value)

        # Convert INR → USD
        price_usd = price_inr / INR_PER_USD

        return round(price_usd, 2)

    except ValueError:
        return np.nan


df["price"] = df["Price"].apply(parse_price)


# ============================================================
# 6. PROCESSOR
# ============================================================

df["processor"] = df["Processor_Name"].astype("string").str.strip()


# ============================================================
# 7. PROCESSOR BRAND
# ============================================================

def normalize_processor_brand(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    mapping = {
        "intel": "Intel",
        "amd": "AMD",
        "apple": "Apple",
        "mediatek": "MediaTek",
        "qualcomm": "Qualcomm",
    }

    return mapping.get(value, value.title())


df["processor_brand"] = df["Processor_Brand"].apply(
    normalize_processor_brand
)

# Some rows in the source dataset have shifted processor fields.
# In these rows:
# Processor_Name contains the CPU frequency,
# Processor_Brand contains the frequency,
# Ghz contains 0.
#
# Recover the correct values from the product name and shifted fields.

def recover_processor_brand(product_name):
    if pd.isna(product_name):
        return np.nan

    text = str(product_name).lower()

    if "apple m1" in text or "apple m2" in text or "apple m3" in text:
        return "Apple"

    if "amd" in text or "ryzen" in text or "apu" in text:
        return "AMD"

    if any(x in text for x in ["intel", "core i3", "core i5", "core i7",
                               "core i9", "pentium", "celeron"]):
        return "Intel"

    return np.nan


shifted_processor = (
    df["Processor_Brand"]
    .astype(str)
    .str.match(r"^\d+(?:\.\d+)?$", na=False)
)

df.loc[shifted_processor, "processor_brand"] = (
    df.loc[shifted_processor, "Name"]
    .apply(recover_processor_brand)
)

df.loc[shifted_processor, "cpu_ghz"] = (
    df.loc[shifted_processor, "Processor_Brand"]
    .astype(str)
    .str.extract(r"(\d+(?:\.\d+)?)")[0]
    .astype(float)
)



# ============================================================
# 8. CPU FREQUENCY
# ============================================================

def parse_ghz(value):
    if pd.isna(value):
        return np.nan

    match = re.search(r"(\d+(?:\.\d+)?)", str(value))

    if not match:
        return np.nan

    ghz = float(match.group(1))

    # Dataset contains 0 as a placeholder
    if ghz <= 0:
        return np.nan

    return ghz


df["cpu_ghz"] = df["Ghz"].apply(parse_ghz)


# 8.1 FIX SHIFTED PROCESSOR DATA
# Some source rows have processor information shifted:
# Processor_Name contains GHz,
# Processor_Brand contains the numeric GHz,
# Ghz contains 0.
shifted_processor = df["Processor_Brand"].astype(str).str.fullmatch(
    r"\d+(?:\.\d+)?",
    na=False
)


def extract_cpu_from_product_name(value):
    if pd.isna(value):
        return np.nan

    product = str(value).split("::")[0]

    if "(" not in product:
        return np.nan

    details = product.split("(", 1)[1]
    parts = [part.strip() for part in details.split("|")]

    if len(parts) >= 2:
        return parts[1]

    return np.nan


def infer_processor_brand(processor_text):
    if pd.isna(processor_text):
        return np.nan

    text = str(processor_text).lower()

    if any(x in text for x in [
        "intel",
        "core i3",
        "core i5",
        "core i7",
        "core i9",
        "pentium",
        "celeron",
    ]):
        return "Intel"

    if any(x in text for x in [
        "amd",
        "ryzen",
        "apu",
    ]):
        return "AMD"

    if "apple" in text or re.search(r"\bm[123]\b", text):
        return "Apple"

    if "mediatek" in text:
        return "MediaTek"

    if "qualcomm" in text:
        return "Qualcomm"

    return np.nan


recovered_processor = df.loc[
    shifted_processor, "Name"
].apply(extract_cpu_from_product_name)

df.loc[shifted_processor, "processor"] = recovered_processor

df.loc[shifted_processor, "processor_brand"] = recovered_processor.apply(
    infer_processor_brand
)

df.loc[shifted_processor, "cpu_ghz"] = pd.to_numeric(
    df.loc[shifted_processor, "Processor_Brand"],
    errors="coerce"
)

# ============================================================
# 9. RAM
# ============================================================

def parse_ram(value):
    if pd.isna(value):
        return np.nan

    match = re.search(r"(\d+(?:\.\d+)?)", str(value))

    if not match:
        return np.nan

    return float(match.group(1))


df["ram_gb"] = df["RAM"].apply(parse_ram)


# ============================================================
# 10. RAM EXPANDABILITY
# ============================================================

def parse_ram_expandable(value):
    if pd.isna(value):
        return False

    value = str(value).lower()

    if "not expandable" in value:
        return False

    if "expandable" in value:
        return True

    return False


df["ram_expandable"] = df["RAM_Expandable"].apply(
    parse_ram_expandable
)


# ============================================================
# 11. MAX RAM
# ============================================================

def parse_ram_max(row):
    current_ram = row["ram_gb"]
    expandable = row["ram_expandable"]
    raw_value = row["RAM_Expandable"]

    if pd.isna(current_ram):
        return np.nan

    # If RAM cannot be expanded,
    # maximum RAM = current RAM
    if not expandable:
        return current_ram

    if pd.isna(raw_value):
        return current_ram

    match = re.search(r"(\d+(?:\.\d+)?)", str(raw_value))

    if match:
        max_ram = float(match.group(1))

        # Sanity check
        if max_ram >= current_ram:
            return max_ram

    return current_ram


df["ram_max_gb"] = df.apply(parse_ram_max, axis=1)


# ============================================================
# 12. RAM TYPE
# ============================================================

df["ram_type"] = (
    df["RAM_TYPE"]
    .astype("string")
    .str.strip()
    .str.upper()
)


# ============================================================
# 13. DISPLAY TYPE
# ============================================================

def parse_display_type(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    mapping = {
        "led": "LED",
        "ips": "IPS",
        "oled": "OLED",
        "amoled": "AMOLED",
        "tn": "TN",
        "retina": "Retina",
        "lcd": "LCD",
    }

    for key, normalized in mapping.items():
        if key in value:
            return normalized

    return str(value).strip()


df["display_type"] = df["Display_type"].apply(
    parse_display_type
)


# ============================================================
# 14. DISPLAY SIZE
# ============================================================

def parse_display_inches(value):
    if pd.isna(value):
        return np.nan

    match = re.search(r"(\d+(?:\.\d+)?)", str(value))

    if not match:
        return np.nan

    inches = float(match.group(1))

    # Basic sanity check
    if 5 <= inches <= 30:
        return inches

    return np.nan


df["display_inches"] = df["Display"].apply(
    parse_display_inches
)


# ============================================================
# 15. GPU NAME
# ============================================================

df["gpu_name"] = (
    df["GPU"]
    .astype("string")
    .str.strip()
)


# ============================================================
# 16. GPU BRAND
# ============================================================

def normalize_gpu_brand(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    mapping = {
        "intel": "Intel",
        "nvidia": "NVIDIA",
        "nividia": "NVIDIA",   # typo in source dataset
        "amd": "AMD",
        "ati": "AMD",          # old AMD/ATI naming
        "apple": "Apple",
        "mediatek": "MediaTek",
        "qualcomm": "Qualcomm",
        "arm": "Arm",
        "microsoft": "Microsoft",
    }

    return mapping.get(value, value.title())


df["gpu_brand"] = df["GPU_Brand"].apply(
    normalize_gpu_brand
)


# ============================================================
# 17. GPU VRAM
# ============================================================

def parse_vram(value):
    if pd.isna(value):
        return np.nan

    text = str(value).lower()

    # Examples:
    # 4 GB
    # 6GB
    # 8 gb
    match = re.search(r"(\d+(?:\.\d+)?)\s*gb", text)

    if match:
        return float(match.group(1))

    return np.nan


df["gpu_vram_gb"] = df["GPU"].apply(parse_vram)


# ============================================================
# 18. STORAGE
# ============================================================

def parse_storage(value):
    if pd.isna(value):
        return 0.0

    text = str(value).lower().strip()

    # Explicitly no storage of this type
    if "no ssd" in text or "no hdd" in text:
        return 0.0

    # TB → GB
    tb_match = re.search(r"(\d+(?:\.\d+)?)\s*tb", text)

    if tb_match:
        return float(tb_match.group(1)) * 1024

    # GB
    gb_match = re.search(r"(\d+(?:\.\d+)?)\s*gb", text)

    if gb_match:
        return float(gb_match.group(1))

    # Plain number
    number_match = re.search(r"(\d+(?:\.\d+)?)", text)

    if number_match:
        return float(number_match.group(1))

    return 0.0


df["ssd_gb"] = df["SSD"].apply(parse_storage)
df["hdd_gb"] = df["HDD"].apply(parse_storage)


# ============================================================
# 19. ADAPTER POWER
# ============================================================

def parse_adapter(value):
    if pd.isna(value):
        return np.nan

    text = str(value).lower()

    # Do not confuse "battery life" values with adapter values
    if "no" in text:
        return np.nan

    match = re.search(r"(\d+(?:\.\d+)?)", text)

    if not match:
        return np.nan

    watt = float(match.group(1))

    # Sanity check for laptop adapters
    if 20 <= watt <= 500:
        return watt

    return np.nan


df["adapter_w"] = df["Adapter"].apply(parse_adapter)


# ============================================================
# 20. BATTERY LIFE
# ============================================================

def parse_battery_hours(value):
    if pd.isna(value):
        return np.nan

    text = str(value).lower().strip()

    # Some rows are incorrectly shifted and contain adapter info
    if "adapter" in text or "w" in text and "hr" not in text:
        return np.nan

    # Examples:
    # Upto 12 Hrs
    # 10 Hrs
    # Up to 7.5 Hours

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:hrs?|hours?)",
        text
    )

    if match:
        hours = float(match.group(1))

        if 0 < hours <= 50:
            return hours

    return np.nan


df["battery_hours"] = df["Battery_Life"].apply(
    parse_battery_hours
)


# ============================================================
# 21. OPERATING SYSTEM
# ============================================================

def parse_os(row):
    text = " ".join(
        str(row[col])
        for col in ["Name", "product_name"]
        if not pd.isna(row[col])
    ).lower()

    # Order matters
    if "chrome os" in text or "chromebook" in text:
        return "Chrome OS"

    if "windows 11" in text:
        return "Windows 11"

    if "windows 10" in text:
        return "Windows 10"

    if "macos" in text or "mac os" in text:
        return "macOS"

    if "linux" in text:
        return "Linux"

    if "dos" in text:
        return "DOS"

    return np.nan


df["os"] = df.apply(parse_os, axis=1)


# ============================================================
# 22. PRODUCT ID
# ============================================================

# Create stable IDs after cleaning
df.insert(
    0,
    "product_id",
    [
        f"LAP{i:04d}"
        for i in range(1, len(df) + 1)
    ]
)


# ============================================================
# 23. REMOVE DUPLICATES
# ============================================================

before_duplicates = len(df)

# Product identity based on meaningful product fields
duplicate_columns = [
    "brand",
    "product_name",
    "price",
    "processor",
    "ram_gb",
    "ram_max_gb",
    "gpu_name",
    "ssd_gb",
    "hdd_gb"
]

df = df.drop_duplicates(
    subset=duplicate_columns,
    keep="first"
).reset_index(drop=True)

duplicates_removed = before_duplicates - len(df)

# Recreate IDs after duplicate removal
df["product_id"] = [
    f"LAP{i:04d}"
    for i in range(1, len(df) + 1)
]


# ============================================================
# 24. FINAL COLUMN ORDER
# ============================================================

final_columns = [
    "product_id",
    "brand",
    "product_name",
    "price",
    "processor",
    "processor_brand",
    "cpu_ghz",
    "ram_gb",
    "ram_expandable",
    "ram_max_gb",
    "ram_type",
    "display_type",
    "display_inches",
    "gpu_name",
    "gpu_brand",
    "gpu_vram_gb",
    "ssd_gb",
    "hdd_gb",
    "adapter_w",
    "battery_hours",
    "os",
    "raw_name"
]

df = df[final_columns]


# ============================================================
# 25. NUMERIC TYPES
# ============================================================

numeric_columns = [
    "price",
    "cpu_ghz",
    "ram_gb",
    "ram_max_gb",
    "display_inches",
    "gpu_vram_gb",
    "ssd_gb",
    "hdd_gb",
    "adapter_w",
    "battery_hours"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ============================================================
# 26. SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 27. REPORT
# ============================================================

print()
print("=" * 60)
print("CLEANING COMPLETE")
print("=" * 60)

print("Original rows:", before_duplicates)
print("Duplicates removed:", duplicates_removed)
print("Final rows:", len(df))
print("Final columns:", len(df.columns))

print()
print("FINAL COLUMNS:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2}. {col}")

print()
print("MISSING VALUES:")
print(df.isna().sum())

print()
print("RAM EXPANDABILITY:")
print(df["ram_expandable"].value_counts(dropna=False))

print()
print("OPERATING SYSTEM:")
print(df["os"].value_counts(dropna=False))

print()
print("GPU BRANDS:")
print(df["gpu_brand"].value_counts(dropna=False))

print()
print("FIRST 10 ROWS:")
print(df.head(10).to_string())

print()
print("=" * 60)
print(f"Saved to: {OUTPUT_FILE}")
print("=" * 60)