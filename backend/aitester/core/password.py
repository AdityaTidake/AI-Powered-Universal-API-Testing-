"""
Password hashing service using bcrypt via passlib.

SOLID: Single Responsibility — only handles password hashing and verification.
Interface Segregation: Thin module, importable anywhere without pulling in DB/JWT.
"""

from passlib.context import CryptContext

# bcrypt with auto-upgrading hash rounds
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt. Returns the hashed string."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Returns True if matching, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    return _pwd_context.verify(plain, hashed)
