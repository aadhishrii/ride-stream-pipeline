# run_test_set.py
from run_query import run_query
from test_set import TEST_QUESTIONS
import time

def run_all():
    results = []
    for category, question in TEST_QUESTIONS:
        print(f"Running [{category}]: {question}")
        result = run_query(question)
        result["category"] = category
        results.append(result)
        time.sleep(1)  # small buffer between queries, be polite to the free-tier warehouse

    total = len(results)
    successes = sum(1 for r in results if r["success"])
    retried = sum(1 for r in results if r.get("retried"))

    print("\n=== SUMMARY ===")
    print(f"Total: {total}")
    print(f"Success: {successes}/{total} ({round(successes/total*100)}%)")
    print(f"Required retry: {retried}")

    print("\nBy category:")
    categories = set(c for c, _ in TEST_QUESTIONS)
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_success = sum(1 for r in cat_results if r["success"])
        print(f"  {cat}: {cat_success}/{len(cat_results)}")

    print("\nFailures:")
    for r in results:
        if not r["success"]:
            print(f"  [{r['category']}] {r['question']} → {r.get('error')}")

    return results

if __name__ == "__main__":
    run_all()