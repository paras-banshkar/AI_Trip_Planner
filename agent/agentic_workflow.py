import sys

from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool

from logger.logging import get_logger
from exception.exceptionhandling import TripPlannerException

logger = get_logger(__name__)


class GraphBuilder:
    def __init__(self, model_provider: str = "groq"):
        logger.info(f"Initializing GraphBuilder with provider={model_provider}")
        try:
            self.model_loader = ModelLoader(model_provider=model_provider)
            self.llm = self.model_loader.load_llm()

            self.weather_tools = WeatherInfoTool()
            self.place_search_tools = PlaceSearchTool()
            self.calculator_tools = CalculatorTool()
            self.currency_converter_tools = CurrencyConverterTool()

            self.tools = [
                *self.weather_tools.weather_tool_list,
                *self.place_search_tools.place_search_tool_list,
                *self.calculator_tools.calculator_tool_list,
                *self.currency_converter_tools.currency_converter_tool_list,
            ]
            logger.info(f"Registered {len(self.tools)} tools with the agent.")

            self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
            self.graph = None
            self.system_prompt = SYSTEM_PROMPT

        except Exception as e:
            logger.error(f"Failed to initialize GraphBuilder: {e}")
            raise TripPlannerException(e, sys) from e

    def agent_function(self, state: MessagesState):
        """
        Main agent node: injects the system prompt and calls the LLM (with
        tools bound).

        Retries once on a transient tool-calling failure (observed with
        Groq's llama-3.3-70b: it occasionally emits malformed function-call
        syntax like `<function=foo{"x": 1}</function>` missing the closing
        `>`, which the API rejects with a 400 'tool_use_failed' error).
        Retrying the same request usually succeeds on the second attempt
        since it's a generation quirk, not a deterministic bug. Any other
        kind of error is raised immediately without retrying.
        """
        user_question = state["messages"]
        input_question = [self.system_prompt] + user_question

        last_error = None
        for attempt in range(1, 3):  # try once, retry once on tool_use_failed
            try:
                response = self.llm_with_tools.invoke(input_question)
                return {"messages": [response]}
            except Exception as e:
                last_error = e
                is_transient_tool_call_error = "tool_use_failed" in str(e)
                if is_transient_tool_call_error and attempt == 1:
                    logger.warning(
                        f"Transient tool-call failure on attempt {attempt}, retrying once: {e}"
                    )
                    continue
                logger.error(f"Agent step failed on attempt {attempt}: {e}")
                raise TripPlannerException(e, sys) from e

        # Unreachable, but keeps type-checkers happy.
        raise TripPlannerException(last_error, sys)

    def build_graph(self):
        logger.info("Building LangGraph StateGraph...")
        graph_builder = StateGraph(MessagesState)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
        graph_builder.add_edge("agent", END)
        self.graph = graph_builder.compile()
        logger.info("Graph compiled successfully.")
        return self.graph

    def __call__(self):
        return self.build_graph()
