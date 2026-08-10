# 🌍 AI Trip Planner

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

## 🗺️ Roadmap Ideas

- [ ] Persist chat history / past itineraries per user
- [ ] Export itinerary as PDF (see `utils/save_to_document.py`)
- [ ] Support multi-city trips
- [ ] Add authentication for the API
- [ ] Move Mermaid graph visualization out of the request path (currently regenerated on every `/query` call)
- [ ] Add automated tests

---

## ⚠️ Disclaimer

Travel plans are AI-generated. Always verify prices, opening hours, visa requirements, and other time-sensitive details before you travel.

---

## 📄 License

Add a license (e.g. MIT) to clarify how others can use this project.
