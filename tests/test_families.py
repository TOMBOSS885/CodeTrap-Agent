from codetrap.core.registry import registry


def test_all_families_generate_expected_outputs():
    for family in registry.all():
        for level in ("basic", "edge", "adversarial"):
            cases = family.generate_cases(level, 2)
            assert cases
            for case in cases:
                assert case.expected_output == family.reference_solve(case.input_data)


def test_all_families_generate_problem_bundle():
    for family in registry.all():
        bundle = family.generate_problem_bundle("edge", 2, [], "unit test query", "online_search_disabled")
        assert bundle.statement.startswith("# ")
        assert len(bundle.cases) == 2
        namespace = {}
        exec(bundle.reference_answer, namespace)
        assert callable(namespace["solve"])
        assert namespace["solve"](bundle.cases[0].input_data) == bundle.cases[0].expected_output
        assert all(case.expected_output is not None for case in bundle.cases)


def test_graph_reference_edge_cases():
    graph = registry.get("graph_paths")
    assert graph.reference_solve({"n": 1, "edges": []}) == 1
    assert graph.reference_solve({"n": 1, "edges": [[0, 0]]}) == -1
    assert graph.reference_solve({"n": 4, "edges": [[0, 1], [2, 2]]}) == 0
    assert graph.reference_solve({"n": 3, "edges": [[0, 1], [0, 1], [1, 2]]}) == 2


def test_json_patch_escapes_and_failure():
    family = registry.get("json_patch")
    assert family.reference_solve({"document": {"a/b": {"~x": 1}}, "patch": [{"op": "test", "path": "/a~1b/~0x", "value": 1}]})["ok"] is True
    assert family.reference_solve({"document": {"x": 1}, "patch": [{"op": "remove", "path": "/x~2"}]})["ok"] is False


def test_interval_parser_dp_references():
    assert registry.get("interval_merge").reference_solve({"intervals": [[2, 4], [1, 2]], "target": [1, 4]})["covered_length"] == 3
    assert registry.get("string_parser").reference_solve({"expr": "-7 / 2"}) == {"ok": True, "value": -3}
    assert registry.get("dp_counting").reference_solve({"n": 5, "allowed_steps": [1, 2], "broken": []}) == 8
