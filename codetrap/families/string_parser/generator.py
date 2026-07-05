from __future__ import annotations

from codetrap.core.problem import BaseProblemFamily, MutantSolution, ProblemVariant
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
    title = "整数表达式解析"
    description = "解析并计算整数表达式，支持括号、空格、一元正负号和四则运算。"
    input_format = '{"expr": 表达式字符串}'
    output_format = '{"ok": true, "value": int} 或 {"ok": false, "error": str}'
    difficulty = "medium"
    tags = ["parser", "expression", "precedence"]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant("calculator", "安全计算器", "实现一个安全整数计算器，不允许使用 eval。表达式包含整数、空格、括号、+、-、*、/ 和一元正负号。", ["calculator"]),
            ProblemVariant("formula", "配置公式解释器", "某配置系统允许用户写简单整数公式。请解析公式并返回结果，非法公式必须返回错误对象。", ["formula"]),
            ProblemVariant("dsl", "迷你表达式 DSL", "为一个迷你 DSL 实现表达式求值器。除法向 0 截断，且要区分一元负号和二元减号。", ["dsl"]),
        ]

    def trap_notes(self) -> list[str]:
        return [
            "必须区分一元负号和二元减号。",
            "乘除优先级高于加减，括号可以嵌套。",
            "整数除法向 0 截断，除 0 返回错误。",
            "非法表达式、缺失括号和整数溢出都应返回结构化错误。",
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
            TestCase(id="parser-basic-precedence", name="乘法优先级", input_data={"expr": "2 + 3 * 4"}, trap_reason="不能从左到右无优先级计算。", difficulty="basic", tags=["precedence"]),
            TestCase(id="parser-basic-spaces", name="随机空格", input_data={"expr": " 10 -  2 * 3 "}, trap_reason="空格位置不应影响解析。", difficulty="basic", tags=["spaces"]),
            TestCase(id="parser-edge-unary", name="一元负号和括号", input_data={"expr": "-(2 + 3) * 4"}, trap_reason="一元负号作用于整个括号表达式。", difficulty="edge", tags=["unary", "paren"]),
            TestCase(id="parser-edge-div", name="向 0 截断", input_data={"expr": "-7 / 2"}, trap_reason="除法语义是向 0 截断。", difficulty="edge", tags=["division"]),
            TestCase(id="parser-adv-invalid", name="非法表达式", input_data={"expr": "1 + * 2"}, trap_reason="非法表达式不能崩溃或给出任意值。", difficulty="adversarial", tags=["invalid"]),
            TestCase(id="parser-adv-div0", name="除零", input_data={"expr": "3 / (2 - 2)"}, trap_reason="除零要返回错误。", difficulty="adversarial", tags=["division-by-zero"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def reference_solution_code(self) -> str:
        return r'''class Parser:
    def __init__(self, text):
        self.text = text
        self.i = 0
    def skip(self):
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1
    def parse(self):
        value = self.expr()
        self.skip()
        if self.i != len(self.text):
            raise ValueError("trailing input")
        return value
    def expr(self):
        value = self.term()
        while True:
            self.skip()
            if self.i < len(self.text) and self.text[self.i] in "+-":
                op = self.text[self.i]; self.i += 1
                rhs = self.term()
                value = value + rhs if op == "+" else value - rhs
            else:
                return value
    def term(self):
        value = self.factor()
        while True:
            self.skip()
            if self.i < len(self.text) and self.text[self.i] in "*/":
                op = self.text[self.i]; self.i += 1
                rhs = self.factor()
                if op == "*":
                    value *= rhs
                else:
                    if rhs == 0:
                        raise ValueError("division by zero")
                    value = int(value / rhs)
            else:
                return value
    def factor(self):
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

def solve(input_data):
    try:
        expr = input_data.get("expr")
        if not isinstance(expr, str) or expr == "":
            raise ValueError("empty expression")
        return {"ok": True, "value": Parser(expr).parse()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
'''

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_unary", "忽略一元负号", "遇到 -(...) 时失败。", "def solve(input_data):\n    return {'ok': False, 'error': 'unary unsupported'}\n"),
            MutantSolution("no_parens", "不处理括号", "直接删除括号或忽略嵌套。", "def solve(input_data):\n    return {'ok': False, 'error': 'paren unsupported'}\n"),
            MutantSolution("left_to_right", "无优先级", "从左到右计算，忽略乘除优先级。", "def solve(input_data):\n    return {'ok': True, 'value': 0}\n"),
        ]
