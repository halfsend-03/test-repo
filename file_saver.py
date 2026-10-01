"""File saving module with proper UTF-8 multibyte character handling.

Saves file content in chunks, using byte length (not character count)
for buffer allocation to avoid buffer overruns with multibyte UTF-8
characters.
"""

CHUNK_SIZE = 65536  # 64KB


def save_file(filepath: str, content: str) -> None:
    """Save content to a file, handling large files with multibyte UTF-8.

    Writes content in 64KB chunks based on byte length to avoid buffer
    overruns when content contains multibyte UTF-8 characters (e.g.,
    emoji, CJK).

    Args:
        filepath: Path to the output file.
        content: The string content to save.
    """
    encoded = content.encode("utf-8")
    with open(filepath, "wb") as f:
        offset = 0
        while offset < len(encoded):
            chunk = encoded[offset : offset + CHUNK_SIZE]
            f.write(chunk)
            offset += CHUNK_SIZE


def load_file(filepath: str) -> str:
    """Load a UTF-8 file and return its content as a string.

    Args:
        filepath: Path to the file to read.

    Returns:
        The file content as a string.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
