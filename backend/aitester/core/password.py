"""
Password hashing using bcrypt directly (bypasses passlib's bcrypt 4.x incompatibility).

SOLID: Single Responsibility — only handles password hashing and verification.
Interface Segregation: Thin module, importable anywhere without pulling in DB/JWT.
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt. Returns the hashed string."""
    # bcrypt has a 72-byte limit; we truncate to avoid the passlib compat error.
    password_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Returns True if matching, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    password_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
