import requests


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
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("API call failed:", response.json())
        rates = response.json()["conversion_rates"]
        if to_currency not in rates:
            raise ValueError(f"{to_currency} not found in exchange rates.")
        return amount * rates[to_currency]