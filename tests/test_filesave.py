"""Tests for file save with UTF-8 multibyte character handling."""

import os
import tempfile

from src.filesave import _calculate_buffer_size, save_file


class TestCalculateBufferSize:
    """Tests for buffer size calculation."""

    def test_ascii_only(self):
        """ASCII characters: byte length equals character count."""
        content = "a" * 100
        assert _calculate_buffer_size(content) == 100

    def test_emoji_characters(self):
        """Emoji characters are 4 bytes each in UTF-8."""
        content = "\U0001f389" * 10  # party popper emoji
        assert _calculate_buffer_size(content) == 40

    def test_cjk_characters(self):
        """CJK characters are 3 bytes each in UTF-8."""
        content = "世" * 10  # Chinese character
        assert _calculate_buffer_size(content) == 30

    def test_mixed_content(self):
        """Mixed ASCII and multibyte characters."""
        # 5 ASCII (5 bytes) + 5 emoji (20 bytes) = 25 bytes
        content = "hello" + "\U0001f389" * 5
        assert _calculate_buffer_size(content) == 25


class TestSaveFile:
    """Tests for saving files with various content types and sizes."""

    def test_save_ascii_under_64kb(self):
        """Save a small ASCII file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            content = "Hello, World!"
            save_file(path, content)
            with open(path, "rb") as f:
                assert f.read() == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_ascii_over_64kb(self):
        """Save a large ASCII file (>64KB)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            content = "x" * 70000  # 70KB of ASCII
            save_file(path, content)
            with open(path, "rb") as f:
                data = f.read()
            assert len(data) == 70000
            assert data == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_emoji_over_64kb(self):
        """Save >64KB of emoji characters without crash.

        This is the exact scenario from issue #2377: ~70KB of emoji
        characters caused a segfault because the buffer was allocated
        based on character count (len(content)) instead of byte length
        (len(content.encode('utf-8'))).

        Each emoji is 4 bytes, so 18000 emoji = 72000 bytes > 64KB.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            content = "\U0001f389" * 18000  # 72KB of emoji
            save_file(path, content)
            with open(path, "rb") as f:
                data = f.read()
            assert len(data) == 72000
            assert data == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_mixed_at_64kb_boundary(self):
        """Save exactly 64KB of mixed ASCII + multibyte characters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            # 32768 ASCII bytes + 8192 emoji * 4 bytes = 65536 bytes
            content = "a" * 32768 + "\U0001f389" * 8192
            save_file(path, content)
            with open(path, "rb") as f:
                data = f.read()
            assert len(data) == 65536
            assert data == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_emoji_just_under_64kb(self):
        """Save just under 64KB of emoji characters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            # 16383 emoji * 4 bytes = 65532 bytes (just under 64KB)
            content = "\U0001f389" * 16383
            save_file(path, content)
            with open(path, "rb") as f:
                data = f.read()
            assert len(data) == 65532
            assert data == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_cjk_over_64kb(self):
        """Save >64KB of CJK characters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            # 23000 CJK chars * 3 bytes = 69000 bytes > 64KB
            content = "世" * 23000
            save_file(path, content)
            with open(path, "rb") as f:
                data = f.read()
            assert len(data) == 69000
            assert data == content.encode("utf-8")
        finally:
            os.unlink(path)

    def test_save_creates_parent_directories(self):
        """Save creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sub", "dir", "file.txt")
            content = "nested file content"
            save_file(path, content)
            with open(path, "rb") as f:
                assert f.read() == content.encode("utf-8")
