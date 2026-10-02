"""Tests for the file handler module.

Covers the UTF-8 buffer sizing fix: files larger than 64KB that
contain multibyte characters must save and round-trip correctly.
"""

import os
import tempfile

import pytest

from src.file_handler import CHUNK_SIZE, _encode_content, load_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a temporary file path inside a temporary directory."""
    return str(tmp_path / "output.txt")


class TestEncodeContent:
    """Tests for _encode_content."""

    def test_ascii_string(self):
        result = _encode_content("hello")
        assert result == b"hello"

    def test_bytes_passthrough(self):
        data = b"\x00\x01\x02"
        assert _encode_content(data) is data

    def test_multibyte_utf8(self):
        text = "\U0001f600"  # 😀 — 4-byte UTF-8 sequence
        result = _encode_content(text)
        assert len(result) == 4
        assert result == text.encode("utf-8")

    def test_cjk_characters(self):
        text = "世界"  # 世界 — 3-byte UTF-8 each
        result = _encode_content(text)
        assert len(result) == 6


class TestSaveFile:
    """Tests for save_file."""

    def test_save_small_ascii(self, tmp_path_file):
        save_file(tmp_path_file, "hello world")
        with open(tmp_path_file, "rb") as f:
            assert f.read() == b"hello world"

    def test_save_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "a" / "b" / "file.txt")
        save_file(path, "nested")
        assert os.path.isfile(path)

    def test_save_large_ascii_file(self, tmp_path_file):
        """ASCII-only content larger than 64KB saves correctly."""
        content = "A" * (CHUNK_SIZE + 1024)
        save_file(tmp_path_file, content)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == content.encode("utf-8")

    def test_save_large_multibyte_file(self, tmp_path_file):
        """70KB+ of emoji content must save without error.

        This is the primary regression test for the buffer overflow.
        Each emoji is 4 bytes in UTF-8, so 18000 emoji = 72000 bytes,
        well above the 65536-byte chunk boundary.
        """
        emoji_count = 18000  # 18000 * 4 bytes = 72000 bytes > 64KB
        content = "\U0001f600" * emoji_count
        save_file(tmp_path_file, content)

        with open(tmp_path_file, "rb") as f:
            saved = f.read()
        assert len(saved) == emoji_count * 4
        assert saved == content.encode("utf-8")

    def test_save_multibyte_straddling_chunk_boundary(self, tmp_path_file):
        """A 4-byte UTF-8 sequence straddling the 65536 offset saves correctly.

        Fill up to byte offset 65534 with ASCII, then place an emoji
        whose 4 bytes span offsets 65534..65537.  The old character-count
        buffer would allocate only 65536 bytes and overflow.
        """
        prefix = "X" * 65534  # 65534 ASCII bytes
        suffix = "\U0001f600"  # 4-byte emoji straddles the boundary
        content = prefix + suffix
        save_file(tmp_path_file, content)

        with open(tmp_path_file, "rb") as f:
            saved = f.read()
        expected = content.encode("utf-8")
        assert saved == expected
        assert len(saved) == 65534 + 4

    def test_save_cjk_over_64kb(self, tmp_path_file):
        """CJK content (3-byte sequences) over 64KB saves correctly."""
        char_count = 25000  # 25000 * 3 bytes = 75000 bytes > 64KB
        content = "世" * char_count
        save_file(tmp_path_file, content)

        with open(tmp_path_file, "rb") as f:
            saved = f.read()
        assert len(saved) == char_count * 3
        assert saved == content.encode("utf-8")

    def test_save_bytes_input(self, tmp_path_file):
        data = b"\xff\xfe\xfd"
        save_file(tmp_path_file, data)
        with open(tmp_path_file, "rb") as f:
            assert f.read() == data


class TestRoundTrip:
    """Tests for save + load round-trip integrity."""

    def test_roundtrip_ascii(self, tmp_path_file):
        content = "hello world"
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_roundtrip_large_emoji(self, tmp_path_file):
        """Round-trip 70KB of emoji content — byte-for-byte integrity."""
        content = "\U0001f600" * 18000
        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content

    def test_roundtrip_mixed_content(self, tmp_path_file):
        """Round-trip mixed ASCII + multibyte content over 64KB."""
        parts = []
        for i in range(5000):
            parts.append(f"line {i}: \U0001f4dd ☃ data\n")
        content = "".join(parts)
        assert len(content.encode("utf-8")) > CHUNK_SIZE

        save_file(tmp_path_file, content)
        assert load_file(tmp_path_file) == content


class TestLoadFile:
    """Tests for load_file."""

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_file("/nonexistent/path/file.txt")

    def test_load_utf8_content(self, tmp_path_file):
        content = "café \U0001f37a"
        with open(tmp_path_file, "wb") as f:
            f.write(content.encode("utf-8"))
        assert load_file(tmp_path_file) == content
