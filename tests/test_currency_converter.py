"""
Unit tests for utils/currency_converter.py.

External HTTP calls are mocked with pytest-mock, so these run offline and
don't burn real EXCHANGE_RATE_API_KEY quota.

Run:
    pytest tests/test_currency_converter.py -v
"""
import pytest
from utils.currency_converter import CurrencyConverter


def _make_response(mocker, status_code=200, json_data=None):
    resp = mocker.Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = str(json_data)
    return resp


class TestConvert:
    def test_successful_conversion(self, mocker):
        converter = CurrencyConverter(api_key="fake_key")
        mock_get = mocker.patch(
            "utils.currency_converter.requests.get",
            return_value=_make_response(
                mocker, json_data={"conversion_rates": {"INR": 83.0, "EUR": 0.92}}
            ),
        )

        result = converter.convert(100, "USD", "INR")

        assert result == pytest.approx(8300.0)
        mock_get.assert_called_once()
        assert "USD" in mock_get.call_args[0][0]

    def test_string_amount_is_coerced_to_float(self, mocker):
        # Regression test: the LLM sometimes passes amount as "5000" (string)
        # instead of 5000 (number). This used to raise a TypeError.
        converter = CurrencyConverter(api_key="fake_key")
        mocker.patch(
            "utils.currency_converter.requests.get",
            return_value=_make_response(
                mocker, json_data={"conversion_rates": {"EUR": 0.9}}
            ),
        )

        result = converter.convert("100", "USD", "EUR")

        assert result == pytest.approx(90.0)

    def test_non_numeric_amount_raises_value_error(self):
        converter = CurrencyConverter(api_key="fake_key")
        with pytest.raises(ValueError, match="non-numeric"):
            converter.convert("not_a_number", "USD", "EUR")

    def test_unknown_target_currency_raises(self, mocker):
        converter = CurrencyConverter(api_key="fake_key")
        mocker.patch(
            "utils.currency_converter.requests.get",
            return_value=_make_response(
                mocker, json_data={"conversion_rates": {"EUR": 0.9}}
            ),
        )

        with pytest.raises(ValueError, match="not found in exchange rates"):
            converter.convert(100, "USD", "ZZZ")

    def test_api_error_status_raises(self, mocker):
        converter = CurrencyConverter(api_key="bad_key")
        mocker.patch(
            "utils.currency_converter.requests.get",
            return_value=_make_response(mocker, status_code=403, json_data={}),
        )

        with pytest.raises(Exception, match="API call failed"):
            converter.convert(100, "USD", "INR")
