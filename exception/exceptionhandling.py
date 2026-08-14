import sys


class TripPlannerException(Exception):
    """
    Custom exception that captures the originating file name and line
    number of the error, so logs/tracebacks point straight at the
    failure site instead of a generic "Exception" with no context.

    Usage:
        try:
            risky_call()
        except Exception as e:
            raise TripPlannerException(e, sys) from e
    """

    def __init__(self, error_message, error_detail: sys):
        super().__init__(str(error_message))
        self.error_message = self._build_detailed_message(error_message, error_detail)

    @staticmethod
    def _build_detailed_message(error_message, error_detail: sys) -> str:
        _, _, exc_tb = error_detail.exc_info()

        if exc_tb is None:
            return f"Error: {error_message}"

        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        return (
            f"Error occurred in script [{file_name}] "
            f"at line [{line_number}]: {error_message}"
        )

    def __str__(self):
        return self.error_message
