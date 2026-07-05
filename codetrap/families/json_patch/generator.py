from __future__ import annotations

import copy

from codetrap.core.errors import PatchError
from codetrap.core.problem import BaseProblemFamily, MutantSolution
from codetrap.core.testcase import TestCase


def parse_pointer(path: str) -> list[str]:
    if path == "":
        return []
    if not isinstance(path, str) or not path.startswith("/"):
        raise PatchError("invalid pointer")
    parts = path.split("/")[1:]
    out = []
    for part in parts:
        i = 0
        token = ""
        while i < len(part):
            if part[i] == "~":
                if i + 1 >= len(part) or part[i + 1] not in "01":
                    raise PatchError("invalid escape")
                token += "~" if part[i + 1] == "0" else "/"
                i += 2
            else:
                token += part[i]
                i += 1
        out.append(token)
    return out


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
        return None, doc
    parent, key = resolve_parent(doc, tokens)
    if isinstance(parent, list):
        if key == "-" or not key.isdigit():
            raise PatchError("invalid array index")
        idx = int(key)
        if idx < 0 or idx >= len(parent):
            raise PatchError("array remove out of bounds")
        return parent.pop(idx), doc
    if isinstance(parent, dict):
        if key not in parent:
            raise PatchError("missing key")
        return parent.pop(key), doc
    raise PatchError("cannot remove from scalar")


class JsonPatchFamily(BaseProblemFamily):
    family_id = "json_patch"
    title = "简化版 JSON Patch"
    description = "实现简化版 JSON Patch，支持 add、remove、replace、move、copy、test 操作，路径遵循 JSON Pointer 规则。"
    input_format = '{"document": 原始 JSON 文档, "patch": [{"op": 操作名, "path": 路径, ...}]}'
    output_format = '{"ok": true, "document": 修改后文档} 或 {"ok": false, "error": 错误信息}'
    difficulty = "hard"
    tags = ["json", "patch", "pointer"]

    def trap_notes(self) -> list[str]:
        return [
            "JSON Pointer 中 ~0 表示 ~，~1 表示 /，非法转义必须报错。",
            "数组 add、remove、replace 的下标边界不同，'-' 只能用于 add 到数组末尾。",
            "move 不能把父节点移动到自己的子节点。",
            "任一操作失败时整个 patch 失败，不能暴露部分修改后的文档。",
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
                    _, doc = remove_value(doc, path)
                elif name == "replace":
                    _, doc = remove_value(doc, path)
                    doc = add_value(doc, path, copy.deepcopy(op.get("value")))
                elif name == "copy":
                    doc = add_value(doc, path, copy.deepcopy(get_value(doc, op.get("from"))))
                elif name == "move":
                    src = op.get("from")
                    if path.startswith(src.rstrip("/") + "/") and src != "":
                        raise PatchError("cannot move parent into child")
                    value, doc = remove_value(doc, src)
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
            TestCase(id="json-basic-1", name="add replace remove", input_data={"document": {"a": [1, 2]}, "patch": [{"op": "add", "path": "/a/-", "value": 3}, {"op": "replace", "path": "/a/0", "value": 9}]}, trap_reason="Array append and replace have different index rules.", difficulty="basic", tags=["array"]),
            TestCase(id="json-edge-1", name="escaped pointer", input_data={"document": {"a/b": {"~key": 1}}, "patch": [{"op": "test", "path": "/a~1b/~0key", "value": 1}]}, trap_reason="JSON Pointer requires ~0 and ~1 escapes.", difficulty="edge", tags=["escape"]),
            TestCase(id="json-edge-2", name="invalid escape rollback", input_data={"document": {"x": 1}, "patch": [{"op": "add", "path": "/y", "value": 2}, {"op": "remove", "path": "/bad~2"}]}, trap_reason="A failing operation should make the whole patch fail without exposing partial success.", difficulty="edge", tags=["rollback"]),
            TestCase(id="json-adv-1", name="move parent into child", input_data={"document": {"a": {"b": 1}}, "patch": [{"op": "move", "from": "/a", "path": "/a/b/c"}]}, trap_reason="Moving a parent into its child is invalid.", difficulty="adversarial", tags=["move"]),
        ]
        filtered = [c for c in cases if c.difficulty == level] or cases
        return self._finalize_cases((filtered * ((count // len(filtered)) + 1)), count)

    def generate_mutants(self) -> list[MutantSolution]:
        return [
            MutantSolution("no_escape", "No pointer escaping", "Splits pointer without decoding ~0/~1.", "def solve(input_data):\n    return {'ok': False, 'error': 'no escapes supported'}\n"),
            MutantSolution("bad_array_append", "Bad array append", "Rejects '-' for array append.", "def solve(input_data):\n    if any(op.get('path','').endswith('/-') for op in input_data.get('patch',[])): return {'ok':False,'error':'bad index'}\n    return {'ok':True,'document':input_data.get('document')}\n"),
            MutantSolution("partial_modify", "Partial modification", "Mutates before returning error.", "def solve(input_data):\n    doc=input_data.get('document')\n    if isinstance(doc,dict): doc['partial']=True\n    return {'ok':False,'error':'failed'}\n"),
        ]
