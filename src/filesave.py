"""File save module with proper UTF-8 buffer handling."""

import os

# Buffer size threshold in bytes
BUFFER_SIZE = 65536  # 64KB


def _calculate_buffer_size(content: str) -> int:
    """Calculate the required buffer size based on byte length of content.

    Uses the byte length of the UTF-8 encoded content rather than the
    character count. For ASCII-only content these are equivalent, but
    for multibyte UTF-8 characters (e.g. emoji at 4 bytes each, CJK at
    3 bytes each) the byte length can be significantly larger.
    """
    return len(content.encode("utf-8"))


def save_file(filepath: str, content: str) -> None:
    """Save content to a file with proper UTF-8 encoding.

    Allocates a write buffer based on the byte length of the encoded
    content, not the character count. This prevents buffer overflows
    when saving files containing multibyte UTF-8 characters that exceed
    the 64KB threshold.

    Args:
        filepath: Path to the file to write.
        content: The text content to save.

    Raises:
        OSError: If the file cannot be written.
    """
    encoded = content.encode("utf-8")
    byte_length = len(encoded)

    # Allocate buffer based on actual byte length
    buffer = bytearray(byte_length)
    buffer[:byte_length] = encoded

    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(buffer)
