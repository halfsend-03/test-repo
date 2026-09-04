"""Tests for file_handler – focused on the UTF-8 buffer-overflow fix.

Covers:
  - Small ASCII file (baseline sanity check)
  - Large (>64 KB) ASCII file (no multibyte – should always have worked)
  - Large (>64 KB) multibyte UTF-8 file (the crash scenario from #1876)
  - Exactly 64 KB boundary with multibyte characters (edge case)
  - Mixed ASCII / multibyte content crossing the 64 KB boundary
"""

import os
import sys
import tempfile

import pytest

# Allow importing from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_handler import CHUNK_SIZE, read_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a helper that yields a fresh file path inside tmp_path."""

    def _make(name: str = "output.txt") -> str:
        return str(tmp_path / name)

    return _make


class TestSaveFile:
    """Verify save_file round-trips content correctly."""

    def test_small_ascii(self, tmp_path_file):
        path = tmp_path_file()
        content = "hello world"
        save_file(path, content)
        assert read_file(path) == content

    def test_large_ascii(self, tmp_path_file):
        """ASCII content >64 KB – should work even before the fix."""
        path = tmp_path_file()
        content = "A" * (CHUNK_SIZE + 1024)
        save_file(path, content)
        assert read_file(path) == content

    def test_large_multibyte_utf8(self, tmp_path_file):
        """Multibyte content >64 KB – the crash scenario from #1876.

        Each emoji is 4 bytes in UTF-8. 20 000 emoji = 80 000 bytes,
        which exceeds the 64 KB (65 536 byte) chunk boundary.
        """
        path = tmp_path_file()
        emoji = "\U0001f600"  # grinning face, 4 bytes in UTF-8
        content = emoji * 20_000  # 80 000 bytes
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        save_file(path, content)
        result = read_file(path)
        assert result == content

    def test_exact_boundary_multibyte(self, tmp_path_file):
        """Content whose byte length is exactly CHUNK_SIZE."""
        path = tmp_path_file()
        # 2-byte character (e.g. 'e' with accent U+00E9)
        char = "é"  # 2 bytes in UTF-8
        count = CHUNK_SIZE // 2  # exactly 65 536 bytes
        content = char * count
        assert len(content.encode("utf-8")) == CHUNK_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_mixed_ascii_multibyte_crossing_boundary(self, tmp_path_file):
        """Mixed ASCII and multibyte where the boundary falls mid-chunk."""
        path = tmp_path_file()
        ascii_part = "x" * (CHUNK_SIZE - 10)
        multibyte_part = "\U0001f4a9" * 1000  # 4 bytes each = 4 000 bytes
        content = ascii_part + multibyte_part
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        save_file(path, content)
        assert read_file(path) == content

    def test_empty_file(self, tmp_path_file):
        path = tmp_path_file()
        save_file(path, "")
        assert read_file(path) == ""

    def test_cjk_characters(self, tmp_path_file):
        """CJK characters (3 bytes each in UTF-8) exceeding 64 KB."""
        path = tmp_path_file()
        cjk_char = "世"  # 'world' in Chinese, 3 bytes
        count = (CHUNK_SIZE // 3) + 1000
        content = cjk_char * count
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        save_file(path, content)
        assert read_file(path) == content
