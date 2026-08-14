"""
Unit tests for agent/agentic_workflow.py's retry logic.

GraphBuilder.__init__ builds real tool objects and loads a real LLM via
ModelLoader, so instead of constructing a full GraphBuilder (which needs
API keys), these tests call GraphBuilder.agent_function directly on a
bare instance with llm_with_tools/system_prompt patched in. That isolates
exactly the retry behavior we care about.

Run:
    pytest tests/test_agentic_workflow.py -v
"""
import pytest
from agent.agentic_workflow import GraphBuilder
from exception.exceptionhandling import TripPlannerException


def _make_bare_builder(mocker, llm_with_tools):
    """A GraphBuilder instance with __init__ skipped, only the attributes
    agent_function actually touches set up."""
    builder = GraphBuilder.__new__(GraphBuilder)
    builder.llm_with_tools = llm_with_tools
    builder.system_prompt = "You are a trip planning assistant."
    return builder


class TestAgentFunctionRetry:
    def test_succeeds_first_try_no_retry_needed(self, mocker):
        fake_response = mocker.Mock()
        llm_with_tools = mocker.Mock()
        llm_with_tools.invoke.return_value = fake_response
        builder = _make_bare_builder(mocker, llm_with_tools)

        result = builder.agent_function({"messages": ["Plan a trip to Goa"]})

        assert result == {"messages": [fake_response]}
        assert llm_with_tools.invoke.call_count == 1

    def test_retries_once_on_tool_use_failed_then_succeeds(self, mocker):
        fake_response = mocker.Mock()
        llm_with_tools = mocker.Mock()
        # First call raises the transient Groq error, second call succeeds.
        llm_with_tools.invoke.side_effect = [
            Exception(
                "Error code: 400 - {'error': {'code': 'tool_use_failed', "
                "'message': 'Failed to call a function.'}}"
            ),
            fake_response,
        ]
        builder = _make_bare_builder(mocker, llm_with_tools)

        result = builder.agent_function({"messages": ["What's the weather in Jaipur?"]})

        assert result == {"messages": [fake_response]}
        assert llm_with_tools.invoke.call_count == 2

    def test_raises_after_second_tool_use_failed(self, mocker):
        llm_with_tools = mocker.Mock()
        llm_with_tools.invoke.side_effect = Exception(
            "Error code: 400 - {'error': {'code': 'tool_use_failed'}}"
        )
        builder = _make_bare_builder(mocker, llm_with_tools)

        with pytest.raises(TripPlannerException):
            builder.agent_function({"messages": ["Plan a trip to Jaipur"]})

        # Exactly one retry: two attempts total, not more.
        assert llm_with_tools.invoke.call_count == 2

    def test_non_transient_error_raises_immediately_without_retry(self, mocker):
        llm_with_tools = mocker.Mock()
        llm_with_tools.invoke.side_effect = Exception("Error code: 401 - invalid api key")
        builder = _make_bare_builder(mocker, llm_with_tools)

        with pytest.raises(TripPlannerException):
            builder.agent_function({"messages": ["Plan a trip to Jaipur"]})

        # A non-tool_use_failed error should NOT be retried.
        assert llm_with_tools.invoke.call_count == 1
