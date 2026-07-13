"""
seed_database.py

Loads data/processed/catalog_enriched.json into the products table.
Safe to re-run: upserts by item_id instead of duplicating rows.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import logging
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.database import SessionLocal, engine
from app.db.models import Product, Base

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("seed_database")

CATALOG_PATH = Path("data/processed/catalog_enriched.json")


def load_catalog() -> list[dict]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"{CATALOG_PATH} not found. Run build_catalog.py and enrich_catalog.py first."
        )
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def to_product_row(item: dict) -> dict:
    return {
        "item_id": item["item_id"],
        "brand": item.get("brand", ""),
        "name_en": item["name_en"],
        "name_ar": item.get("name_ar"),
        "gender": item.get("gender"),
        "main_accords": item.get("main_accords", []),
        "notes": item.get("notes", {}),
        "description_en": item.get("description_en_raw", ""),
        "description_ar": item.get("description_ar"),
        "category": item.get("category"),
        "price_aed": item["price_aed"],
        "quantity_in_stock": item["quantity_in_stock"],
        "rating": item.get("rating"),
        "reviews_count": item.get("reviews_count", 0),
        "source_url": item.get("source_url"),
    }


def seed(catalog: list[dict]) -> None:
    rows = [to_product_row(item) for item in catalog]

    with SessionLocal() as db:
        for row in rows:
            stmt = pg_insert(Product).values(**row)
            update_cols = {k: v for k, v in row.items() if k != "item_id"}
            stmt = stmt.on_conflict_do_update(
                index_elements=["item_id"],
                set_=update_cols,
            )
            db.execute(stmt)
        db.commit()

    log.info(f"Seeded/updated {len(rows)} products")


def verify() -> None:
    with SessionLocal() as db:
        count = db.query(Product).count()
        sample = db.query(Product).first()
        log.info(f"Total products in DB: {count}")
        if sample:
            log.info(f"Sample: {sample.brand} — {sample.name_en} ({sample.price_aed} AED)")


def main():
    Base.metadata.create_all(bind=engine)  # no-op if tables already exist via Alembic
    catalog = load_catalog()
    log.info(f"Loaded {len(catalog)} records from {CATALOG_PATH}")
    seed(catalog)
    verify()


if __name__ == "__main__":
    main()
