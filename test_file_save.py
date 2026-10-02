"""Tests for file_save module.

Verifies that files save correctly regardless of size or character
encoding, covering the regression where files >64KB with UTF-8
multibyte characters caused a segmentation fault.
"""

import os
import tempfile

from file_save import save_file


def test_save_large_file_with_emoji():
    """Save a 70KB file containing emoji characters."""
    # Each emoji is 4 bytes in UTF-8; 70KB of emoji content
    emoji = "\U0001f600"  # 😀
    char_count = (70 * 1024) // len(emoji.encode("utf-8"))
    content = emoji * char_count
    assert len(content.encode("utf-8")) >= 70 * 1024

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_64kb_file_with_cjk():
    """Save a 64KB file containing CJK characters."""
    # CJK characters are 3 bytes each in UTF-8
    cjk_char = "世"  # 世
    byte_per_char = len(cjk_char.encode("utf-8"))
    char_count = (64 * 1024 + byte_per_char - 1) // byte_per_char
    content = cjk_char * char_count
    assert len(content.encode("utf-8")) >= 64 * 1024

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_large_ascii_file():
    """Save a 70KB ASCII-only file (regression guard)."""
    content = "A" * (70 * 1024)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_round_trip_integrity():
    """Verify saved content matches original (round-trip integrity)."""
    # Mix of ASCII, emoji, and CJK to stress byte/char mismatch
    content = ("Hello 世界! 😀🎉 " * 5000)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)


def test_save_small_file():
    """Save a small file (under 64KB) to confirm no regression."""
    content = "Small file with emoji 😀\n"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    try:
        save_file(path, content)
        with open(path, "r", encoding="utf-8") as f:
            result = f.read()
        assert result == content
    finally:
        os.unlink(path)
