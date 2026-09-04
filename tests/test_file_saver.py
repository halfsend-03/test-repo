"""Tests for file_saver module.

Covers boundary cases for UTF-8 multibyte character handling around
the 64KB buffer threshold.
"""

import os
import tempfile

from src.file_saver import BUFFER_SIZE, _calculate_buffer_size, save_file


class TestCalculateBufferSize:
    """Tests for buffer size calculation."""

    def test_ascii_under_threshold(self):
        content = "a" * (BUFFER_SIZE - 1)
        assert _calculate_buffer_size(content) == BUFFER_SIZE

    def test_ascii_at_threshold(self):
        content = "a" * BUFFER_SIZE
        assert _calculate_buffer_size(content) == BUFFER_SIZE

    def test_ascii_over_threshold(self):
        content = "a" * (BUFFER_SIZE + 1)
        assert _calculate_buffer_size(content) == BUFFER_SIZE + 1

    def test_multibyte_under_threshold_by_chars_over_by_bytes(self):
        """Multibyte content where char count < 64KB but byte count > 64KB.

        This is the exact scenario that caused the original crash:
        emoji characters are 4 bytes each in UTF-8, so 20000 emoji
        characters = 80000 bytes, which exceeds the 64KB buffer.
        """
        # Each emoji is 4 bytes in UTF-8
        emoji_count = BUFFER_SIZE // 4 + 1000
        content = "\U0001f600" * emoji_count  # 😀
        byte_length = len(content.encode("utf-8"))
        assert byte_length > BUFFER_SIZE
        assert _calculate_buffer_size(content) == byte_length

    def test_multibyte_cjk_over_threshold(self):
        """CJK characters are 3 bytes each in UTF-8."""
        # Each CJK char is 3 bytes
        cjk_count = BUFFER_SIZE // 3 + 1000
        content = "世" * cjk_count  # 世
        byte_length = len(content.encode("utf-8"))
        assert byte_length > BUFFER_SIZE
        assert _calculate_buffer_size(content) == byte_length


class TestSaveFile:
    """Tests for file saving functionality."""

    def test_save_small_ascii_file(self, tmp_path):
        path = tmp_path / "small_ascii.txt"
        content = "Hello, world!"
        save_file(str(path), content)
        assert path.read_bytes() == content.encode("utf-8")

    def test_save_64kb_ascii(self, tmp_path):
        """64KB ASCII-only file saves successfully."""
        path = tmp_path / "64kb_ascii.txt"
        content = "a" * BUFFER_SIZE
        save_file(str(path), content)
        assert path.read_bytes() == content.encode("utf-8")

    def test_save_64kb_multibyte(self, tmp_path):
        """64KB of multibyte content saves successfully."""
        path = tmp_path / "64kb_multibyte.txt"
        # Create content whose byte length is exactly 64KB
        # Each emoji is 4 bytes, so BUFFER_SIZE // 4 emojis = 64KB
        emoji_count = BUFFER_SIZE // 4
        content = "\U0001f600" * emoji_count
        save_file(str(path), content)
        result = path.read_bytes()
        assert result == content.encode("utf-8")

    def test_save_65kb_ascii(self, tmp_path):
        """65KB ASCII-only file saves successfully."""
        path = tmp_path / "65kb_ascii.txt"
        content = "a" * (BUFFER_SIZE + 1024)
        save_file(str(path), content)
        assert path.read_bytes() == content.encode("utf-8")

    def test_save_65kb_multibyte(self, tmp_path):
        """65KB multibyte file saves successfully (was crashing before fix)."""
        path = tmp_path / "65kb_multibyte.txt"
        # Create ~70KB of emoji content (the reproduction scenario)
        emoji_count = 70000 // 4  # ~70KB of emoji
        content = "\U0001f600" * emoji_count
        byte_length = len(content.encode("utf-8"))
        assert byte_length > BUFFER_SIZE  # Confirm we exceed 64KB

        save_file(str(path), content)
        result = path.read_bytes()
        assert result == content.encode("utf-8")

    def test_save_large_mixed_content(self, tmp_path):
        """Mixed ASCII and multibyte content over 64KB saves correctly."""
        path = tmp_path / "mixed.txt"
        # Mix of ASCII and emoji to exceed 64KB
        ascii_part = "Hello " * 5000  # 30KB
        emoji_part = "\U0001f600" * 10000  # 40KB
        content = ascii_part + emoji_part
        byte_length = len(content.encode("utf-8"))
        assert byte_length > BUFFER_SIZE

        save_file(str(path), content)
        result = path.read_bytes()
        assert result == content.encode("utf-8")

    def test_save_roundtrip_preserves_content(self, tmp_path):
        """Reading back saved file produces byte-identical content."""
        path = tmp_path / "roundtrip.txt"
        content = "Hello 世界! 🎉🎊 " * 5000  # Mixed multibyte content
        save_file(str(path), content)
        with open(str(path), "rb") as f:
            result = f.read()
        assert result == content.encode("utf-8")
        assert result.decode("utf-8") == content

    def test_save_rejects_non_string(self, tmp_path):
        """Non-string content raises TypeError."""
        path = tmp_path / "invalid.txt"
        try:
            save_file(str(path), 12345)
            assert False, "Expected TypeError"
        except TypeError:
            pass
