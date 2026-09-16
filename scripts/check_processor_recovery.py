import pandas as pd
from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "laptop.csv"

df = pd.read_csv(INPUT_FILE)


def extract_cpu_from_name(value):
    if pd.isna(value):
        return None

    product = str(value).split("::")[0]

    if "(" not in product:
        return None

    details = product.split("(", 1)[1]
    parts = [part.strip() for part in details.split("|")]

    if len(parts) >= 2:
        return parts[1]

    return None


def infer_processor_brand(processor_text):
    if pd.isna(processor_text):
        return None

    text = str(processor_text).lower()

    if any(x in text for x in [
        "intel",
        "core i3",
        "core i5",
        "core i7",
        "core i9",
        "pentium",
        "celeron"
    ]):
        return "Intel"

    if any(x in text for x in [
        "amd",
        "ryzen",
        "apu"
    ]):
        return "AMD"

    if "apple" in text or re.search(r"\bm[123]\b", text):
        return "Apple"

    if "mediatek" in text:
        return "MediaTek"

    if "qualcomm" in text:
        return "Qualcomm"

    return None


# Find corrupted rows
bad = df[
    df["Processor_Brand"]
    .astype(str)
    .str.fullmatch(r"\d+(?:\.\d+)?", na=False)
].copy()

print("=" * 100)
print(f"Suspicious rows: {len(bad)}")
print("=" * 100)

for index, row in bad.iterrows():

    recovered_cpu = extract_cpu_from_name(row["Name"])
    recovered_brand = infer_processor_brand(recovered_cpu)

    recovered_ghz = float(row["Processor_Brand"])

    print(f"\nROW {index}")
    print(f"Product:          {row['Name']}")
    print(f"Old processor:    {row['Processor_Name']}")
    print(f"Old brand:        {row['Processor_Brand']}")
    print(f"Old GHz:          {row['Ghz']}")
    print(f"Recovered CPU:    {recovered_cpu}")
    print(f"Recovered brand:  {recovered_brand}")
    print(f"Recovered GHz:    {recovered_ghz}")