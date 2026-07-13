import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.search.semantic_search import semantic_search

# عطور موجودة فعلاً، بس مكتوبة بصيغ مختلفة عن المخزّن
queries = [
    "بلاد سوفاج",        # Balade Sauvage (تعريب مختلف)
    "مرسيدس بنز",        # Mercedes Benz Club Extreme (جزء من الاسم)
    "her code",          # إنجليزي lowercase
    "كاساندرا بلو",      # Cassandra Bleu
    "عطر مرسيدس",        # وصف + ماركة
    "eternity men",      # جزء من Eternity For Men
]

for q in queries:
    print("=" * 50)
    print("Query:", q)
    results = semantic_search(q, top_k=3, max_distance=2.0)  # عتبة مفتوحة للتشخيص
    for r in results:
        flag = "✓" if r["distance"] <= 0.85 else " "
        print(f"  [{flag}] {r['distance']:.3f} | {r['name_en']} | {r['name_ar']}")
    print()