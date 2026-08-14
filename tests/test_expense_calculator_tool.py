"""
Unit tests for tools/expense_calculator_tool.py — invoked through .invoke(),
the same way LangChain's ToolNode calls them, not by calling Calculator
directly.

Why this file exists: tests/test_calculator.py tests utils/expense_calculator.py
directly and passed the whole time, even though calculate_total_expense was
completely broken. The bug was in how the @tool-decorated wrapper's schema
maps to the underlying function signature (*costs can't receive a keyword
argument), not in Calculator itself. Only invoking through the LangChain
tool interface exercises that wiring.

Run:
    pytest tests/test_expense_calculator_tool.py -v
"""
import pytest
from tools.expense_calculator_tool import CalculatorTool


@pytest.fixture
def tools_by_name():
    calc_tool = CalculatorTool()
    return {t.name: t for t in calc_tool.calculator_tool_list}


class TestEstimateTotalHotelCost:
    def test_invoke_with_numeric_args(self, tools_by_name):
        result = tools_by_name["estimate_total_hotel_cost"].invoke(
            {"price_per_night": 2000, "total_days": 5}
        )
        assert result == 10000


class TestCalculateTotalExpense:
    def test_invoke_with_list_of_costs(self, tools_by_name):
        # This is exactly the call shape LangChain builds from the tool's
        # generated schema. It used to raise:
        #   "got an unexpected keyword argument 'costs'"
        result = tools_by_name["calculate_total_expense"].invoke(
            {"costs": [1000, 2000, 500]}
        )
        assert result == 3500

    def test_invoke_with_single_cost(self, tools_by_name):
        result = tools_by_name["calculate_total_expense"].invoke({"costs": [750]})
        assert result == 750


class TestCalculateDailyExpenseBudget:
    def test_invoke_with_numeric_args(self, tools_by_name):
        result = tools_by_name["calculate_daily_expense_budget"].invoke(
            {"total_cost": 1000, "days": 4}
        )
        assert result == 250
