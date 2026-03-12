"""FizzBuzz implementation."""


def fizzbuzz(n: int) -> str:
    """Return FizzBuzz string for n."""
    if n % 3 == 0:
        return "Fizz"
    elif n % 5 == 0:
        return "Buzz"
    elif n % 15 == 0:
        return "FizzBuzz"
    else:
        return str(n)
