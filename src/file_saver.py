"""File saving module with correct UTF-8 buffer handling.

This module provides file saving functionality that correctly handles
multibyte UTF-8 characters by allocating buffers based on byte length
rather than character count.
"""

# Buffer size threshold in bytes
BUFFER_SIZE = 65536  # 64KB


def _calculate_buffer_size(content):
    """Calculate the required buffer size based on byte length.

    Uses the byte length of the encoded content to determine the
    buffer size, ensuring multibyte UTF-8 characters are accounted
    for correctly.

    Args:
        content: String content to calculate buffer size for.

    Returns:
        The required buffer size in bytes.
    """
    byte_length = len(content.encode("utf-8"))
    if byte_length <= BUFFER_SIZE:
        return BUFFER_SIZE
    # Allocate enough buffer to hold the full byte content
    return byte_length


def save_file(path, content):
    """Save content to a file with correct UTF-8 handling.

    Allocates a write buffer based on the byte length of the content,
    not the character count, to correctly handle multibyte UTF-8
    characters (emoji, CJK, etc.) that exceed the 64KB buffer
    threshold.

    Args:
        path: File path to write to.
        content: String content to save.

    Raises:
        OSError: If the file cannot be written.
        TypeError: If content is not a string.
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    buffer_size = _calculate_buffer_size(content)
    encoded = content.encode("utf-8")

    if len(encoded) > buffer_size:
        raise RuntimeError(
            f"Buffer overflow: content byte length {len(encoded)} "
            f"exceeds buffer size {buffer_size}"
        )

    with open(path, "wb") as f:
        f.write(encoded)
