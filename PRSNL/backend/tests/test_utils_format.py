import pytest

# Assuming your utility functions are in a module like 'app.utils.format_utils'
# For this test, we'll mock simple versions or assume they are directly available

def format_file_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024**2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_bytes / (1024**2):.2f} MB"
    else:
        return f"{size_in_bytes / (1024**3):.2f} GB"

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


class TestFormatUtils:

    @pytest.mark.parametrize("size_in_bytes, expected", [
        (0, "0 B"),
        (100, "100 B"),
        (1023, "1023 B"),
        (1024, "1.00 KB"),
        (1536, "1.50 KB"),
        (1024**2 - 1, "1023.99 KB"),
        (1024**2, "1.00 MB"),
        (1.5 * 1024**2, "1.50 MB"),
        (1024**3 - 1, "1023.99 MB"),
        (1024**3, "1.00 GB"),
        (1.5 * 1024**3, "1.50 GB"),
    ])
    def test_format_file_size(self, size_in_bytes, expected):
        assert format_file_size(size_in_bytes) == expected

    @pytest.mark.parametrize("text, max_length, suffix, expected", [
        ("hello world", 20, "...", "hello world"),
        ("hello world", 5, "...", "he..."),
        ("a very long string that needs to be truncated", 10, "...", "a very..."),
        ("short", 3, "..", "s.."),
        ("short", 5, "", "short"),
        ("short", 4, "", "shor"),
    ])
    def test_truncate_string(self, text, max_length, suffix, expected):
        assert truncate_string(text, max_length, suffix) == expected
