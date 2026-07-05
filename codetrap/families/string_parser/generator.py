from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution
from codetrap.core.testcase import TestCase


class Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def parse(self) -> int:
        value = self.expr()
        self.skip()
        if self.i != len(self.text):
            raise ValueError("trailing input")
        return value

    def skip(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def expr(self) -> int:
        value = self.term()
        while True:
            self.skip()
            if self.i < len(self.text) and self.text[self.i] in "+-":
                op = self.text[self.i]
                self.i += 1
                rhs = self.term()
                value = value + rhs if op == "+" else value - rhs
            else:
                return value

    def term(self) -> int:
        value = self.factor()
        while True:
            self.skip()
            if self.i < len(self.text) and self.text[self.i] in "*/":
                op = self.text[self.i]
                self.i += 1
                rhs = self.factor()
                if op == "*":
                    value *= rhs
                else:
                    if rhs == 0:
                        raise ValueError("division by zero")
                    value = int(value / rhs)
            else:
                return value

    def factor(self) -> int:
        self.skip()
        sign = 1
        while self.i < len(self.text) and self.text[self.i] in "+-":
            if self.text[self.i] == "-":
                sign *= -1
            self.i += 1
            self.skip()
        if self.i < len(self.text) and self.text[self.i] == "(":
            self.i += 1
            value = self.expr()
            self.skip()
            if self.i >= len(self.text) or self.text[self.i] != ")":
                raise ValueError("missing closing parenthesis")
            self.i += 1
            return sign * value
        start = self.i
        while self.i < len(self.text) and self.text[self.i].isdigit():
            self.i += 1
        if start == self.i:
            raise ValueError("expected integer")
        value = int(self.text[start:self.i])
        if abs(value) > 2**31:
            raise ValueError("integer overflow")
        return sign * value


class StringParserFamily(BaseProblemFamily):
    family_id = "string_parser"
    title = "整数表达式解析器"
    description = "实现一个整数表达式解析器，支持加减乘除、括号、空格和一元正负号。整数除法向 0 截断，非法表达式返回错误。"
    input_format = '{"expr": 表达式字符串}'
    output_format = '{"ok": true, "value": 计算结果} 或 {"ok": false, "error": 错误信息}'
    difficulty = "medium"
    tags = ["parser", "expression", "precedence"]

    def trap_notes(self) -> list[str]:
        return [
            "需要区分一元负号和二元减号。",
            "乘除优先级高于加减，括号可以嵌套。",
            "整数除法向 0 截断，除 0 要返回错误。",
            "非法表达式、缺失括号和整数溢出都要返回结构化错误。",
        ]

    def reference_solve(self, input_data: dict) -> dict:
        try:
            expr = input_data.get("expr")
            if not isinstance(expr, str) or expr == "":
                raise ValueError("empty expression")
            return {"ok": True, "value": Parser(expr).parse()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="parser-basic-1", name="precedence", input_data={"expr": "2 + 3 * 4"}, trap_reason="Multiplication must bind tighter than addition.", difficulty="basic", tags=["precedence"]),
            TestCase(id="parser-edge-1", name="unary and parentheses", input_data={"expr": "-(2 + 3) * 4"}, trap_reason="Unary minus before parentheses differs from binary subtraction.", difficulty="edge", tags=["unary", "paren"]),
            TestCase(id="parser-edge-2", name="truncate toward zero", input_data={"expr": "-7 / 2"}, trap_reason="Division semantics must be explicit: truncate toward zero.", difficulty="edge", tags=["division"]),
            TestCase(id="parser-adv-1", name="invalid expression", input_data={"expr": "1 + * 2"}, trap_reason="Malformed expressions should return structured errors.", difficulty="adversarial", tags=["invalid"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_unary", "Ignores unary signs", "Fails on unary minus.", "def solve(input_data):\n    return {'ok': False, 'error': 'unary unsupported'}\n"),
            MutantSolution("no_parens", "No parentheses", "Strips parentheses instead of parsing them.", "def solve(input_data):\n    return {'ok': True, 'value': eval(input_data['expr'].replace('(','').replace(')',''))}\n"),
            MutantSolution("left_to_right", "Left-to-right precedence", "Evaluates without operator precedence.", "def solve(input_data):\n    toks=input_data['expr'].split(); val=int(toks[0]); i=1\n    while i<len(toks):\n        op=toks[i]; rhs=int(toks[i+1]); val = val+rhs if op=='+' else val-rhs if op=='-' else val*rhs if op=='*' else int(val/rhs); i+=2\n    return {'ok': True, 'value': val}\n"),
        ]
