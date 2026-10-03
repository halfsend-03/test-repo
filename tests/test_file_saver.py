"""Tests for file_saver module.

Verifies that save_file correctly handles large files containing
multibyte UTF-8 characters, including edge cases around the 64KB
buffer boundary.
"""

import os
import tempfile

from src.file_saver import BUFFER_SIZE, save_file


def test_save_large_file_with_multibyte_characters():
    """Save ~70KB of text containing emoji and CJK characters."""
    # Each emoji is 4 bytes in UTF-8; 18000 emoji ≈ 72KB
    content = "\U0001F600" * 18000
    assert len(content.encode("utf-8")) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == content.encode("utf-8")
        assert bytes_written == len(content.encode("utf-8"))
    finally:
        os.unlink(path)


def test_save_exactly_64kb_multibyte():
    """Save exactly 64KB of multibyte text."""
    # 4-byte emoji: 16384 of them = exactly 65536 bytes = 64KB
    content = "\U0001F600" * (BUFFER_SIZE // 4)
    assert len(content.encode("utf-8")) == BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == content.encode("utf-8")
        assert bytes_written == BUFFER_SIZE
    finally:
        os.unlink(path)


def test_multibyte_character_straddling_boundary():
    """A multibyte character straddling the 64KB boundary must not be split."""
    # Fill to just before the boundary with ASCII, then add a 4-byte emoji
    # so the emoji straddles the 64KB mark.
    ascii_prefix = "A" * (BUFFER_SIZE - 2)  # 2 bytes short of 64KB
    content = ascii_prefix + "\U0001F600"  # emoji adds 4 bytes, crossing 64KB

    encoded = content.encode("utf-8")
    assert len(encoded) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == encoded
        assert bytes_written == len(encoded)
    finally:
        os.unlink(path)


def test_save_1mb_pure_emoji():
    """Save 1MB of pure emoji/CJK text."""
    # 4-byte emoji: 262144 of them = 1MB
    content = "\U0001F680" * 262144
    expected = content.encode("utf-8")
    assert len(expected) == 1048576  # 1MB

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == expected
        assert bytes_written == len(expected)
    finally:
        os.unlink(path)


def test_mixed_ascii_and_multibyte_above_64kb():
    """Mixed ASCII + multibyte at various ratios above 64KB."""
    # Alternate ASCII and CJK characters
    cjk_char = "世"  # 3 bytes in UTF-8
    content = ""
    while len(content.encode("utf-8")) < BUFFER_SIZE + 10000:
        content += "Hello" + cjk_char * 5

    encoded = content.encode("utf-8")
    assert len(encoded) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == encoded
        assert bytes_written == len(encoded)
    finally:
        os.unlink(path)


def test_save_small_ascii_file():
    """Files under 64KB with ASCII content should still work."""
    content = "Hello, World!\n" * 100

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file(content, path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == content.encode("utf-8")
        assert bytes_written == len(content.encode("utf-8"))
    finally:
        os.unlink(path)


def test_save_empty_content():
    """Saving an empty string should produce an empty file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        bytes_written = save_file("", path)
        with open(path, "rb") as f:
            data = f.read()
        assert data == b""
        assert bytes_written == 0
    finally:
        os.unlink(path)
