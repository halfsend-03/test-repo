"""Tests for the file writer module.

Covers the UTF-8 multibyte save crash reported in issue #2387:
files over 64KB with multibyte characters must save and round-trip
without corruption or crashes.
"""

import os
import tempfile

from src.file_writer import BUFFER_SIZE, read_file, save_file


def _roundtrip(content: str) -> str:
    """Save content to a temp file and read it back."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        save_file(content, path)
        return read_file(path)
    finally:
        os.unlink(path)


def test_small_ascii_file():
    """Files under 64KB with only ASCII should save correctly."""
    content = "a" * 1000
    assert _roundtrip(content) == content


def test_small_file_with_multibyte():
    """Files under 64KB with multibyte characters should save correctly."""
    content = "Hello 🌍🌎🌏 World! " * 100
    assert len(content.encode("utf-8")) < BUFFER_SIZE
    assert _roundtrip(content) == content


def test_large_ascii_file():
    """Files over 64KB with only ASCII should save correctly."""
    content = "x" * (BUFFER_SIZE + 1024)
    assert _roundtrip(content) == content


def test_large_file_with_multibyte_crossing_boundary():
    """Multibyte characters straddling the 64KB boundary must not crash.

    This is the primary regression test for issue #2387.
    """
    # Fill up to just before the 64KB boundary with ASCII, then add emoji
    # so that multibyte sequences straddle the boundary.
    ascii_prefix = "A" * (BUFFER_SIZE - 2)
    emoji_suffix = "🎉" * 512  # each emoji is 4 bytes in UTF-8
    content = ascii_prefix + emoji_suffix
    assert len(content.encode("utf-8")) > BUFFER_SIZE
    assert _roundtrip(content) == content


def test_file_exactly_64kb_ending_with_multibyte():
    """A file whose UTF-8 encoding is exactly 64KB, ending with a
    multibyte character, should save correctly."""
    # U+00E9 (é) is 2 bytes in UTF-8
    filler_len = BUFFER_SIZE - 2  # leave room for one 2-byte char
    content = "B" * filler_len + "é"
    assert len(content.encode("utf-8")) == BUFFER_SIZE
    assert _roundtrip(content) == content


def test_file_64kb_plus_one_byte_partial_multibyte():
    """File of 64KB + 1 byte where the extra byte is part of a 4-byte
    UTF-8 sequence."""
    # Place a 4-byte emoji right at the boundary so that 1 byte falls in
    # the first 64KB chunk and 3 bytes in the next.
    filler_len = BUFFER_SIZE - 1  # one byte of the emoji lands here
    ascii_part = "C" * filler_len
    # The emoji's 4 bytes will span: 1 byte in first chunk, 3 in second
    content = ascii_part + "🔥" + "D" * 100
    encoded = content.encode("utf-8")
    assert len(encoded) > BUFFER_SIZE
    assert _roundtrip(content) == content


def test_entirely_4byte_characters_exceeding_64kb():
    """A file composed entirely of 4-byte UTF-8 characters exceeding
    64KB must save correctly."""
    # Each emoji is 4 bytes; we need > 64KB total
    num_chars = (BUFFER_SIZE // 4) + 256
    content = "😀" * num_chars
    assert len(content.encode("utf-8")) > BUFFER_SIZE
    assert _roundtrip(content) == content


def test_cjk_characters_crossing_boundary():
    """CJK characters (3-byte UTF-8) crossing the 64KB boundary."""
    # U+4E16 (世) is 3 bytes in UTF-8
    ascii_part = "E" * (BUFFER_SIZE - 1)
    cjk_part = "世" * 1000
    content = ascii_part + cjk_part
    assert len(content.encode("utf-8")) > BUFFER_SIZE
    assert _roundtrip(content) == content


def test_mixed_multibyte_across_boundary():
    """Mix of 2-byte, 3-byte, and 4-byte characters at the boundary."""
    ascii_part = "F" * (BUFFER_SIZE - 5)
    mixed = "é世🌍" * 200  # 2 + 3 + 4 = 9 bytes per group
    content = ascii_part + mixed
    assert _roundtrip(content) == content


def test_empty_file():
    """An empty file should save and round-trip correctly."""
    assert _roundtrip("") == ""


def test_file_size_on_disk():
    """Verify the on-disk file size matches the UTF-8 byte length."""
    content = "G" * (BUFFER_SIZE - 3) + "🎯" * 500
    encoded = content.encode("utf-8")
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        save_file(content, path)
        assert os.path.getsize(path) == len(encoded)
    finally:
        os.unlink(path)
