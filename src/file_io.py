"""File I/O module for saving documents.

Handles file saving with proper UTF-8 encoding support, including
multibyte characters (emoji, CJK, etc.).
"""

# Buffer size threshold in bytes (64KB)
BUFFER_SIZE = 65536


def allocate_save_buffer(content: str) -> bytearray:
    """Allocate a buffer for saving file content.

    The buffer is sized based on the byte length of the UTF-8 encoded
    content, not the character count. This ensures multibyte characters
    (emoji, CJK, etc.) are fully accommodated.

    Args:
        content: The text content to be saved.

    Returns:
        A bytearray large enough to hold the UTF-8 encoded content.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)
    return bytearray(byte_length)


def save_file(filepath: str, content: str) -> int:
    """Save content to a file with proper UTF-8 encoding.

    Allocates a buffer based on byte length (not character count) to
    correctly handle multibyte UTF-8 characters at any file size.

    Args:
        filepath: Path to the file to save.
        content: The text content to write.

    Returns:
        The number of bytes written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Allocate buffer based on byte length, not character count
    buf = allocate_save_buffer(content)
    buf[:byte_length] = encoded

    with open(filepath, "wb") as f:
        bytes_written = f.write(buf)

    return bytes_written
