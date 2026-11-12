import pytest

from business_orchestrator.security.password import (
    hash_password,
    verify_password,
)


def test_password_is_hashed() -> None:
    password = "NexoraSecurePassword123!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2")


def test_password_verification_succeeds() -> None:
    password = "NexoraSecurePassword123!"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password)


def test_password_verification_rejects_wrong_password() -> None:
    hashed_password = hash_password("NexoraSecurePassword123!")

    assert not verify_password("WrongPassword123!", hashed_password)


def test_short_password_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least 12 characters"):
        hash_password("short")