"""Tests for file_saver module.

Verifies correct handling of large files with multibyte UTF-8 characters,
including edge cases at the 64KB chunk boundary.
"""

import os
import tempfile

from file_saver import CHUNK_SIZE, load_file, save_file


def test_save_large_file_with_multibyte_utf8():
    """Save a ~70KB file containing emoji characters without crashing."""
    emoji = "\U0001f600"  # grinning face, 4 bytes in UTF-8
    count = (70 * 1024) // len(emoji.encode("utf-8"))
    content = emoji * count

    assert len(content.encode("utf-8")) > CHUNK_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)


def test_save_multibyte_char_spanning_chunk_boundary():
    """Multibyte char at exactly the 64KB boundary is handled correctly."""
    ascii_part = "A" * (CHUNK_SIZE - 1)
    emoji = "\U0001f600"  # 4 bytes in UTF-8
    content = ascii_part + emoji

    encoded = content.encode("utf-8")
    assert len(encoded) == CHUNK_SIZE - 1 + 4  # spans the boundary

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)


def test_save_ascii_and_multibyte_mix_over_64kb():
    """Mixed ASCII and CJK content totaling over 64KB roundtrips."""
    block = "Hello " + "世界" + " "  # "Hello 世界 "
    repeat = (CHUNK_SIZE + 1024) // len(block.encode("utf-8")) + 1
    content = block * repeat

    assert len(content.encode("utf-8")) > CHUNK_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)


def test_save_large_ascii_file():
    """ASCII-only file over 64KB saves correctly (regression guard)."""
    content = "A" * (CHUNK_SIZE + 1024)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)


def test_save_small_ascii_file():
    """Small ASCII-only file still works."""
    content = "Hello, world!\n" * 10

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)


def test_save_empty_file():
    """Empty content saves without error."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, "")
        loaded = load_file(path)
        assert loaded == ""
    finally:
        os.unlink(path)


def test_save_128kb_multibyte_file():
    """128KB file with multibyte chars roundtrips correctly."""
    emoji = "\U0001f4a9"  # 4 bytes in UTF-8
    count = (128 * 1024) // len(emoji.encode("utf-8"))
    content = emoji * count

    assert len(content.encode("utf-8")) >= 2 * CHUNK_SIZE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        path = tmp.name

    try:
        save_file(path, content)
        loaded = load_file(path)
        assert loaded == content
    finally:
        os.unlink(path)
