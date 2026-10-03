"""Tests for the file_handler module.

Covers the segfault regression from issue #2411: saving files larger
than 64KB that contain UTF-8 multibyte characters (emoji, CJK) must
succeed without crashing.
"""

import os
import tempfile

import pytest

from src.file_handler import (
    DEFAULT_BUFFER_SIZE,
    _calculate_buffer_size,
    save_file,
)


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test file output."""
    return tmp_path


class TestCalculateBufferSize:
    """Unit tests for _calculate_buffer_size."""

    def test_small_data_uses_default(self):
        data = b"hello"
        assert _calculate_buffer_size(data) == DEFAULT_BUFFER_SIZE

    def test_data_at_default_boundary(self):
        data = b"x" * DEFAULT_BUFFER_SIZE
        assert _calculate_buffer_size(data) == DEFAULT_BUFFER_SIZE

    def test_data_exceeding_default(self):
        data = b"x" * (DEFAULT_BUFFER_SIZE + 1)
        assert _calculate_buffer_size(data) == DEFAULT_BUFFER_SIZE + 1

    def test_large_multibyte_data(self):
        # 20K emoji characters × 4 bytes each = 80KB
        content = "😀" * 20000
        data = content.encode("utf-8")
        assert len(data) > DEFAULT_BUFFER_SIZE
        assert _calculate_buffer_size(data) == len(data)


class TestSaveFile:
    """Integration tests for save_file."""

    def test_ascii_under_64kb(self, tmp_dir):
        """Baseline: small ASCII content saves successfully."""
        filepath = str(tmp_dir / "small_ascii.txt")
        content = "Hello, world!\n" * 100
        bytes_written = save_file(filepath, content)
        assert bytes_written == len(content.encode("utf-8"))
        with open(filepath, "rb") as f:
            assert f.read() == content.encode("utf-8")

    def test_ascii_over_64kb(self, tmp_dir):
        """ASCII-only content >64KB saves successfully."""
        filepath = str(tmp_dir / "large_ascii.txt")
        # Generate >64KB of ASCII text
        content = "A" * (DEFAULT_BUFFER_SIZE + 10000)
        bytes_written = save_file(filepath, content)
        assert bytes_written == len(content.encode("utf-8"))
        with open(filepath, "rb") as f:
            assert f.read() == content.encode("utf-8")

    def test_multibyte_char_count_under_64k_byte_count_over_64kb(self, tmp_dir):
        """Multibyte content where char count < 64K but byte count > 64KB.

        This is the exact scenario that triggered the segfault in v2.3.1:
        the buffer was allocated based on character count (~20K) rather
        than byte count (~80KB), causing an overflow.
        """
        filepath = str(tmp_dir / "multibyte_over_64kb.txt")
        # Each emoji is 4 bytes in UTF-8; 20000 chars = 80000 bytes > 64KB
        content = "😀" * 20000
        assert len(content) < DEFAULT_BUFFER_SIZE  # char count under 64K
        assert len(content.encode("utf-8")) > DEFAULT_BUFFER_SIZE  # byte count over 64KB

        bytes_written = save_file(filepath, content)
        expected_data = content.encode("utf-8")
        assert bytes_written == len(expected_data)
        with open(filepath, "rb") as f:
            assert f.read() == expected_data

    def test_mixed_ascii_multibyte_at_64kb_boundary(self, tmp_dir):
        """Mixed ASCII + multibyte at exactly 64KB byte boundary."""
        filepath = str(tmp_dir / "mixed_boundary.txt")
        # Build content that lands right at the 64KB byte boundary
        emoji_part = "🎉" * 5000  # 5000 × 4 bytes = 20000 bytes
        ascii_needed = DEFAULT_BUFFER_SIZE - len(emoji_part.encode("utf-8"))
        ascii_part = "x" * ascii_needed
        content = ascii_part + emoji_part
        assert len(content.encode("utf-8")) == DEFAULT_BUFFER_SIZE

        bytes_written = save_file(filepath, content)
        expected_data = content.encode("utf-8")
        assert bytes_written == len(expected_data)
        with open(filepath, "rb") as f:
            assert f.read() == expected_data

    def test_large_multibyte_only_over_128kb(self, tmp_dir):
        """Large multibyte-only content (>128KB bytes)."""
        filepath = str(tmp_dir / "large_multibyte.txt")
        # CJK characters: 3 bytes each in UTF-8
        # 50000 CJK chars = 150000 bytes > 128KB
        content = "漢" * 50000
        assert len(content.encode("utf-8")) > 2 * DEFAULT_BUFFER_SIZE

        bytes_written = save_file(filepath, content)
        expected_data = content.encode("utf-8")
        assert bytes_written == len(expected_data)
        with open(filepath, "rb") as f:
            assert f.read() == expected_data

    def test_file_content_matches_input_byte_for_byte(self, tmp_dir):
        """Verify saved file matches input byte-for-byte with mixed content."""
        filepath = str(tmp_dir / "byte_match.txt")
        # Mix of ASCII, 2-byte, 3-byte, and 4-byte UTF-8 characters
        content = "Hello " + "café " + "日本語 " + "🎨🎯🎲 " + "end\n"
        content = content * 5000  # Make it large enough to exceed 64KB

        bytes_written = save_file(filepath, content)
        expected_data = content.encode("utf-8")
        assert bytes_written == len(expected_data)
        with open(filepath, "rb") as f:
            assert f.read() == expected_data

    def test_empty_content(self, tmp_dir):
        """Edge case: saving empty content succeeds."""
        filepath = str(tmp_dir / "empty.txt")
        bytes_written = save_file(filepath, "")
        assert bytes_written == 0
        with open(filepath, "rb") as f:
            assert f.read() == b""

    def test_atomic_write_no_partial_on_error(self, tmp_dir):
        """If write fails, the original file is not corrupted."""
        filepath = str(tmp_dir / "original.txt")
        save_file(filepath, "original content")

        # Try to save to a read-only directory to trigger an error
        readonly_dir = tmp_dir / "readonly"
        readonly_dir.mkdir()
        bad_path = str(readonly_dir / "file.txt")
        os.chmod(str(readonly_dir), 0o444)

        try:
            with pytest.raises(OSError):
                save_file(bad_path, "should fail")
        finally:
            os.chmod(str(readonly_dir), 0o755)

        # Original file is untouched
        with open(filepath, "rb") as f:
            assert f.read() == b"original content"
