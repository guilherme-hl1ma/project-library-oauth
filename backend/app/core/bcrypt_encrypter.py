import bcrypt


def hash_text(plain_text: str) -> str:
    """Hashes the plain text using bcrypt.

    Args:
        plain_text (str): The text to be hashed.

    Returns:
        str: The hashed text.
    """
    hashed = bcrypt.hashpw(plain_text.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_text(plain_text: str, hashed_text: str) -> bool:
    """Verifies plain text against a bcrypt hash.
    Args:
        plain_text (str): The text to be verified.
        hashed_text (str): The hashed text to compare against.
    Returns:
        bool: True if the plain text matches the hash, False otherwise.
    """
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed_text.encode("utf-8"))
