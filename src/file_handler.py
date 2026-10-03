"""File handler module for saving documents to disk.

Handles file saving with proper buffer allocation based on byte length
rather than character count, ensuring correct behavior with UTF-8
multibyte characters (emoji, CJK, etc.) at any file size.
"""

import os
import tempfile

# Default write buffer size (64KB).
DEFAULT_BUFFER_SIZE = 65536


def _calculate_buffer_size(data: bytes) -> int:
    """Calculate the write buffer size for the given data.

    The buffer must be sized based on the byte length of the encoded
    content, not the character count. UTF-8 multibyte characters (emoji,
    CJK, etc.) use 2-4 bytes per character, so character count can be
    significantly less than byte length.

    Args:
        data: The encoded byte content to be written.

    Returns:
        A buffer size large enough to hold the entire content, at least
        DEFAULT_BUFFER_SIZE.
    """
    return max(DEFAULT_BUFFER_SIZE, len(data))


def save_file(filepath: str, content: str, encoding: str = "utf-8") -> int:
    """Save content to a file with proper buffer allocation.

    Encodes the content to bytes first, then allocates a write buffer
    based on the byte length. This ensures correct handling of UTF-8
    multibyte characters at any file size.

    Uses atomic write (write to temp file, then rename) to prevent data
    loss on failure.

    Args:
        filepath: Destination file path.
        content: The text content to save.
        encoding: Character encoding to use (default: utf-8).

    Returns:
        The number of bytes written.

    Raises:
        OSError: If the file cannot be written.
        UnicodeEncodeError: If content cannot be encoded with the
            specified encoding.
    """
    # Encode content to bytes first — this is the actual size we need
    # to write, not len(content) which counts characters.
    data = content.encode(encoding)
    byte_length = len(data)

    # Allocate buffer based on byte length, not character count.
    buffer_size = _calculate_buffer_size(data)

    dir_name = os.path.dirname(filepath) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        with os.fdopen(fd, "wb", buffering=buffer_size) as f:
            f.write(data)
        os.replace(tmp_path, filepath)
    except BaseException:
        # Clean up temp file on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    return byte_length
