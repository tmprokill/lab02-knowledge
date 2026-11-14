import json
import os
import sys
from pathlib import Path

# Додаємо корінь проєкту в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kb.embedder import KnowledgeEmbedder
from kb.store import KnowledgeStore


def evaluate_retrieval(eval_path: str = "eval/retrieval_set.json", max_distance: float = 0.28):
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with open(eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    store = KnowledgeStore()
    embedder = KnowledgeEmbedder()

    hits = 0
    rr_total = 0.0
    in_domain_count = 0
    false_accepts = 0

    print(f"=== Оцінювання пошуку з порогом KB_MAX_DISTANCE = {max_distance} ===")

    for item in data:
        qid = item["id"]
        query = item["query"]
        is_in = item["is_in_domain"]

        q_vec = embedder.embed([query], task_type="retrieval_query")[0]
        results = store.query(q_vec, n_results=4)

        # Фільтрація за порогом відстані
        valid_results = [r for r in results if r["distance"] <= max_distance]

        if is_in:
            in_domain_count += 1
            expected_ref = item["relevant_reference"]
            expected_note = item["expected_note"]

            found_rank = None
            for rank, r in enumerate(valid_results, start=1):
                ref = r["metadata"].get("reference", "")
                rel_path = r["metadata"].get("rel_path", "")
                if expected_ref == ref or expected_note == rel_path:
                    found_rank = rank
                    break

            if found_rank is not None:
                hits += 1
                rr_total += (1.0 / found_rank)
                print(f"[{qid}] PASS (Rank {found_rank}): {query[:50]}...")
            else:
                top_dist = valid_results[0]["distance"] if valid_results else (results[0]["distance"] if results else 1.0)
                print(f"[{qid}] MISS (Top dist: {top_dist:.3f}): {query[:50]}...")
        else:
            # Поза доменом: має бути 0 результатів нижче порогу
            if valid_results:
                false_accepts += 1
                print(f"[{qid}] FALSE ACCEPT ({len(valid_results)} results, min dist: {valid_results[0]['distance']:.3f}): {query[:50]}...")
            else:
                print(f"[{qid}] CORRECT NOT_FOUND: {query[:50]}...")

    hit_at_4 = hits / in_domain_count if in_domain_count else 0.0
    mrr = rr_total / in_domain_count if in_domain_count else 0.0

    print("\n=== ПІДСУМКОВІ МЕТРИКИ ===")
    print(f"Hit@4: {hit_at_4:.3f} ({hits}/{in_domain_count})")
    print(f"MRR:   {mrr:.3f}")
    print(f"False Accepts (поза базою): {false_accepts}")

    return {"hit@4": hit_at_4, "mrr": mrr, "false_accepts": false_accepts}

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from dotenv import load_dotenv
    load_dotenv()
    evaluate_retrieval()
