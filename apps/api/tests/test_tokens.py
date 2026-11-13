from uuid import uuid4

import jwt
import pytest

from business_orchestrator.core.config import get_settings
from business_orchestrator.security.tokens import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


def test_access_token_generation_and_decoding() -> None:
    user_id = uuid4()
    organization_id = uuid4()

    token = create_access_token(user_id, organization_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["org"] == str(organization_id)
    assert payload["type"] == "access"
    assert "exp" in payload


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.token.value")


def test_refresh_token_type_is_rejected() -> None:
    from datetime import UTC, datetime, timedelta

    settings = get_settings()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(jwt.InvalidTokenError, match="Invalid token type"):
        decode_access_token(token)

def test_generate_refresh_token():
    token_one = generate_refresh_token()
    token_two = generate_refresh_token()

    assert isinstance(token_one, str)
    assert len(token_one) > 50
    assert token_one != token_two


def test_hash_refresh_token():
    token = generate_refresh_token()

    hashed = hash_refresh_token(token)

    assert len(hashed) == 64
    assert hashed == hash_refresh_token(token)
    assert hashed != token