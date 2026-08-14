# 🌍 AI Trip Planner

![Tests](https://github.com/paras-banshkar/AI_Trip_Planner/actions/workflows/tests.yml/badge.svg)

An agentic travel-planning application that turns a simple natural-language request — like *"Plan a trip to Goa for 5 days"* — into a complete, structured travel itinerary. Built with **LangGraph** for agentic reasoning, **FastAPI** for the backend, and **Streamlit** for the chat interface.

The agent doesn't just generate text — it reasons step-by-step and calls real tools (weather, places, currency, budget) to ground its plan in live data before composing the final itinerary.

---

## ✨ Features

- **Conversational trip planning** — describe your trip in plain English and get back a full itinerary.
- **Agentic reasoning (ReAct-style)** via LangGraph — the agent decides which tools to call and when, iterating until it has enough information to produce a complete plan.
- **Real-time weather** lookups for your destination and travel dates.
- **Places & attractions discovery** — recommendations for sights, activities, and points of interest.
- **Currency conversion** for budgeting trips across currencies.
- **Cost/budget calculation** — estimates for accommodation, activities, and overall trip cost.
- **Pluggable LLM providers** — currently wired up for **Groq**, with `config/` structured to support swapping in other providers.
- **FastAPI backend** exposing a simple `/query` endpoint.
- **Streamlit frontend** for a clean, chat-style user experience.

---

## 🏗️ Architecture

```
User (Streamlit UI)
        │
        ▼
   FastAPI  /query
        │
        ▼
  GraphBuilder (LangGraph agent)
        │
        ├──► Weather Tool          (OpenWeatherMap)
        ├──► Places Tool           (Google Places / Foursquare / Geoapify)
        ├──► Search Tool           (Tavily)
        ├──► Currency Converter    (Exchange Rate API)
        └──► Budget Calculator
        │
        ▼
  Composed Travel Plan (Markdown) → returned to Streamlit
```

The agent is guided by a system prompt defined in `prompt_library/`, which instructs it on how to structure the final itinerary and when to reach for which tool.

---

## 📁 Project Structure

```
AI_Trip_Planner/
├── agent/                  # LangGraph agent definition (GraphBuilder)
│   └── agentic_workflow.py
├── config/                 # LLM provider & app configuration
├── exception/              # Custom exception handling
├── logger/                 # Logging setup
├── notebook/                # Experiments / prototyping notebooks
├── prompt_library/         # System prompts used to guide the agent
├── src/ai_trip_planner/    # Packaged source (installable via setup.py)
├── tools/                  # Agent tools: weather, places, currency, budget
├── utils/                  # Helpers (e.g. save_to_document.py)
├── main.py                 # FastAPI backend entry point
├── streamlit_app.py        # Streamlit frontend
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata (uv-based)
├── uv.lock                 # Locked dependency versions
├── setup.py                # Package setup
└── .python-version         # Pinned Python version
```

---

## 🔧 Tech Stack

| Layer         | Technology |
|---------------|------------|
| Agent framework | LangGraph / LangChain |
| LLM provider    | Groq |
| Backend         | FastAPI |
| Frontend        | Streamlit |
| Weather data    | OpenWeatherMap |
| Places data     | Google Places API, Foursquare, Geoapify |
| Web search      | Tavily |
| Currency data   | ExchangeRate API |
| Dependency mgmt | uv |

---

## 🚀 Getting Started

### Prerequisites

- Python (version pinned in `.python-version`)
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- API keys for the services listed below

### 1. Clone the repository

```bash
git clone https://github.com/paras-banshkar/AI_Trip_Planner.git
cd AI_Trip_Planner
```

### 2. Install dependencies

Using `uv` (recommended, matches the included `uv.lock`):

```bash
uv sync
```

Or with `pip`:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root (this file is git-ignored and should **never** be committed):

```env
# LLM provider
OPENAI_API_KEY=
GROQ_API_KEY=

# Places & maps
GOOGLE_API_KEY=
GPLACES_API_KEY=
FOURSQUARE_API_KEY=
GEOAPIFY_API_KEY=

# Search
TAVILY_API_KEY=

# Weather
OPENWEATHERMAP_API_KEY=

# Currency
EXCHANGE_RATE_API_KEY=
```

> ⚠️ Treat every value above as a secret. Never commit a filled-in `.env` file, and rotate any key you suspect has been exposed (e.g. shared in a screenshot, chat log, or public commit).

### 4. Run the backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run the frontend

In a separate terminal:

```bash
streamlit run streamlit_app.py
```

The Streamlit app expects the backend at `http://localhost:8000` by default (see `BASE_URL` in `streamlit_app.py`).

---

## 📡 API Usage

**Endpoint:** `POST /query`

**Request body:**
```json
{
  "question": "Plan a trip to Goa for 5 days"
}
```

**Response:**
```json
{
  "answer": "## 5-Day Goa Itinerary\n\n..."
}
```

Example with `curl`:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Plan a trip to Manali for 4 days on a budget"}'
```

---

## 🧪 Testing & Evaluation

This project has two layers of evaluation: a standard **unit/integration test suite** (fast, mocked, runs in CI on every push) and an **agent-level evaluation harness** (runs against the real LLM to measure whether the agent behaves correctly, not just whether the code doesn't crash).

### Unit & integration tests

```bash
pip install -r requirements-dev.txt
pytest
```

- **50 tests**, all mocked (no real API keys or network calls needed) — safe to run in CI with zero secrets configured.
- **70% line coverage** overall, concentrated on the tools/utils the agent actually calls (`expense_calculator.py`, `expense_calculator_tool.py`, `currency_converter.py`, `place_search_tool.py`, `place_info_search.py` all at 79–100%).
- Every run also generates `coverage.xml`, `test_results.xml` (JUnit), and a browsable `htmlcov/index.html` report (see `pyproject.toml`'s `[tool.pytest.ini_options]`).
- Tests are split across two levels deliberately: some call `Calculator`/`CurrencyConverter` etc. directly, others invoke the LangChain-wrapped tools via `.invoke()` the way the agent actually calls them — the latter is what caught a real bug (below) that direct unit tests missed entirely.

### Agent evaluation: `eval/tool_call_accuracy.py`

Runs the real compiled LangGraph agent against a fixed set of queries and checks whether it invokes the *correct* tool for each — not just whether the final answer looks plausible.

```bash
python eval/tool_call_accuracy.py
```

| Stage | Tool-call accuracy | What changed |
|---|---|---|
| Baseline | 60% (3/5) | — |
| After fixing a tool type-hint bug | 80% (4/5) | `estimate_total_hotel_cost`'s `price_per_night` was typed `str` instead of `float`, corrupting the generated tool schema |
| After adding retry + fixing a schema-wiring bug | **100% (5/5)** | Added a single retry for transient `tool_use_failed` errors from the LLM provider, and fixed `calculate_total_expense(*costs)` — a `*args` signature that can't receive the keyword argument LangChain's schema-based invocation sends it |

Two of these were genuine production bugs the eval harness caught that standard unit tests could not, because they lived in the *tool-schema-to-Python-function wiring* layer rather than in the underlying logic itself.

There's also a benchmark script in `notebook/benchmark.py` measuring end-to-end latency and destination-grounding across varied trip queries (100% grounding, ~15s average latency at last run).

---

## ✅ Recent Improvements

- **Graph now built once at startup**, not on every `/query` call — the LangGraph agent and its Mermaid diagram used to be rebuilt/regenerated per request; both are now cached and initialized once via a FastAPI startup event.
- **Structured logging** (`logger/logging.py`) — rotating file handler + console output across the agent, model loader, and external API calls (weather/places/currency), replacing the previous empty stub.
- **Custom exception handling** (`exception/exceptionhandling.py`) — wraps errors with the originating file/line for easier debugging, replacing the previous empty stub.
- **Fixed a live bug**: `get_current_weather` was missing `units=metric`, so OpenWeatherMap returned Kelvin while the tool labeled it °C.
- **Fixed a config bug**: the OpenAI provider ignored the model name in `config.yaml` and silently hardcoded `o4-mini`.
- **Fixed a Streamlit bug**: `raise f"..."` (raising a string, which isn't valid Python) has been replaced with proper error display.
- **Wired up chat history** in the Streamlit UI (previously initialized but never displayed) and optional itinerary export via `save_to_file` in the `/query` request body.
- Removed unused/dead code (`tools/arthamatic_op_tool.py`, an experimental Alpha Vantage integration that was never registered with the agent).
- Added a `/health` endpoint for readiness checks.
- **Fixed a tool-schema bug**: `estimate_total_hotel_cost`'s `price_per_night` was typed `str` instead of `float`, corrupting the tool's generated JSON schema and causing both `TypeError`s and LLM-provider validation failures.
- **Fixed a tool-wiring bug**: `calculate_total_expense` used a `*costs: float` signature, which can't accept the keyword argument LangChain's schema-based tool invocation actually sends it — every call to this tool failed regardless of what the model generated.
- **Added retry handling** for transient `tool_use_failed` errors from the LLM provider (a Groq/llama-3.3-70b quirk where it occasionally emits malformed function-call syntax) — retries once before raising.
- **Added a pytest suite** (50 tests, 70% coverage) and a tool-call-accuracy evaluation harness (`eval/tool_call_accuracy.py`) — see [Testing & Evaluation](#-testing--evaluation) above.
- **Added CI** (GitHub Actions) running the full test suite on every push/PR.
- **Added Docker support** (`Dockerfile`) for containerized deployment.

## 🗺️ Roadmap Ideas

- [ ] Persist chat history / past itineraries per user across sessions (server-side)
- [ ] Export itinerary as PDF (currently Markdown only, via `utils/save_to_document.py`)
- [ ] Support multi-city trips
- [ ] Add authentication for the API
- [ ] Expand test coverage on `agent/agentic_workflow.py` (52%), `utils/model_loader.py` (46%), and `tools/weather_info_tool.py` (24%)

---

## ⚠️ Disclaimer

Travel plans are AI-generated. Always verify prices, opening hours, visa requirements, and other time-sensitive details before you travel.

---

## 📄 License

Add a license (e.g. MIT) to clarify how others can use this project.
