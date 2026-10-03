"""Tests for file_io module.

Verifies that file saving works correctly for large files containing
UTF-8 multibyte characters (emoji, CJK, etc.).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from file_io import allocate_save_buffer, save_file

# 64KB threshold
BUFFER_SIZE = 65536


def test_allocate_buffer_ascii():
    """ASCII content: byte length equals character count."""
    content = "a" * 100
    buf = allocate_save_buffer(content)
    assert len(buf) == 100


def test_allocate_buffer_multibyte():
    """Multibyte content: buffer must be sized by byte count, not char count."""
    # U+1F600 (grinning face) is 4 bytes in UTF-8
    emoji = "\U0001F600"
    content = emoji * 100
    buf = allocate_save_buffer(content)
    # 100 characters * 4 bytes each = 400 bytes
    assert len(buf) == 400
    assert len(buf) != len(content)  # char count would be 100


def test_allocate_buffer_cjk():
    """CJK characters: each is 3 bytes in UTF-8."""
    # U+4E16 is a CJK character (3 bytes in UTF-8)
    content = "世" * 100
    buf = allocate_save_buffer(content)
    assert len(buf) == 300


def test_save_large_emoji_file():
    """Save a file >64KB containing emoji characters without crash."""
    # 20,000 emoji * 4 bytes each = 80,000 bytes (>64KB)
    content = "\U0001F600" * 20000
    assert len(content.encode("utf-8")) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        filepath = f.name

    try:
        bytes_written = save_file(filepath, content)
        assert bytes_written == 80000

        with open(filepath, "rb") as f:
            saved = f.read()
        assert saved.decode("utf-8") == content
    finally:
        os.unlink(filepath)


def test_save_large_mixed_file():
    """Save a file >64KB with mixed ASCII and CJK text."""
    ascii_part = "Hello " * 5000  # 30,000 bytes
    cjk_part = "世界" * 10000  # 60,000 bytes (2 chars * 3 bytes * 10000)
    content = ascii_part + cjk_part
    assert len(content.encode("utf-8")) > BUFFER_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        filepath = f.name

    try:
        bytes_written = save_file(filepath, content)
        assert bytes_written == len(content.encode("utf-8"))

        with open(filepath, "rb") as f:
            saved = f.read()
        assert saved.decode("utf-8") == content
    finally:
        os.unlink(filepath)


def test_save_boundary_multibyte():
    """Char count < 64K but byte count > 64K (boundary condition)."""
    # 20,000 four-byte emoji = 20K chars but 80KB on disk
    content = "\U0001F600" * 20000
    char_count = len(content)
    byte_count = len(content.encode("utf-8"))

    assert char_count < BUFFER_SIZE  # 20,000 chars < 65,536
    assert byte_count > BUFFER_SIZE  # 80,000 bytes > 65,536

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        filepath = f.name

    try:
        bytes_written = save_file(filepath, content)
        assert bytes_written == byte_count

        with open(filepath, "rb") as f:
            saved = f.read()
        assert saved.decode("utf-8") == content
    finally:
        os.unlink(filepath)


def test_save_small_file_still_works():
    """Small files (<64KB) should continue to work as before."""
    content = "small file content"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        filepath = f.name

    try:
        bytes_written = save_file(filepath, content)
        assert bytes_written == len(content.encode("utf-8"))

        with open(filepath, "rb") as f:
            saved = f.read()
        assert saved.decode("utf-8") == content
    finally:
        os.unlink(filepath)
