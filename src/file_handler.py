"""File handler with chunked write support for large files.

Handles saving files of arbitrary size with correct UTF-8 encoding.
The write buffer is sized based on byte length, not character count,
to prevent overflow when content contains multibyte UTF-8 sequences.
"""

import os

CHUNK_SIZE = 65536  # 64KB write buffer


def _encode_content(text):
    """Encode text to UTF-8 bytes.

    Returns the full byte representation of the input text, correctly
    handling multibyte UTF-8 sequences (emoji, CJK characters, etc.).
    """
    if isinstance(text, bytes):
        return text
    return text.encode("utf-8")


def save_file(path, content):
    """Save content to a file, handling large files with chunked writes.

    Uses byte length (not character count) to size the write buffer,
    ensuring multibyte UTF-8 sequences do not cause buffer overflow
    when content exceeds 64KB.

    Args:
        path: Destination file path.
        content: Text string or bytes to write.

    Raises:
        OSError: If the file cannot be written.
    """
    data = _encode_content(content)

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "wb") as f:
        offset = 0
        while offset < len(data):
            end = min(offset + CHUNK_SIZE, len(data))
            f.write(data[offset:end])
            offset = end


def load_file(path):
    """Load and return the contents of a file as a string.

    Args:
        path: Source file path.

    Returns:
        The file contents decoded as UTF-8.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    with open(path, "rb") as f:
        return f.read().decode("utf-8")
