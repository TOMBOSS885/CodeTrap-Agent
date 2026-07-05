from codetrap.search.web_search import search_related_problems


def test_search_related_problems_returns_failure_status_on_network_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise TimeoutError("blocked")

    monkeypatch.setattr("codetrap.search.web_search.urllib.request.urlopen", raise_error)
    results, status = search_related_problems("algorithm pitfalls")
    assert results == []
    assert status.startswith("online_search_failed")
