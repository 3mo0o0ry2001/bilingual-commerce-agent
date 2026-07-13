import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.graph import build_graph

graph = build_graph()

test_requests = [
    "عايز اشتري عطر مرسيدس بنز",       # Arabic + brand → semantic match
    "I want to buy Her Code",           # English exact
    "اشتري لي كاساندرا بلو",            # Arabic transliteration
    "do you have any woody perfumes under 400 AED?",  # search
    "can you gift wrap my order?",      # unsupported
]

for req in test_requests:
    print("=" * 60)
    print("Request:", req)
    result = graph.invoke({
        "user_request": req,
        "customer_phone": "+971500000000",
        "filters": {},
        "requested_items": [],
        "matched_products": [],
        "order_items": [],
    })
    print("Intent:", result.get("intent"), "| Status:", result.get("status"))
    print("Answer:", result.get("answer_text"))
    print()