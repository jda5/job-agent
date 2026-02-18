from random import uniform


def calculate_delay(attempt: int) -> float:
    """
    Calculate delay for exponential backoff with jitter.
    """
    return (2**attempt) + uniform(0, 1)
