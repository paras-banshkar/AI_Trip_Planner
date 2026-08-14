"""
Unit tests for utils/expense_calculator.py (pure functions, no API calls).

Run:
    pytest tests/test_calculator.py -v
"""
import pytest
from utils.expense_calculator import Calculator


class TestMultiply:
    def test_multiply_positive_numbers(self):
        assert Calculator.multiply(3, 4) == 12

    def test_multiply_by_zero(self):
        assert Calculator.multiply(100, 0) == 0

    def test_multiply_floats(self):
        # price_per_night is often passed as a float from the LLM
        assert Calculator.multiply(1500.5, 3) == pytest.approx(4501.5)

    def test_multiply_numeric_strings(self):
        # Regression test: eval/tool_call_accuracy.py caught the LLM
        # sending price_per_night/total_days as strings (e.g. "2000", "3"),
        # which used to raise "can't multiply sequence by non-int of type
        # 'float'". estimate_total_hotel_cost's tool signature was also
        # fixed (price_per_night was incorrectly typed `str`).
        assert Calculator.multiply("2000", "3") == pytest.approx(6000.0)
        assert Calculator.multiply("1500.5", 3) == pytest.approx(4501.5)

    def test_multiply_non_numeric_string_raises_clear_error(self):
        with pytest.raises(ValueError, match="must be numeric"):
            Calculator.multiply("free", 3)


class TestCalculateTotal:
    def test_sums_multiple_costs(self):
        assert Calculator.calculate_total(100, 200, 300) == 600

    def test_single_cost(self):
        assert Calculator.calculate_total(50) == 50

    def test_no_costs_returns_zero(self):
        assert Calculator.calculate_total() == 0

    def test_handles_floats(self):
        assert Calculator.calculate_total(10.5, 20.25) == pytest.approx(30.75)


class TestCalculateDailyBudget:
    def test_normal_division(self):
        assert Calculator.calculate_daily_budget(1000, 4) == 250

    def test_zero_days_does_not_raise(self):
        # Guards against ZeroDivisionError if the LLM ever passes days=0
        assert Calculator.calculate_daily_budget(1000, 0) == 0

    def test_negative_days_does_not_raise(self):
        # Documents current behavior; flips to 0 rather than raising or
        # returning a negative number.
        assert Calculator.calculate_daily_budget(1000, -2) == 0
