import bcrypt


def hash_pwd(password: str) -> str:
    """Hashes the plain-text password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_pwd(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )
