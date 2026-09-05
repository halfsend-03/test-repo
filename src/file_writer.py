"""Buffered file writer with UTF-8 multibyte boundary handling.

Fixes a segmentation fault that occurs when saving files larger than 64KB
containing UTF-8 multibyte characters (e.g., emoji or CJK characters).
The bug occurs when a multibyte UTF-8 sequence straddles the 64KB buffer
boundary, causing the write logic to split the character mid-sequence.

This module provides a UTF-8-aware buffered writer that ensures multibyte
sequences are never split across buffer boundaries.
"""

BUFFER_SIZE = 65536  # 64KB


def _utf8_safe_split(data: bytes, boundary: int) -> int:
    """Find the largest split point <= boundary that does not break a
    UTF-8 multibyte sequence.

    UTF-8 encoding rules:
    - 0xxxxxxx: single-byte character (ASCII)
    - 110xxxxx: start of 2-byte sequence
    - 1110xxxx: start of 3-byte sequence
    - 11110xxx: start of 4-byte sequence
    - 10xxxxxx: continuation byte

    If the byte at `boundary` is a continuation byte, we walk backwards
    to find the start of the multibyte sequence so we don't split it.

    Args:
        data: The raw bytes to split.
        boundary: The desired split position.

    Returns:
        A safe split position that does not break a multibyte sequence.
    """
    if boundary >= len(data):
        return len(data)

    pos = boundary
    # Walk backwards past any continuation bytes (10xxxxxx)
    while pos > 0 and (data[pos] & 0xC0) == 0x80:
        pos -= 1

    # pos now points to either the start of a multibyte sequence or an
    # ASCII byte. If it is the start of a multibyte sequence that would
    # extend past the boundary, we split before it.
    if pos < boundary:
        # Determine the expected length of the sequence starting at pos
        lead_byte = data[pos]
        if (lead_byte & 0x80) == 0x00:
            seq_len = 1
        elif (lead_byte & 0xE0) == 0xC0:
            seq_len = 2
        elif (lead_byte & 0xF0) == 0xE0:
            seq_len = 3
        elif (lead_byte & 0xF8) == 0xF0:
            seq_len = 4
        else:
            # Invalid lead byte; split here to avoid further corruption
            return pos

        # If the full sequence fits within the boundary, include it
        if pos + seq_len <= boundary:
            return boundary
        # Otherwise, split before the sequence
        return pos

    return boundary


def save_file(content: str, filepath: str) -> None:
    """Save text content to a file using buffered writes that respect
    UTF-8 multibyte character boundaries.

    This replaces the previous implementation that used a fixed 64KB
    buffer without checking for multibyte boundaries, which caused a
    segmentation fault when a UTF-8 sequence straddled the boundary.

    Args:
        content: The text content to save.
        filepath: The path to write the file to.
    """
    data = content.encode("utf-8")
    with open(filepath, "wb") as f:
        offset = 0
        while offset < len(data):
            end = min(offset + BUFFER_SIZE, len(data))
            if end < len(data):
                end = _utf8_safe_split(data, end)
            chunk = data[offset:end]
            f.write(chunk)
            offset = end


def read_file(filepath: str) -> str:
    """Read a file and return its content as a string.

    Args:
        filepath: The path to read the file from.

    Returns:
        The file content as a string.
    """
    with open(filepath, "rb") as f:
        return f.read().decode("utf-8")
