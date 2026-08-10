"""
benchmark.py — Quantify AI Trip Planner performance.

Measures, across a fixed set of test queries against the running FastAPI backend:
  - Response latency (avg / min / max / p95)
  - Success rate (did we get a valid, non-empty itinerary back?)
  - Response length (rough proxy for itinerary completeness)
  - Basic keyword-grounding check (did the plan mention the requested destination?)

Usage:
    1. Start your backend:  uvicorn main:app --reload --host 0.0.0.0 --port 8000
    2. In another terminal: python benchmark.py
    3. Results print to console AND are saved to benchmark_results.csv

Adjust BASE_URL / ENDPOINT / REQUEST_KEY below if your main.py differs.
"""

import csv
import statistics
import time
from dataclasses import dataclass, asdict

import requests

# ---- Config: adjust to match your main.py ----
BASE_URL = "http://localhost:8000"
ENDPOINT = "/query"
REQUEST_KEY = "question"          # the JSON key main.py expects, e.g. {"question": "..."}
RESPONSE_KEY = "answer"           # the JSON key main.py returns the itinerary under
TIMEOUT_SECONDS = 60

# ---- Test set: 8 queries spanning different trip types ----
# Kept small + paced (see DELAY_BETWEEN_QUERIES_SECONDS below) to conserve
# Groq's free-tier daily token budget (100k TPD on llama-3.3-70b-versatile).
# At ~950-1900 tokens/query, 8 queries uses roughly 8k-15k tokens total.
TEST_QUERIES = [
    ("Plan a 3-day trip to Jaipur", "Jaipur"),
    ("Plan a 5-day budget trip to Goa", "Goa"),
    ("Weekend trip to Manali with adventure activities", "Manali"),
    ("Plan a 4-day family trip to Kerala with kids", "Kerala"),
    ("Luxury 3-day honeymoon trip to Udaipur", "Udaipur"),
    ("Solo backpacking trip to Rishikesh for 4 days", "Rishikesh"),
    ("Plan a 6-day trip to Ladakh covering major attractions", "Ladakh"),
    ("2-day quick trip to Pondicherry with beach activities", "Pondicherry"),
]

# Delay between requests (seconds) — spreads out token usage and avoids
# tripping any per-minute rate limit on top of the daily cap.
DELAY_BETWEEN_QUERIES_SECONDS = 4


@dataclass
class QueryResult:
    query: str
    expected_destination: str
    success: bool
    latency_seconds: float
    response_length_chars: int
    mentions_destination: bool
    error: str = ""


def run_query(question: str) -> tuple[bool, float, str, str]:
    """Returns (success, latency, response_text, error_message)."""
    start = time.time()
    try:
        resp = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json={REQUEST_KEY: question},
            timeout=TIMEOUT_SECONDS,
        )
        latency = time.time() - start
        data = resp.json()
        if resp.status_code != 200:
            # main.py returns {"error": "..."} on failure — surface it instead of discarding it
            error_msg = data.get("error", str(data))
            return False, latency, "", f"HTTP {resp.status_code}: {error_msg}"
        text = data.get(RESPONSE_KEY, "")
        if not text:
            # fall back: some versions return the raw string or a different key
            text = str(data)
        success = len(text.strip()) > 0
        return success, latency, text, ""
    except Exception as e:
        latency = time.time() - start
        return False, latency, "", str(e)


def main():
    results: list[QueryResult] = []

    print(f"Running {len(TEST_QUERIES)} test queries against {BASE_URL}{ENDPOINT} ...\n")

    for i, (query, destination) in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] {query}")
        success, latency, text, error = run_query(query)
        mentions_dest = destination.lower() in text.lower() if text else False

        results.append(
            QueryResult(
                query=query,
                expected_destination=destination,
                success=success,
                latency_seconds=round(latency, 2),
                response_length_chars=len(text),
                mentions_destination=mentions_dest,
                error=error,
            )
        )

        status = "OK" if success else f"FAILED ({error})"
        print(f"    -> {status} | {latency:.2f}s | {len(text)} chars | mentions destination: {mentions_dest}\n")

        if i < len(TEST_QUERIES):
            time.sleep(DELAY_BETWEEN_QUERIES_SECONDS)

    # ---- Aggregate stats ----
    successful = [r for r in results if r.success]
    latencies = [r.latency_seconds for r in successful]
    grounded = [r for r in successful if r.mentions_destination]

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total queries:         {len(results)}")
    print(f"Successful responses:  {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    if latencies:
        print(f"Avg latency:           {statistics.mean(latencies):.2f}s")
        print(f"Min latency:           {min(latencies):.2f}s")
        print(f"Max latency:           {max(latencies):.2f}s")
        if len(latencies) > 1:
            print(f"Median latency:        {statistics.median(latencies):.2f}s")
            sorted_lat = sorted(latencies)
            p95_idx = int(len(sorted_lat) * 0.95)
            print(f"p95 latency:           {sorted_lat[min(p95_idx, len(sorted_lat)-1)]:.2f}s")
    if successful:
        avg_len = statistics.mean(r.response_length_chars for r in successful)
        print(f"Avg response length:   {avg_len:.0f} characters")
        print(f"Destination-grounded:  {len(grounded)}/{len(successful)} ({len(grounded)/len(successful)*100:.1f}%)")
    print("=" * 60)

    # ---- Save to CSV ----
    with open("benchmark_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))

    print("\nDetailed results saved to benchmark_results.csv")


if __name__ == "__main__":
    main()