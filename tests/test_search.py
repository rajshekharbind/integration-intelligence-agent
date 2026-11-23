from src.search import generate_search_queries, is_official_domain, execute_search


def test_generate_search_queries():
    queries = generate_search_queries("HubSpot")
    assert len(queries) == 5
    assert "HubSpot official developer API documentation" in queries[0]
    assert "authentication" in queries[1]
    assert "pricing" in queries[2]
    assert "rate limits" in queries[3]
    assert "MCP server" in queries[4]


def test_is_official_domain():
    assert is_official_domain("https://developers.hubspot.com/docs", "HubSpot", "hubspot.com") is True
    assert is_official_domain("https://docs.github.com/en/rest", "GitHub", "github.com") is True
    assert is_official_domain("https://medium.com/@dev/how-to-use-stripe", "Stripe", "stripe.com") is False
    assert is_official_domain("https://cloud.google.com/looker/docs", "Looker", "cloud.google.com") is True


def test_search_knowledge_fallback():
    hits = execute_search("HubSpot official developer API documentation", app_name="HubSpot")
    assert len(hits) > 0
    assert any("hubspot" in hit["url"].lower() for hit in hits)
