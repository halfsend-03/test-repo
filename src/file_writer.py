"""File writer module with safe UTF-8 handling for large files.

Writes files using a streaming approach that respects UTF-8 multibyte
character boundaries, preventing buffer overruns when files exceed 64KB.
"""

BUFFER_SIZE = 65536  # 64KB


def save_file(content: str, path: str) -> None:
    """Save content to a file, handling UTF-8 multibyte characters safely.

    Encodes the entire content to UTF-8 bytes first, then writes in
    BUFFER_SIZE chunks. This avoids the v2.3.1 bug where byte length
    was confused with character count, causing a buffer overrun when
    multibyte characters straddled the 64KB boundary.

    Args:
        content: The string content to save.
        path: The filesystem path to write to.
    """
    data = content.encode("utf-8")
    with open(path, "wb") as f:
        offset = 0
        while offset < len(data):
            end = offset + BUFFER_SIZE
            f.write(data[offset:end])
            offset = end


def read_file(path: str) -> str:
    """Read a UTF-8 encoded file and return its content as a string.

    Args:
        path: The filesystem path to read from.

    Returns:
        The decoded string content of the file.
    """
    with open(path, "rb") as f:
        return f.read().decode("utf-8")
