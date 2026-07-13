"""
build_catalog.py

Builds a clean perfume catalog from fra_perfumes.csv (70K+ real Fragrantica
entries), ready for AED pricing/stock generation and LLM bilingual enrichment.
"""

import ast
import hashlib
import json
import random
import re
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/fra_perfumes.csv")
OUT_PATH = Path("data/processed/catalog_base.json")

CATEGORY_PRICE_BANDS_AED = {
    "niche": (450, 1200),
    "designer": (180, 450),
    "mass": (60, 180),
}

# Rough heuristic; refine later with a real brand-tier list if needed
NICHE_KEYWORDS = ["amouage", "xerjoff", "roja", "creed", "parfums de marly", "mfk", "byredo"]
MASS_KEYWORDS = ["axe", "adidas", "bath & body works", "avon"]

GENDER_MAP = {
    "for women": "women",
    "for men": "men",
    "for women and men": "unisex",
}


def clean_name(raw_name: str, gender_raw: str) -> str:
    if not isinstance(raw_name, str):
        return ""
    name = raw_name
    if isinstance(gender_raw, str) and gender_raw in name:
        name = name.split(gender_raw)[0]
    return name.strip()


def parse_accords(raw: str) -> list[str]:
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        parsed = ast.literal_eval(raw)
        return [str(a).strip() for a in parsed if str(a).strip()]
    except (ValueError, SyntaxError):
        return []


def infer_category(name: str) -> str:
    n = name.lower()
    if any(k in n for k in NICHE_KEYWORDS):
        return "niche"
    if any(k in n for k in MASS_KEYWORDS):
        return "mass"
    return "designer"


def deterministic_value(seed_str: str, low: float, high: float, is_int: bool = False):
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % 10_000
    rng = random.Random(seed)
    val = rng.uniform(low, high)
    return int(val) if is_int else round(val, 2)


def extract_notes(description: str) -> dict[str, list[str]]:
    """Best-effort extraction of top/middle/base notes from the description sentence."""
    result = {"top": [], "middle": [], "base": []}
    if not isinstance(description, str):
        return result
    patterns = {
        "top": r"[Tt]op notes are ([^;.]+)",
        "middle": r"middle notes are ([^;.]+)",
        "base": r"base notes are ([^;.]+)",
    }
    for section, pattern in patterns.items():
        m = re.search(pattern, description)
        if m:
            raw = m.group(1)
            raw = raw.replace(" and ", ", ")
            result[section] = [n.strip() for n in raw.split(",") if n.strip()]
    return result


def build_catalog(sample_size: int = 100) -> list[dict]:
    df = pd.read_csv(RAW_PATH)
    df["Rating Value"] = pd.to_numeric(df["Rating Value"], errors="coerce")
    df["Rating Count"] = pd.to_numeric(df["Rating Count"], errors="coerce")

    df = df.dropna(subset=["Name", "Gender", "Description"])
    df = df[df["Rating Count"].fillna(0) >= 50]
    df = df[df["Description"].str.contains("notes are", case=False, na=False)]
    df = df.sample(frac=1.0, random_state=42)
    ...

    catalog = []
    for _, r in df.iterrows():
        name = clean_name(r["Name"], r["Gender"])
        if not name:
            continue

        item_id = "PF" + hashlib.sha256(name.encode()).hexdigest()[:8].upper()
        category = infer_category(name)
        band = CATEGORY_PRICE_BANDS_AED[category]

        catalog.append({
            "item_id": item_id,
            "name_en": name,
            "gender": GENDER_MAP.get(r["Gender"], "unisex"),
            "rating": float(r["Rating Value"]) if pd.notna(r["Rating Value"]) and str(r["Rating Value"]).replace(".", "", 1).isdigit() else None,
            "reviews_count": int(r["Rating Count"]) if pd.notna(r["Rating Count"]) else 0,
            "main_accords": parse_accords(r["Main Accords"]),
            "notes": extract_notes(r["Description"]),
            "description_en_raw": str(r["Description"]).strip(),
            "category": category,
            "price_aed": deterministic_value(item_id, *band),
            "quantity_in_stock": deterministic_value(item_id + "stock", 0, 40, is_int=True),
            "source_url": r["url"],
        })

        if len(catalog) >= sample_size:
            break

    return catalog


def main():
    catalog = build_catalog(sample_size=100)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(catalog)} records to {OUT_PATH}")
    print("\n--- Sample record ---")
    print(json.dumps(catalog[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()