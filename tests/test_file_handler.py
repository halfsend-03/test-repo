"""Tests for file_handler module.

Covers the UTF-8 multibyte buffer overflow fix (issue #2415).
Verifies that files of various sizes and character compositions
save and round-trip correctly.
"""

import os
import tempfile

import pytest

from src.file_handler import CHUNK_SIZE, read_file, save_file


@pytest.fixture
def tmp_path_file(tmp_path):
    """Return a temporary file path for testing."""
    return str(tmp_path / "test_output.txt")


class TestSaveFileUTF8:
    """Tests for saving files with multibyte UTF-8 content."""

    def test_small_ascii_file(self, tmp_path_file):
        """ASCII-only content under 64KB saves correctly."""
        content = "Hello, world!" * 100
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(content.encode("utf-8"))

    def test_small_multibyte_file(self, tmp_path_file):
        """Multibyte UTF-8 content under 64KB saves correctly."""
        content = "Hello 🌍🌎🌏 " * 500
        assert len(content.encode("utf-8")) < CHUNK_SIZE
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(content.encode("utf-8"))

    def test_large_ascii_file(self, tmp_path_file):
        """ASCII-only content over 64KB saves correctly."""
        content = "A" * (CHUNK_SIZE + 10000)
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(content.encode("utf-8"))

    def test_large_multibyte_file(self, tmp_path_file):
        """Large file with multibyte UTF-8 characters saves correctly.

        This is the primary regression test for issue #2415: files
        over 64KB containing multibyte characters previously caused a
        segmentation fault due to buffer allocation using character
        count instead of byte length.
        """
        # ~70KB of text with emoji (4-byte UTF-8 characters)
        content = "Hello 🌍 World 🎉 " * 5000
        encoded = content.encode("utf-8")
        assert len(encoded) > CHUNK_SIZE
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(encoded)

    def test_exactly_64kb_of_4byte_emoji(self, tmp_path_file):
        """Exactly 64KB of 4-byte emoji characters (16384 chars = 65536 bytes).

        Edge case: each emoji is 4 bytes, so 16384 emoji = exactly 64KB.
        """
        content = "\U0001F600" * 16384  # grinning face emoji, 4 bytes each
        encoded = content.encode("utf-8")
        assert len(encoded) == CHUNK_SIZE
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == CHUNK_SIZE

    def test_multibyte_char_spanning_64kb_boundary(self, tmp_path_file):
        """Multibyte character that would span the 64KB chunk boundary.

        Fill just under 64KB with ASCII, then add a 4-byte emoji so
        the multibyte character straddles the boundary.
        """
        # 65534 bytes of ASCII + 1 four-byte emoji = 65538 bytes total
        ascii_part = "A" * (CHUNK_SIZE - 2)
        content = ascii_part + "\U0001F60A"  # smiling face emoji
        encoded = content.encode("utf-8")
        assert len(encoded) == CHUNK_SIZE + 2  # spans boundary
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(encoded)

    def test_63kb_multibyte_content(self, tmp_path_file):
        """63KB of multibyte content (just under the 64KB threshold)."""
        # CJK characters are 3 bytes each in UTF-8
        target_bytes = CHUNK_SIZE - 1024  # ~63KB
        num_chars = target_bytes // 3
        content = "世" * num_chars  # CJK character 世
        encoded = content.encode("utf-8")
        assert len(encoded) < CHUNK_SIZE
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(encoded)

    def test_mixed_ascii_and_multibyte_over_64kb(self, tmp_path_file):
        """Mixed ASCII + multibyte content totaling over 64KB."""
        # Mix of ASCII, 2-byte, 3-byte, and 4-byte characters
        segment = "Hello café 世界 🌍 "
        repeat_count = CHUNK_SIZE // len(segment.encode("utf-8")) + 100
        content = segment * repeat_count
        encoded = content.encode("utf-8")
        assert len(encoded) > CHUNK_SIZE
        bytes_written = save_file(tmp_path_file, content)
        result = read_file(tmp_path_file)
        assert result == content
        assert bytes_written == len(encoded)

    def test_empty_file(self, tmp_path_file):
        """Empty content saves correctly."""
        bytes_written = save_file(tmp_path_file, "")
        result = read_file(tmp_path_file)
        assert result == ""
        assert bytes_written == 0

    def test_byte_count_matches_file_size(self, tmp_path_file):
        """Returned byte count matches actual file size on disk."""
        content = "🎵🎶🎼" * 10000  # lots of 4-byte chars
        bytes_written = save_file(tmp_path_file, content)
        file_size = os.path.getsize(tmp_path_file)
        assert bytes_written == file_size
        assert file_size == len(content.encode("utf-8"))
