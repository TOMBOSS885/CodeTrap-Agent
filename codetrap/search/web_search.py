from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

from codetrap.core.problem_bundle import SearchSource


def search_related_problems(query: str, limit: int = 5, timeout_sec: float = 4.0) -> tuple[list[SearchSource], str]:
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 CodeTrap-Agent/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            text = response.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return [], f"online_search_failed: {type(exc).__name__}"

    results: list[SearchSource] = []
    blocks = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?(?:<a[^>]+class="result__snippet"[^>]*>(.*?)</a>|<div[^>]+class="result__snippet"[^>]*>(.*?)</div>)', text, re.S)
    for raw_url, raw_title, raw_snippet_a, raw_snippet_div in blocks:
        title = _strip_tags(raw_title)
        snippet = _strip_tags(raw_snippet_a or raw_snippet_div)
        actual_url = _decode_duckduckgo_url(html.unescape(raw_url))
        if title and actual_url:
            results.append(SearchSource(title=title, url=actual_url, snippet=snippet))
        if len(results) >= limit:
            break
    return results, "online_search_ok" if results else "online_search_empty"


def _strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _decode_duckduckgo_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    params = urllib.parse.parse_qs(parsed.query)
    if "uddg" in params:
        return params["uddg"][0]
    return value

