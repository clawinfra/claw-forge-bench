"""Simple arithmetic interpreter with variables."""


class Token:
    def __init__(self, type_: str, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


def tokenize(text: str) -> list[Token]:
    """Tokenize arithmetic expression."""
    tokens = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text[i].isdigit():
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                j += 1
            tokens.append(Token("NUMBER", float(text[i:j])))
            i = j
        elif text[i].isalpha():
            j = i
            while j < len(text) and text[j].isalnum():
                j += 1
            tokens.append(Token("NAME", text[i:j]))
            i = j
        elif text[i] in "+-":
            # Bug: doesn't handle negative numbers (e.g., -5 or x = -3)
            tokens.append(Token("OP", text[i]))
            i += 1
        elif text[i] in "*/":
            tokens.append(Token("OP", text[i]))
            i += 1
        elif text[i] == "=":
            tokens.append(Token("ASSIGN", "="))
            i += 1
        elif text[i] == "(":
            tokens.append(Token("LPAREN", "("))
            i += 1
        elif text[i] == ")":
            tokens.append(Token("RPAREN", ")"))
            i += 1
        else:
            raise SyntaxError(f"Unexpected character: {text[i]}")
    return tokens


class Interpreter:
    def __init__(self):
        self.variables: dict[str, float] = {}

    def evaluate(self, text: str) -> float | None:
        """Evaluate an expression or assignment."""
        tokens = tokenize(text)
        if not tokens:
            return None

        # Check for assignment: NAME = expr
        if (len(tokens) >= 3 and tokens[0].type == "NAME"
                and tokens[1].type == "ASSIGN"):
            name = tokens[0].value
            value = self._eval_expr(tokens[2:])
            self.variables[name] = value
            return value

        return self._eval_expr(tokens)

    def _eval_expr(self, tokens: list[Token]) -> float:
        """Evaluate expression tokens with +/- precedence."""
        result, pos = self._eval_term(tokens, 0)
        while pos < len(tokens) and tokens[pos].type == "OP" and tokens[pos].value in "+-":
            op = tokens[pos].value
            right, pos = self._eval_term(tokens, pos + 1)
            if op == "+":
                result += right
            else:
                result -= right
        return result

    def _eval_term(self, tokens: list[Token], pos: int) -> tuple[float, int]:
        """Evaluate term with *// precedence."""
        result, pos = self._eval_factor(tokens, pos)
        while pos < len(tokens) and tokens[pos].type == "OP" and tokens[pos].value in "*/":
            op = tokens[pos].value
            right, pos = self._eval_factor(tokens, pos + 1)
            if op == "*":
                result *= right
            else:
                result /= right
        return result, pos

    def _eval_factor(self, tokens: list[Token], pos: int) -> tuple[float, int]:
        """Evaluate a factor (number, variable, or parenthesized expr)."""
        token = tokens[pos]
        if token.type == "NUMBER":
            return token.value, pos + 1
        elif token.type == "NAME":
            name = token.value
            if name not in self.variables:
                raise NameError(f"Undefined variable: {name}")
            return self.variables[name], pos + 1
        elif token.type == "LPAREN":
            result = self._eval_expr_from(tokens, pos + 1)
            # Find closing paren
            return result
        raise SyntaxError(f"Unexpected token: {token}")

    def _eval_expr_from(self, tokens: list[Token], start: int) -> float:
        """Evaluate expression from a given position (for parens)."""
        result, pos = self._eval_term(tokens, start)
        while pos < len(tokens) and tokens[pos].type == "OP" and tokens[pos].value in "+-":
            op = tokens[pos].value
            right, pos = self._eval_term(tokens, pos + 1)
            if op == "+":
                result += right
            else:
                result -= right
        return result
