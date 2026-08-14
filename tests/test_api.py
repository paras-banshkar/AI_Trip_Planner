"""
Integration tests for main.py's FastAPI app.

The LangGraph agent (GraphBuilder) is mocked so these tests run fast,
offline, and without needing real GROQ/OpenAI/weather/places API keys.
For a true end-to-end test against the real agent, see eval/ instead.

Run:
    pytest tests/test_api.py -v
"""
import sys
import types

import pytest
from fastapi.testclient import TestClient


class _FakeAIMessage:
    def __init__(self, content):
        self.content = content


class _FakeCompiledGraph:
    """Stands in for the object returned by GraphBuilder()() (react_app)."""

    def __init__(self, reply="## Mock itinerary\n\nDay 1: ..."):
        self._reply = reply

    def invoke(self, messages):
        return {"messages": [_FakeAIMessage(self._reply)]}

    def get_graph(self):
        class _G:
            def draw_mermaid_png(self_inner):
                return b""  # empty PNG bytes; main.py writes this to disk
        return _G()


class _FakeGraphBuilder:
    """Stands in for agent.agentic_workflow.GraphBuilder."""

    def __init__(self, model_provider="groq"):
        self.model_provider = model_provider

    def __call__(self):
        return _FakeCompiledGraph()


@pytest.fixture
def client(mocker, tmp_path, monkeypatch):
    # Patch GraphBuilder where main.py looks it up, BEFORE the app's
    # startup event runs (TestClient triggers startup on first use / __enter__).
    mocker.patch("main.GraphBuilder", _FakeGraphBuilder)
    # Avoid writing my_graph.png into the real repo during tests.
    monkeypatch.chdir(tmp_path)

    import main  # import after patching sys.path is set up by conftest.py

    with TestClient(main.app) as test_client:
        yield test_client


class TestHealthEndpoint:
    def test_health_ok_after_startup(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["agent_ready"] is True


class TestQueryEndpoint:
    def test_returns_answer_for_valid_question(self, client):
        resp = client.post("/query", json={"question": "Plan a 3-day trip to Goa"})
        assert resp.status_code == 200
        body = resp.json()
        assert "answer" in body
        assert "itinerary" in body["answer"].lower()

    def test_missing_question_returns_422(self, client):
        # `question` is a required field on QueryRequest
        resp = client.post("/query", json={})
        assert resp.status_code == 422

    def test_save_to_file_flag_returns_saved_path(self, client, mocker):
        mocker.patch("main.save_document", return_value="/tmp/fake_itinerary.md")

        resp = client.post(
            "/query",
            json={"question": "Plan a 2-day trip to Pondicherry", "save_to_file": True},
        )

        assert resp.status_code == 200
        assert resp.json()["saved_to"] == "/tmp/fake_itinerary.md"
