"""
Unit tests for Phase 2 — JWT Auth + Password Hashing.

Tests run without a DB or Redis connection.
Gate: all must pass before Phase 3.

Run: pytest tests/unit/test_auth.py -v
"""

import uuid
import time
import pytest
from unittest.mock import AsyncMock, patch


# ─── Password tests ───────────────────────────────────────────────────────────

class TestPassword:
    def test_hash_returns_different_from_plaintext(self):
        from aitester.core.password import hash_password
        plain = "MySecurePass123"
        assert hash_password(plain) != plain

    def test_verify_correct_password(self):
        from aitester.core.password import hash_password, verify_password
        plain = "MySecurePass123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        from aitester.core.password import hash_password, verify_password
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salts — two hashes must not be equal."""
        from aitester.core.password import hash_password
        pw = "SamePassword!"
        assert hash_password(pw) != hash_password(pw)


# ─── JWT tests ────────────────────────────────────────────────────────────────

class TestJWT:
    def test_create_and_decode_access_token(self):
        from aitester.core.jwt import create_access_token, decode_token, TokenType
        uid = uuid.uuid4()
        token = create_access_token(uid)
        payload = decode_token(token, TokenType.ACCESS)
        assert payload["sub"] == str(uid)
        assert payload["type"] == TokenType.ACCESS

    def test_create_and_decode_refresh_token(self):
        from aitester.core.jwt import create_refresh_token, decode_token, TokenType
        uid = uuid.uuid4()
        token = create_refresh_token(uid)
        payload = decode_token(token, TokenType.REFRESH)
        assert payload["sub"] == str(uid)
        assert payload["type"] == TokenType.REFRESH

    def test_wrong_type_raises_token_error(self):
        from aitester.core.jwt import create_access_token, decode_token, TokenType, TokenError
        uid = uuid.uuid4()
        token = create_access_token(uid)
        with pytest.raises(TokenError, match="Expected"):
            decode_token(token, TokenType.REFRESH)

    def test_tampered_token_raises_token_error(self):
        from aitester.core.jwt import create_access_token, decode_token, TokenType, TokenError
        token = create_access_token(uuid.uuid4()) + "tampered"
        with pytest.raises(TokenError):
            decode_token(token, TokenType.ACCESS)

    def test_get_user_id_from_token_returns_correct_uuid(self):
        from aitester.core.jwt import create_access_token, get_user_id_from_token
        uid = uuid.uuid4()
        token = create_access_token(uid)
        assert get_user_id_from_token(token) == str(uid)

    def test_token_contains_jti(self):
        from aitester.core.jwt import create_access_token, decode_token, TokenType
        token = create_access_token(uuid.uuid4())
        payload = decode_token(token, TokenType.ACCESS)
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID string length

    def test_two_tokens_have_different_jtis(self):
        from aitester.core.jwt import create_access_token, decode_token, TokenType
        uid = uuid.uuid4()
        t1 = decode_token(create_access_token(uid), TokenType.ACCESS)
        t2 = decode_token(create_access_token(uid), TokenType.ACCESS)
        assert t1["jti"] != t2["jti"]


# ─── Auth schemas tests ───────────────────────────────────────────────────────

class TestAuthSchemas:
    def test_register_request_valid(self):
        from aitester.schemas.auth import RegisterRequest
        r = RegisterRequest(email="user@example.com", password="securepass", full_name="Jane Doe")
        assert r.email == "user@example.com"

    def test_register_rejects_invalid_email(self):
        from aitester.schemas.auth import RegisterRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(email="not-an-email", password="securepass", full_name="Jane")

    def test_register_rejects_short_password(self):
        from aitester.schemas.auth import RegisterRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(email="user@example.com", password="short", full_name="Jane")

    def test_register_rejects_digits_only_password(self):
        from aitester.schemas.auth import RegisterRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            RegisterRequest(email="user@example.com", password="12345678", full_name="Jane")

    def test_token_response_fields(self):
        from aitester.schemas.auth import TokenResponse
        tr = TokenResponse(access_token="abc", refresh_token="xyz")
        assert tr.token_type == "bearer"
        assert tr.access_token == "abc"


# ─── AuthService unit tests (Beanie mocked) ──────────────────────────────────

class TestAuthService:
    """Test AuthService.register/login against a mocked Beanie layer."""

    @pytest.mark.asyncio
    @patch("aitester.services.auth_service.User.find_one", new_callable=AsyncMock)
    @patch("aitester.services.auth_service.User.insert", new_callable=AsyncMock)
    async def test_register_returns_tokens(self, mock_insert, mock_find_one):
        from aitester.schemas.auth import RegisterRequest
        from aitester.services.auth_service import AuthService
        from beanie import PydanticObjectId
        from unittest.mock import MagicMock, patch

        mock_find_one.return_value = None  # no duplicate

        # Patch the User class itself in auth_service so no Beanie __init__ runs
        fake_user = MagicMock()
        fake_user.id = PydanticObjectId()
        fake_user.insert = AsyncMock()

        with patch("aitester.services.auth_service.User", return_value=fake_user) as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)
            result = await AuthService.register(RegisterRequest(
                email="new@example.com",
                password="strongpass1",
                full_name="New User",
            ))
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    @patch("aitester.services.auth_service.User.find_one", new_callable=AsyncMock)
    async def test_register_duplicate_email_raises(self, mock_find_one):
        from aitester.db.models import User
        from aitester.schemas.auth import RegisterRequest
        from aitester.services.auth_service import AuthService, AuthError
        from beanie import PydanticObjectId
        from unittest.mock import MagicMock

        existing = MagicMock(spec=User)
        existing.email = "existing@example.com"
        mock_find_one.return_value = existing

        with pytest.raises(AuthError, match="already exists"):
            await AuthService.register(RegisterRequest(
                email="existing@example.com",
                password="strongpass1",
                full_name="Test",
            ))

    @pytest.mark.asyncio
    @patch("aitester.services.auth_service.User.find_one", new_callable=AsyncMock)
    async def test_login_wrong_password_raises(self, mock_find_one):
        from aitester.db.models import User
        from aitester.core.password import hash_password
        from aitester.schemas.auth import LoginRequest
        from aitester.services.auth_service import AuthService, AuthError
        from beanie import PydanticObjectId
        from unittest.mock import MagicMock

        user = MagicMock(spec=User)
        user.email = "u@example.com"
        user.hashed_password = hash_password("correct_pass")
        user.is_active = True
        mock_find_one.return_value = user

        with pytest.raises(AuthError, match="Invalid email or password"):
            await AuthService.login(LoginRequest(email="u@example.com", password="wrong_pass"))

    @pytest.mark.asyncio
    @patch("aitester.services.auth_service.User.find_one", new_callable=AsyncMock)
    async def test_login_success_returns_tokens(self, mock_find_one):
        from aitester.db.models import User
        from aitester.core.password import hash_password
        from aitester.schemas.auth import LoginRequest
        from aitester.services.auth_service import AuthService
        from beanie import PydanticObjectId
        from unittest.mock import MagicMock

        user = MagicMock(spec=User)
        user.id = PydanticObjectId()
        user.email = "u@example.com"
        user.hashed_password = hash_password("correct_pass")
        user.is_active = True
        mock_find_one.return_value = user

        result = await AuthService.login(LoginRequest(email="u@example.com", password="correct_pass"))
        assert result.access_token
        assert result.refresh_token
