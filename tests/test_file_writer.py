"""Tests for the UTF-8-aware buffered file writer.

Covers the segfault scenario from issue #1895: saving files >64KB with
UTF-8 multibyte characters that straddle the buffer boundary.
"""

import os
import tempfile

from src.file_writer import BUFFER_SIZE, _utf8_safe_split, read_file, save_file


class TestUtf8SafeSplit:
    """Test the boundary-splitting logic directly."""

    def test_ascii_at_boundary(self):
        """ASCII byte at boundary needs no adjustment."""
        data = b"A" * 100
        assert _utf8_safe_split(data, 50) == 50

    def test_split_before_2byte_sequence(self):
        """2-byte sequence starting at boundary-1 should not be split."""
        # Build data: ASCII up to position 49, then a 2-byte char (é = C3 A9)
        data = b"A" * 49 + "é".encode("utf-8") + b"B" * 10
        # Boundary at 50 lands on the continuation byte (A9) of é
        assert _utf8_safe_split(data, 50) == 49

    def test_split_before_3byte_sequence(self):
        """3-byte sequence straddling boundary should not be split."""
        # CJK character 中 = E4 B8 AD (3 bytes)
        data = b"A" * 49 + "中".encode("utf-8") + b"B" * 10
        # Boundary at 50 lands on first continuation byte
        assert _utf8_safe_split(data, 50) == 49

    def test_split_before_4byte_sequence(self):
        """4-byte emoji straddling boundary should not be split."""
        # Emoji 😀 = F0 9F 98 80 (4 bytes)
        data = b"A" * 49 + "😀".encode("utf-8") + b"B" * 10
        # Boundary at 50 lands on first continuation byte
        assert _utf8_safe_split(data, 50) == 49

    def test_complete_multibyte_before_boundary(self):
        """Multibyte sequence fully before boundary is not adjusted."""
        # é at positions 48-49, boundary at 50 is after it
        data = b"A" * 48 + "é".encode("utf-8") + b"B" * 10
        assert _utf8_safe_split(data, 50) == 50

    def test_boundary_at_data_end(self):
        """Boundary at or past data length returns data length."""
        data = b"A" * 10
        assert _utf8_safe_split(data, 10) == 10
        assert _utf8_safe_split(data, 20) == 10

    def test_4byte_emoji_at_boundary_minus_1(self):
        """4-byte emoji starting at byte 65534 straddles 64KB boundary."""
        data = b"A" * (BUFFER_SIZE - 2) + "😀".encode("utf-8") + b"B" * 10
        # Boundary at BUFFER_SIZE lands on byte 2 of the emoji
        assert _utf8_safe_split(data, BUFFER_SIZE) == BUFFER_SIZE - 2


class TestSaveFile:
    """Integration tests for save_file with UTF-8 content."""

    def test_save_small_ascii_file(self):
        """Small ASCII files save correctly."""
        content = "Hello, world!"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            assert read_file(filepath) == content
        finally:
            os.unlink(filepath)

    def test_save_small_utf8_file(self):
        """Small files with multibyte characters save correctly."""
        content = "Hello 😀 世界 café"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            assert read_file(filepath) == content
        finally:
            os.unlink(filepath)

    def test_save_large_ascii_file(self):
        """Large ASCII files (>64KB) save correctly."""
        content = "A" * (BUFFER_SIZE + 1000)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            assert read_file(filepath) == content
        finally:
            os.unlink(filepath)

    def test_save_large_utf8_file_with_emoji(self):
        """Large files with emoji crossing 64KB boundary save correctly.

        This is the exact scenario from issue #1895: ~70KB of text with
        emoji characters should save without crashing.
        """
        # Create content where emoji straddle the 64KB boundary
        # Each emoji (😀) is 4 bytes in UTF-8
        ascii_prefix = "A" * (BUFFER_SIZE - 2)  # 2 bytes short of boundary
        emoji_section = "😀" * 1000  # Emoji that will cross the boundary
        content = ascii_prefix + emoji_section
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            result = read_file(filepath)
            assert result == content
        finally:
            os.unlink(filepath)

    def test_save_large_utf8_file_with_cjk(self):
        """Large files with CJK characters crossing boundary save correctly."""
        # CJK characters are 3 bytes in UTF-8
        ascii_prefix = "A" * (BUFFER_SIZE - 1)  # 1 byte short of boundary
        cjk_section = "中文测试" * 500
        content = ascii_prefix + cjk_section
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            result = read_file(filepath)
            assert result == content
        finally:
            os.unlink(filepath)

    def test_save_exactly_64kb_ending_with_emoji(self):
        """File of exactly 64KB ending with a 4-byte emoji saves correctly."""
        # Make content that encodes to exactly BUFFER_SIZE bytes
        emoji = "😀"  # 4 bytes
        ascii_fill = "A" * (BUFFER_SIZE - 4)
        content = ascii_fill + emoji
        assert len(content.encode("utf-8")) == BUFFER_SIZE
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            result = read_file(filepath)
            assert result == content
        finally:
            os.unlink(filepath)

    def test_save_mixed_content_near_boundary(self):
        """Mixed ASCII and multibyte content near buffer boundary."""
        # Alternate ASCII and emoji near the boundary
        parts = []
        current_size = 0
        while current_size < BUFFER_SIZE + 5000:
            parts.append("Hello ")  # 6 bytes
            parts.append("😀")     # 4 bytes
            parts.append("世界 ")   # 7 bytes (3+3+1)
            current_size += 17
        content = "".join(parts)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            result = read_file(filepath)
            assert result == content
        finally:
            os.unlink(filepath)

    def test_roundtrip_preserves_content(self):
        """Content round-trips through save/read without corruption."""
        # ~70KB of mixed content as described in the issue
        content = ("Hello 😀 World 🌍 " * 5000)[:70000]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            filepath = f.name
        try:
            save_file(content, filepath)
            result = read_file(filepath)
            assert result == content
            assert len(result) == len(content)
        finally:
            os.unlink(filepath)
