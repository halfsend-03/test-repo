"""File saving module with chunked write support.

Handles saving files of arbitrary size with proper UTF-8 encoding.
Uses byte-length based buffer sizing to correctly handle multibyte
characters (emoji, CJK, etc.) without buffer overruns.
"""

BUFFER_SIZE = 65536  # 64KB buffer size in bytes


def save_file(content: str, path: str) -> int:
    """Save text content to a file using chunked writes.

    Splits content into byte-sized chunks that respect UTF-8 character
    boundaries, ensuring multibyte characters are never split across
    chunk boundaries.

    Args:
        content: The text content to save.
        path: The file path to write to.

    Returns:
        The number of bytes written.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    total_bytes = len(encoded)
    bytes_written = 0

    with open(path, "wb") as f:
        while bytes_written < total_bytes:
            end = min(bytes_written + BUFFER_SIZE, total_bytes)
            # Avoid splitting a multibyte UTF-8 character at the chunk
            # boundary. A continuation byte has the form 10xxxxxx
            # (0x80..0xBF). Walk back until we land on a lead byte.
            while end < total_bytes and (encoded[end] & 0xC0) == 0x80:
                end -= 1
            chunk = encoded[bytes_written:end]
            f.write(chunk)
            bytes_written = end

    return bytes_written
