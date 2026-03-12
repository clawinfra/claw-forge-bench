"""Temperature conversion."""


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    # Bug: adds 9/5 instead of multiplying
    return celsius + 9 / 5 + 32
