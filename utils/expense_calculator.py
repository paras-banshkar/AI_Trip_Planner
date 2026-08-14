def _to_number(value, field_name: str) -> float:
    """
    Coerce a value to float, whether it arrives as an int, float, or a
    numeric-looking string (LLM tool-calls sometimes send "2000" instead
    of 2000). Raises a clear ValueError instead of letting a bad type
    blow up downstream with a cryptic TypeError.
    """
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be numeric, got {value!r}")


class Calculator:
    @staticmethod
    def multiply(a, b) -> float:
        """
        Multiply two numbers.

        Args:
            a: The first number (int, float, or numeric string).
            b: The second number (int, float, or numeric string).

        Returns:
            float: The product of a and b.
        """
        return _to_number(a, "a") * _to_number(b, "b")

    @staticmethod
    def calculate_total(*x) -> float:
        """
        Calculate sum of the given list of numbers

        Args:
            x (list): List of numbers (int, float, or numeric strings)

        Returns:
            float: The sum of numbers in the list x
        """
        return sum(_to_number(v, "cost") for v in x)

    @staticmethod
    def calculate_daily_budget(total, days) -> float:
        """
        Calculate daily budget

        Args:
            total: Total cost (int, float, or numeric string).
            days: Total number of days (int, float, or numeric string).

        Returns:
            float: Expense for a single day
        """
        total = _to_number(total, "total")
        days = _to_number(days, "days")
        return total / days if days > 0 else 0
    
    