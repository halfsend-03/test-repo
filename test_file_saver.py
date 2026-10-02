"""Tests for file_saver module.

Verifies that the save utility correctly handles large files with
multibyte UTF-8 characters, including edge cases at chunk boundaries.
"""

import os
import tempfile

from file_saver import CHUNK_SIZE, save_file


def test_save_large_file_with_multibyte_utf8():
    """Save ~70KB of emoji text without crashing."""
    # Each emoji is 4 bytes in UTF-8; 18000 emojis = 72000 bytes > 64KB
    content = "\U0001F600" * 18000
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_multibyte_char_spanning_chunk_boundary():
    """A multibyte character at exactly the 64KB boundary is not split."""
    # Fill up to just before the boundary with ASCII, then place a
    # 4-byte emoji right at the boundary.
    ascii_prefix = "A" * (CHUNK_SIZE - 1)
    emoji = "\U0001F600"  # 4 bytes
    content = ascii_prefix + emoji + "B" * 100
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_mixed_ascii_and_multibyte_over_64kb():
    """Mixed ASCII + multibyte content totaling >64KB saves correctly."""
    # Alternate between ASCII runs and CJK characters
    segment = "Hello World! " + "世界" * 50  # mix of ASCII + CJK
    repetitions = (CHUNK_SIZE * 2) // len(segment.encode("utf-8")) + 1
    content = segment * repetitions
    assert len(content.encode("utf-8")) > CHUNK_SIZE
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_only_4byte_emoji_characters():
    """Document consisting entirely of 4-byte emoji characters (>16K chars)."""
    content = "\U0001F680" * 17000  # 68000 bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_ascii_only_over_64kb():
    """ASCII-only content >64KB saves correctly (regression guard)."""
    content = "A" * (CHUNK_SIZE + 1000)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_small_file_under_chunk_size():
    """Files under chunk size save in a single write."""
    content = "Small file content ☃"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_empty_content():
    """Empty content produces an empty file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file("", path)
        assert os.path.getsize(path) == 0
    finally:
        os.unlink(path)


def test_exact_chunk_size_boundary():
    """Content whose byte length is exactly CHUNK_SIZE."""
    content = "X" * CHUNK_SIZE
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name
    try:
        save_file(content, path)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)
