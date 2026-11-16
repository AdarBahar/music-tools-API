"""File name helpers"""


def truncate_utf8(text: str, max_bytes: int) -> str:
    """Cut text to at most max_bytes of UTF-8, and keep complete characters.

    Linux file systems limit one name to 255 bytes, not 255 characters.
    A CJK or Hebrew character uses 2 to 4 bytes.
    """
    if max_bytes <= 0:
        return ""
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
