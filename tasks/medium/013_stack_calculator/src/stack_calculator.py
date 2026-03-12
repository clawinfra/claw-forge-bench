"""Stack-based calculator with operator precedence."""


def calculate(expression: str) -> float:
    """Evaluate a math expression string with +, -, *, / and parentheses."""
    tokens = _tokenize(expression)
    return _evaluate(tokens)


def _tokenize(expr: str) -> list:
    """Tokenize expression into numbers and operators."""
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        if expr[i].isdigit() or expr[i] == '.':
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(float(expr[i:j]))
            i = j
        else:
            tokens.append(expr[i])
            i += 1
    return tokens


def _evaluate(tokens: list) -> float:
    """Evaluate tokens left to right (BUG: no precedence)."""
    if not tokens:
        return 0.0

    # Bug: evaluates left to right without operator precedence
    # 2 + 3 * 4 returns 20 instead of 14
    result = tokens[0]
    i = 1
    while i < len(tokens) - 1:
        op = tokens[i]
        right = tokens[i + 1]
        if op == '+':
            result += right
        elif op == '-':
            result -= right
        elif op == '*':
            result *= right
        elif op == '/':
            result /= right
        i += 2
    return result
