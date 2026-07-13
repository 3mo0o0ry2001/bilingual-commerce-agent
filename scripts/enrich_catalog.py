"""
enrich_catalog.py

Takes data/processed/catalog_base.json (real Fragrantica data, AED priced)
and enriches each perfume via LLM:
  - splits the brand name out of the raw combined name_en
  - generates a natural Arabic name (Gulf/MSA style)
  - generates a short, warm Arabic product description for WhatsApp

Requirements: openai, python-dotenv, tqdm
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("enrich_catalog")

client = OpenAI()

ENRICH_SYSTEM_PROMPT = """You are a bilingual (Arabic/English) copywriter for a Gulf perfume e-commerce store.

For each perfume in the input list, the "raw_name" field combines the perfume name and the brand name
with no clear separator (e.g., "La Nuit de l'Homme Frozen Cologne Yves Saint Laurent" means brand =
"Yves Saint Laurent", name = "La Nuit de l'Homme Frozen Cologne"). Use your knowledge of real perfume
brands to split them correctly.

For each perfume, produce:
- "brand": the correctly isolated brand name (English)
- "name_en_clean": the perfume name alone, without the brand (English)
- "name_ar": a natural Gulf/MSA Arabic rendering of the perfume name (transliterate proper nouns naturally,
  translate descriptive words where it reads better in Arabic)
- "description_ar": a warm, natural 1-2 sentence Arabic product description suited for a WhatsApp customer
  message, evoking the scent profile. Not a literal translation of the English description.

Return ONLY a JSON array, same order as input, each item:
{"item_id": "...", "brand": "...", "name_en_clean": "...", "name_ar": "...", "description_ar": "..."}
No extra text, no markdown fences."""


def enrich_batch(batch: list[dict[str, Any]], model: str, max_retries: int = 3) -> dict[str, dict[str, str]]:
    payload = [
        {
            "item_id": item["item_id"],
            "raw_name": item["name_en"],
            "main_accords": item["main_accords"][:5],
            "description_en": item["description_en_raw"][:400],
        }
        for item in batch
    ]

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(raw)
            return {item["item_id"]: item for item in parsed}
        except Exception as e:
            log.warning(f"Enrich batch attempt {attempt} failed: {e}")
            time.sleep(2 * attempt)

    log.error(f"Batch failed after {max_retries} attempts, skipping {[b['item_id'] for b in batch]}")
    return {}


def enrich_all(catalog: list[dict[str, Any]], model: str, batch_size: int = 5) -> list[dict[str, Any]]:
    batches = [catalog[i:i + batch_size] for i in range(0, len(catalog), batch_size)]
    enriched_map: dict[str, dict[str, str]] = {}

    for batch in tqdm(batches, desc="Enriching batches"):
        enriched_map.update(enrich_batch(batch, model=model))
        time.sleep(0.5)

    results = []
    missing = 0
    for item in catalog:
        extra = enriched_map.get(item["item_id"])
        if not extra:
            missing += 1
            extra = {}

        merged = dict(item)
        merged["brand"] = extra.get("brand", "")
        merged["name_en"] = extra.get("name_en_clean", item["name_en"])
        merged["name_ar"] = extra.get("name_ar")
        merged["description_ar"] = extra.get("description_ar")
        results.append(merged)

    if missing:
        log.warning(f"{missing} items missing enrichment (kept with null Arabic fields)")

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/processed/catalog_base.json"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/catalog_enriched.json"))
    parser.add_argument("--model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--batch-size", type=int, default=5)
    args = parser.parse_args()

    catalog = json.loads(args.input.read_text(encoding="utf-8"))
    log.info(f"Loaded {len(catalog)} base records from {args.input}")

    enriched = enrich_all(catalog, model=args.model, batch_size=args.batch_size)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Saved {len(enriched)} enriched records to {args.output}")

    print("\n--- Sample enriched record ---")
    print(json.dumps(enriched[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()