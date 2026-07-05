from __future__ import annotations

import copy

from codetrap.core.errors import PatchError
from codetrap.core.problem import BaseProblemFamily, MutantSolution, ProblemVariant
from codetrap.core.testcase import TestCase


def parse_pointer(path: str) -> list[str]:
    if path == "":
        return []
    if not isinstance(path, str) or not path.startswith("/"):
        raise PatchError("invalid pointer")
    result = []
    for part in path.split("/")[1:]:
        token = ""
        i = 0
        while i < len(part):
            if part[i] == "~":
                if i + 1 >= len(part) or part[i + 1] not in "01":
                    raise PatchError("invalid escape")
                token += "~" if part[i + 1] == "0" else "/"
                i += 2
            else:
                token += part[i]
                i += 1
        result.append(token)
    return result


def resolve_parent(doc: object, tokens: list[str]):
    cur = doc
    for token in tokens[:-1]:
        if isinstance(cur, list):
            if not token.isdigit():
                raise PatchError("array index must be numeric")
            idx = int(token)
            if idx < 0 or idx >= len(cur):
                raise PatchError("array index out of bounds")
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur:
                raise PatchError("missing key")
            cur = cur[token]
        else:
            raise PatchError("cannot traverse scalar")
    return cur, tokens[-1] if tokens else None


def get_value(doc: object, path: str):
    tokens = parse_pointer(path)
    if not tokens:
        return doc
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-" or not key.isdigit():
            raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx >= len(parent):
            raise PatchError("array index out of bounds")
        return parent[idx]
    if isinstance(parent, dict):
        if key not in parent:
            raise PatchError("missing key")
        return parent[key]
    raise PatchError("cannot read scalar")


def add_value(doc: object, path: str, value: object):
    tokens = parse_pointer(path)
    if not tokens:
        return value
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-":
            parent.append(value)
            return doc
        if not key.isdigit():
            raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx > len(parent):
            raise PatchError("array insert out of bounds")
        parent.insert(idx, value)
        return doc
    if isinstance(parent, dict):
        parent[key] = value
        return doc
    raise PatchError("cannot add to scalar")


def remove_value(doc: object, path: str):
    tokens = parse_pointer(path)
    if not tokens:
        return doc, None
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-" or not key.isdigit():
            raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx >= len(parent):
            raise PatchError("array remove out of bounds")
        return doc, parent.pop(idx)
    if isinstance(parent, dict):
        if key not in parent:
            raise PatchError("missing key")
        return doc, parent.pop(key)
    raise PatchError("cannot remove from scalar")


class JsonPatchFamily(BaseProblemFamily):
    family_id = "json_patch"
    title = "JSON Patch 补丁应用"
    description = "实现简化版 JSON Patch，支持 add、remove、replace、move、copy、test。"
    input_format = '{"document": JSON文档, "patch": [{"op": 操作, "path": 路径, ...}]}'
    output_format = '{"ok": true, "document": 文档} 或 {"ok": false, "error": 错误信息}'
    difficulty = "hard"
    tags = ["json", "patch", "pointer"]

    def problem_variants(self) -> list[ProblemVariant]:
        return [
            ProblemVariant("config-patch", "配置中心补丁应用", "配置中心收到一组 JSON Patch 操作，需要一次性应用到原配置。任一操作失败时，本次补丁整体失败。", ["config"]),
            ProblemVariant("profile-sync", "用户资料同步补丁", "多个客户端通过 JSON Patch 同步用户资料。请实现补丁应用器，严格处理 JSON Pointer 转义和数组边界。", ["sync"]),
            ProblemVariant("document-edit", "文档结构编辑器", "文档编辑器用补丁描述节点变更。请按顺序执行补丁，并保证失败时不返回部分修改后的文档。", ["document"]),
        ]

    def trap_notes(self) -> list[str]:
        return [
            "JSON Pointer 中 ~0 表示 ~，~1 表示 /，非法转义要报错。",
            "'-' 只能用于 add 到数组末尾，不能用于 remove/replace/test。",
            "move 不能把父节点移动到自己的子节点。",
            "任一操作失败时整个 patch 失败，不能返回部分成功结果。",
        ]

    def reference_solve(self, input_data: dict) -> dict:
        original = input_data.get("document")
        patch = input_data.get("patch", [])
        doc = copy.deepcopy(original)
        try:
            if not isinstance(patch, list):
                raise PatchError("patch must be list")
            for op in patch:
                name = op.get("op")
                path = op.get("path")
                if name == "add":
                    doc = add_value(doc, path, copy.deepcopy(op.get("value")))
                elif name == "remove":
                    doc, _ = remove_value(doc, path)
                elif name == "replace":
                    doc, _ = remove_value(doc, path)
                    doc = add_value(doc, path, copy.deepcopy(op.get("value")))
                elif name == "copy":
                    doc = add_value(doc, path, copy.deepcopy(get_value(doc, op.get("from"))))
                elif name == "move":
                    src = op.get("from")
                    if isinstance(src, str) and path.startswith(src.rstrip("/") + "/") and src != "":
                        raise PatchError("cannot move parent into child")
                    doc, value = remove_value(doc, src)
                    doc = add_value(doc, path, value)
                elif name == "test":
                    if get_value(doc, path) != op.get("value"):
                        raise PatchError("test failed")
                else:
                    raise PatchError("unknown op")
            return {"ok": True, "document": doc}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def generate_cases(self, level: str, count: int) -> list[TestCase]:
        cases = [
            TestCase(id="json-basic-add", name="数组追加", input_data={"document": {"a": [1, 2]}, "patch": [{"op": "add", "path": "/a/-", "value": 3}]}, trap_reason="'-' 只能表示数组末尾追加。", difficulty="basic", tags=["array"]),
            TestCase(id="json-basic-replace", name="对象替换", input_data={"document": {"name": "old"}, "patch": [{"op": "replace", "path": "/name", "value": "new"}]}, trap_reason="replace 要求目标已存在。", difficulty="basic", tags=["replace"]),
            TestCase(id="json-edge-escape", name="路径转义", input_data={"document": {"a/b": {"~key": 1}}, "patch": [{"op": "test", "path": "/a~1b/~0key", "value": 1}]}, trap_reason="必须处理 ~0 和 ~1。", difficulty="edge", tags=["escape"]),
            TestCase(id="json-edge-rollback", name="失败回滚语义", input_data={"document": {"x": 1}, "patch": [{"op": "add", "path": "/y", "value": 2}, {"op": "remove", "path": "/bad~2"}]}, trap_reason="失败时整体失败，不能暴露部分修改。", difficulty="edge", tags=["rollback"]),
            TestCase(id="json-adv-move-child", name="移动到子节点", input_data={"document": {"a": {"b": 1}}, "patch": [{"op": "move", "from": "/a", "path": "/a/b/c"}]}, trap_reason="父节点不能移动到自己的子节点。", difficulty="adversarial", tags=["move"]),
            TestCase(id="json-adv-test-deep", name="深度相等测试", input_data={"document": {"x": [{"a": 1}]}, "patch": [{"op": "test", "path": "/x/0", "value": {"a": 1}}]}, trap_reason="test 需要深度值相等。", difficulty="adversarial", tags=["test"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def reference_solution_code(self) -> str:
        return r'''import copy

class PatchError(Exception):
    pass

def parse_pointer(path):
    if path == "":
        return []
    if not isinstance(path, str) or not path.startswith("/"):
        raise PatchError("invalid pointer")
    result = []
    for part in path.split("/")[1:]:
        token = ""; i = 0
        while i < len(part):
            if part[i] == "~":
                if i + 1 >= len(part) or part[i + 1] not in "01":
                    raise PatchError("invalid escape")
                token += "~" if part[i + 1] == "0" else "/"; i += 2
            else:
                token += part[i]; i += 1
        result.append(token)
    return result

def resolve_parent(doc, tokens):
    cur = doc
    for token in tokens[:-1]:
        if isinstance(cur, list):
            if not token.isdigit(): raise PatchError("array index must be numeric")
            idx = int(token)
            if idx < 0 or idx >= len(cur): raise PatchError("array index out of bounds")
            cur = cur[idx]
        elif isinstance(cur, dict):
            if token not in cur: raise PatchError("missing key")
            cur = cur[token]
        else:
            raise PatchError("cannot traverse scalar")
    return cur, tokens[-1] if tokens else None

def get_value(doc, path):
    tokens = parse_pointer(path)
    if not tokens: return doc
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-" or not key.isdigit(): raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx >= len(parent): raise PatchError("array index out of bounds")
        return parent[idx]
    if isinstance(parent, dict):
        if key not in parent: raise PatchError("missing key")
        return parent[key]
    raise PatchError("cannot read scalar")

def add_value(doc, path, value):
    tokens = parse_pointer(path)
    if not tokens: return value
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-":
            parent.append(value); return doc
        if not key.isdigit(): raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx > len(parent): raise PatchError("array insert out of bounds")
        parent.insert(idx, value); return doc
    if isinstance(parent, dict):
        parent[key] = value; return doc
    raise PatchError("cannot add to scalar")

def remove_value(doc, path):
    tokens = parse_pointer(path)
    if not tokens: return doc, None
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-" or not key.isdigit(): raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx >= len(parent): raise PatchError("array remove out of bounds")
        return doc, parent.pop(idx)
    if isinstance(parent, dict):
        if key not in parent: raise PatchError("missing key")
        return doc, parent.pop(key)
    raise PatchError("cannot remove from scalar")

def solve(input_data):
    doc = copy.deepcopy(input_data.get("document"))
    patch = input_data.get("patch", [])
    try:
        if not isinstance(patch, list):
            raise PatchError("patch must be list")
        for op in patch:
            name = op.get("op"); path = op.get("path")
            if name == "add":
                doc = add_value(doc, path, copy.deepcopy(op.get("value")))
            elif name == "remove":
                doc, _ = remove_value(doc, path)
            elif name == "replace":
                doc, _ = remove_value(doc, path); doc = add_value(doc, path, copy.deepcopy(op.get("value")))
            elif name == "copy":
                doc = add_value(doc, path, copy.deepcopy(get_value(doc, op.get("from"))))
            elif name == "move":
                src = op.get("from")
                if isinstance(src, str) and path.startswith(src.rstrip("/") + "/") and src != "":
                    raise PatchError("cannot move parent into child")
                doc, value = remove_value(doc, src); doc = add_value(doc, path, value)
            elif name == "test":
                if get_value(doc, path) != op.get("value"): raise PatchError("test failed")
            else:
                raise PatchError("unknown op")
        return {"ok": True, "document": doc}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
'''

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_escape", "不处理转义", "没有解析 ~0 和 ~1。", "def solve(input_data):\n    return {'ok': False, 'error': 'escape unsupported'}\n"),
            MutantSolution("bad_array_append", "数组追加错误", "拒绝 '-' 或允许它用于 remove。", "def solve(input_data):\n    return {'ok': True, 'document': input_data.get('document')}\n"),
            MutantSolution("partial_modify", "失败时部分修改", "操作失败后仍返回被修改过的对象。", "def solve(input_data):\n    doc=input_data.get('document')\n    if isinstance(doc,dict): doc['partial']=True\n    return {'ok':False,'error':'failed'}\n"),
        ]
