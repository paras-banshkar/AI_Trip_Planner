import requests

from logger.logging import get_logger

logger = get_logger(__name__)


class CurrencyConverter:
    def __init__(self, api_key: str):
        self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest"

    def convert(self, amount: float, from_currency: str, to_currency: str):
        """Convert the amount from one currency to another"""
        # Guard against the LLM occasionally passing `amount` as a string
        # (e.g. "5000" instead of 5000), which otherwise causes:
        # TypeError: can't multiply sequence by non-int of type 'float'
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError(f"convert_currency received a non-numeric 'amount': {amount!r}")

        url = f"{self.base_url}/{from_currency}"
        try:
            response = requests.get(url, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error(f"Currency API request failed: {e}")
            raise

        if response.status_code != 200:
            logger.error(f"Currency API call failed: {response.status_code} {response.text}")
            raise Exception(f"API call failed: {response.text}")

        rates = response.json()["conversion_rates"]
        if to_currency not in rates:
            raise ValueError(f"{to_currency} not found in exchange rates.")

        result = amount * rates[to_currency]
        logger.info(f"Converted {amount} {from_currency} -> {result:.2f} {to_currency}")
        return result
