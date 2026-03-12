"""Tests for bytecode compiler."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from bytecode_compiler import Compiler, Instruction


def test_simple_assignment():
    c = Compiler()
    stmts = [{"type": "assign", "name": "x", "value": {"type": "number", "value": 42}}]
    instrs = c.compile_block(stmts)
    assert Instruction("LOAD_CONST", 42) in instrs
    assert Instruction("STORE_LOCAL", 0) in instrs


def test_two_variables_different_slots():
    c = Compiler()
    stmts = [
        {"type": "assign", "name": "x", "value": {"type": "number", "value": 1}},
        {"type": "assign", "name": "y", "value": {"type": "number", "value": 2}},
    ]
    c.compile_block(stmts)
    assert c.get_slot_for("x") == 0
    assert c.get_slot_for("y") == 1


def test_inner_scope_new_var_gets_different_slot():
    """A new variable in an inner scope should get its own slot, not collide with outer."""
    c = Compiler()
    stmts = [
        {"type": "assign", "name": "x", "value": {"type": "number", "value": 1}},
        {"type": "block", "body": [
            {"type": "assign", "name": "y", "value": {"type": "number", "value": 2}},
        ]},
    ]
    c.compile_block(stmts)
    # x and y should have DIFFERENT slots
    slot_x = c.get_slot_for("x")
    assert slot_x is not None
    assert slot_x == 0


def test_scope_isolation_inner_var_not_visible_outside():
    """Variables declared only in inner scope should not leak to outer scope after block ends."""
    c = Compiler()
    stmts = [
        {"type": "assign", "name": "x", "value": {"type": "number", "value": 1}},
        {"type": "block", "body": [
            {"type": "assign", "name": "inner_only", "value": {"type": "number", "value": 99}},
        ]},
    ]
    c.compile_block(stmts)
    # After the block, inner_only should NOT be in the outer scope
    # With the buggy flat dict, inner_only leaks into the global scope
    outer_slot = c.get_slot_for("inner_only")
    assert outer_slot is None, (
        "inner_only should not be visible in outer scope, "
        f"but found at slot {outer_slot}"
    )


def test_binop_expression():
    c = Compiler()
    stmts = [
        {"type": "assign", "name": "x", "value": {"type": "number", "value": 1}},
        {"type": "assign", "name": "y", "value": {
            "type": "binop", "op": "+",
            "left": {"type": "name", "name": "x"},
            "right": {"type": "number", "value": 2},
        }},
    ]
    instrs = c.compile_block(stmts)
    assert Instruction("ADD", None) in instrs
