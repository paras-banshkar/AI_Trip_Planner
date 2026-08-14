"""
eval/tool_call_accuracy.py — Measure whether the agent calls the RIGHT tools.

notebook/benchmark.py checks the final answer (latency, success, does it
mention the destination). It does NOT check whether the agent actually used
tools correctly along the way. This script closes that gap: for each test
query we know which tool *categories* a good agent should touch (e.g. a
budget question should call the calculator; a "what's the weather" question
should call the weather tool), run the real compiled graph directly
(bypassing FastAPI), and check the emitted tool_calls against expectations.

This is what lets you honestly say "measured tool-selection accuracy" on a
resume, instead of just "final answer looked okay."

Requires real API keys in .env (GROQ_API_KEY + whatever tool APIs are
configured) since it runs the actual agent, not a mock.

Usage:
    python eval/tool_call_accuracy.py
"""
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from agent.agentic_workflow import GraphBuilder

load_dotenv()

# Each case: (query, set of tool names where AT LEAST ONE must be called)
# Tool names come from tools/*.py — see the @tool-decorated function names.
TEST_CASES = [
    (
        "What's the weather like in Manali right now?",
        {"get_current_weather", "get_weather_forecast"},
    ),
    (
        "What are the top attractions in Jaipur?",
        {"search_attractions"},
    ),
    (
        "Convert 500 USD to INR",
        {"convert_currency"},
    ),
    (
        "If a hotel costs 2000 INR per night for 5 nights, what's the total?",
        {"estimate_total_hotel_cost", "calculate_total_expense"},
    ),
    (
        "Plan a 3-day trip to Goa with a full budget breakdown",
        {
            "get_current_weather",
            "get_weather_forecast",
            "search_attractions",
            "search_restaurants",
            "estimate_total_hotel_cost",
            "calculate_total_expense",
            "calculate_daily_expense_budget",
        },
    ),
]


def get_called_tool_names(final_state) -> set:
    """Extract every tool name the agent invoked across the whole run."""
    called = set()
    for msg in final_state.get("messages", []):
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                called.add(tc["name"])
    return called


def main():
    print("Building agent graph...")
    react_app = GraphBuilder(model_provider="groq")()

    results = []
    for query, expected_any_of in TEST_CASES:
        print(f"\nQuery: {query}")
        try:
            final_state = react_app.invoke({"messages": [query]})
            called = get_called_tool_names(final_state)
            hit = bool(called & expected_any_of)
            results.append(
                {
                    "query": query,
                    "expected_any_of": ",".join(sorted(expected_any_of)),
                    "tools_called": ",".join(sorted(called)) or "(none)",
                    "correct_tool_used": hit,
                }
            )
            print(f"  expected one of: {sorted(expected_any_of)}")
            print(f"  actually called: {sorted(called) or '(none)'}")
            print(f"  -> {'PASS' if hit else 'FAIL'}")
        except Exception as e:
            results.append(
                {
                    "query": query,
                    "expected_any_of": ",".join(sorted(expected_any_of)),
                    "tools_called": f"ERROR: {e}",
                    "correct_tool_used": False,
                }
            )
            print(f"  -> ERROR: {e}")

    accuracy = sum(r["correct_tool_used"] for r in results) / len(results)
    print("\n" + "=" * 60)
    print(f"Tool-call accuracy: {accuracy * 100:.1f}% ({sum(r['correct_tool_used'] for r in results)}/{len(results)})")
    print("=" * 60)

    with open("eval/tool_call_accuracy_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print("\nDetailed results saved to eval/tool_call_accuracy_results.csv")


if __name__ == "__main__":
    main()
