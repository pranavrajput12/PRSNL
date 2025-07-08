import pytest

# Assuming your utility functions are in a module like 'app.utils.url_utils'
# For this test, we'll mock simple versions or assume they are directly available

def is_valid_url(url: str) -> bool:
    # Simple regex for URL validation
    import re
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$'
        , re.IGNORECASE)
    return re.match(regex, url) is not None

def get_domain(url: str) -> str:
    from urllib.parse import urlparse
    parsed_uri = urlparse(url)
    return '{uri.netloc}'.format(uri=parsed_uri)

def normalize_url(url: str) -> str:
    from urllib.parse import urlparse, urlunparse
    parsed_url = urlparse(url)
    # Remove query parameters and fragments for normalization
    normalized_url = parsed_url._replace(query="", fragment="")
    return urlunparse(normalized_url)


class TestUrlUtils:

    @pytest.mark.parametrize("url, expected", [
        ("http://example.com", True),
        ("https://www.example.com/path/to/page?query=1", True),
        ("ftp://ftp.example.com/file.txt", True),
        ("http://localhost:8000", True),
        ("invalid-url", False),
        ("example.com", False),
        ("http:///invalid.com", False),
    ])
    def test_is_valid_url(self, url, expected):
        assert is_valid_url(url) == expected

    @pytest.mark.parametrize("url, expected", [
        ("http://example.com/path", "example.com"),
        ("https://www.sub.domain.co.uk/page", "www.sub.domain.co.uk"),
        ("http://localhost:8080/api", "localhost:8080"),
        ("ftp://user:pass@ftp.example.com/file.txt", "ftp.example.com"),
        ("invalid-url", ""), # urlparse returns empty netloc for invalid urls
    ])
    def test_get_domain(self, url, expected):
        assert get_domain(url) == expected

    @pytest.mark.parametrize("url, expected", [
        ("http://example.com/path?query=1&param=2#fragment", "http://example.com/path"),
        ("https://www.example.com/", "https://www.example.com/"),
        ("http://example.com", "http://example.com"),
        ("http://example.com/#fragment", "http://example.com/"),
    ])
    def test_normalize_url(self, url, expected):
        assert normalize_url(url) == expected
