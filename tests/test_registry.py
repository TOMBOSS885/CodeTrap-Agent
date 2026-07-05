from codetrap.core.registry import registry


def test_registry_loads_all_families():
    ids = {family.family_id for family in registry.all()}
    assert ids == {"graph_paths", "json_patch", "interval_merge", "string_parser", "dp_counting"}

