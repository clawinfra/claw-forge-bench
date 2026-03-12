"""Simple bytecode compiler for variable assignments and arithmetic."""


class Instruction:
    def __init__(self, op: str, arg=None):
        self.op = op
        self.arg = arg

    def __repr__(self):
        if self.arg is not None:
            return f"{self.op} {self.arg}"
        return self.op

    def __eq__(self, other):
        return isinstance(other, Instruction) and self.op == other.op and self.arg == other.arg


class Compiler:
    def __init__(self):
        self.instructions: list[Instruction] = []
        # Bug: single flat dict for all scopes — variables collide
        self.locals: dict[str, int] = {}
        self.next_slot = 0

    def compile_block(self, statements: list[dict]) -> list[Instruction]:
        """Compile a block of statements."""
        for stmt in statements:
            self._compile_stmt(stmt)
        return self.instructions

    def _compile_stmt(self, stmt: dict) -> None:
        """Compile a single statement."""
        if stmt["type"] == "assign":
            self._compile_expr(stmt["value"])
            slot = self._get_slot(stmt["name"])
            self.instructions.append(Instruction("STORE_LOCAL", slot))
        elif stmt["type"] == "block":
            # Bug: doesn't create a new scope — inner vars overwrite outer
            for s in stmt["body"]:
                self._compile_stmt(s)
        elif stmt["type"] == "expr":
            self._compile_expr(stmt["value"])

    def _compile_expr(self, expr: dict) -> None:
        """Compile an expression."""
        if expr["type"] == "number":
            self.instructions.append(Instruction("LOAD_CONST", expr["value"]))
        elif expr["type"] == "name":
            slot = self._get_slot(expr["name"])
            self.instructions.append(Instruction("LOAD_LOCAL", slot))
        elif expr["type"] == "binop":
            self._compile_expr(expr["left"])
            self._compile_expr(expr["right"])
            op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
            self.instructions.append(Instruction(op_map[expr["op"]]))

    def _get_slot(self, name: str) -> int:
        """Get or allocate a local variable slot."""
        if name not in self.locals:
            self.locals[name] = self.next_slot
            self.next_slot += 1
        return self.locals[name]

    def get_slot_for(self, name: str) -> int | None:
        """Get the slot index for a variable name, or None."""
        return self.locals.get(name)
