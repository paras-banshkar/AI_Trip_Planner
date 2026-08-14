import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel

from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document
from logger.logging import get_logger
from exception.exceptionhandling import TripPlannerException

load_dotenv()
logger = get_logger(__name__)

app = FastAPI(title="AI Trip Planner", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set specific origins in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    save_to_file: bool = False


# --- Build the agent graph ONCE at startup instead of on every request. ---
# Rebuilding the LangGraph (and regenerating the Mermaid PNG) per-request was
# pure wasted latency/IO on identical, static graph structure. It's now built
# a single time when the FastAPI app starts.
graph_builder: GraphBuilder | None = None
react_app = None


@app.on_event("startup")
def load_agent_graph():
    global graph_builder, react_app
    logger.info("Building agent graph at startup...")
    graph_builder = GraphBuilder(model_provider="groq")
    react_app = graph_builder()

    try:
        png_graph = react_app.get_graph().draw_mermaid_png()
        with open("my_graph.png", "wb") as f:
            f.write(png_graph)
        logger.info(f"Graph diagram saved as 'my_graph.png' in {os.getcwd()}")
    except Exception as e:
        # Non-fatal: the diagram is a nice-to-have, not required to serve requests.
        logger.warning(f"Could not render graph diagram: {e}")

    logger.info("Agent graph ready.")


@app.post("/query")
async def query_travel_agent(query: QueryRequest):
    logger.info(f"Received query: {query.question!r}")

    if react_app is None:
        logger.error("Agent graph was not initialized.")
        return JSONResponse(
            status_code=503, content={"error": "Agent is still starting up, please retry."}
        )

    try:
        messages = {"messages": [query.question]}
        output = react_app.invoke(messages)

        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content
        else:
            final_output = str(output)

        saved_path = None
        if query.save_to_file:
            saved_path = save_document(final_output)
            logger.info(f"Itinerary saved to {saved_path}")

        logger.info("Query handled successfully.")
        response = {"answer": final_output}
        if saved_path:
            response["saved_to"] = saved_path
        return response

    except Exception as e:
        logger.error(f"Error handling query: {e}")
        exc = TripPlannerException(e, sys)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/health")
async def health_check():
    """Simple readiness probe."""
    return {"status": "ok", "agent_ready": react_app is not None}
