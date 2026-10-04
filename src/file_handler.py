"""File handler module for saving documents with proper UTF-8 support.

This module provides file save functionality that correctly handles
multibyte UTF-8 characters by using byte-length for buffer allocation
instead of character count.

Fix for issue #2415: Prior to this fix, the buffer was allocated based
on character count (len(text)) rather than byte length
(len(text.encode('utf-8'))). For ASCII-only content these are equal,
but multibyte UTF-8 characters (emoji, CJK, etc.) require 2-4 bytes
per character, causing a buffer overflow when content exceeded 64KB.
"""

CHUNK_SIZE = 65536  # 64KB


def save_file(path: str, content: str) -> int:
    """Save content to a file, returning the number of bytes written.

    Uses byte-length (not character count) for buffer management to
    correctly handle multibyte UTF-8 characters at any file size.

    Args:
        path: Destination file path.
        content: Text content to save.

    Returns:
        Total number of bytes written.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    total_bytes = len(encoded)
    bytes_written = 0

    with open(path, "wb") as f:
        while bytes_written < total_bytes:
            end = min(bytes_written + CHUNK_SIZE, total_bytes)
            chunk = encoded[bytes_written:end]
            f.write(chunk)
            bytes_written += len(chunk)

    return bytes_written


def read_file(path: str) -> str:
    """Read a UTF-8 encoded file and return its content as a string.

    Args:
        path: Source file path.

    Returns:
        The file content as a string.

    Raises:
        OSError: If the file cannot be read.
        UnicodeDecodeError: If the file is not valid UTF-8.
    """
    with open(path, "rb") as f:
        return f.read().decode("utf-8")
