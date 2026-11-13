from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from business_orchestrator.database.engine import get_db_session
from business_orchestrator.organizations.membership_repository import MembershipRepository
from business_orchestrator.organizations.repository import OrganizationRepository
from business_orchestrator.security.repository import UserRepository
from business_orchestrator.security.schemas import AuthenticatedUser
from business_orchestrator.security.tokens import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    
def get_authenticated_identity(payload: dict) -> tuple[UUID, UUID]:
    try:
        user_id = UUID(payload["sub"])
        organization_id = UUID(payload["org"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication claims.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return user_id, organization_id

async def get_current_user(
    payload: dict = Depends(get_current_token_payload),
    session=Depends(get_db_session),
) -> AuthenticatedUser:
    user_id, organization_id = get_authenticated_identity(payload)

    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    organization_repository = OrganizationRepository(session)
    organization = await organization_repository.get_by_id(organization_id)

    if organization is None or organization.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization is inactive or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    membership_repository = MembershipRepository(session)
    membership = await membership_repository.get_membership(
        user_id,
        organization_id,
    )

    if membership is None or membership.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization membership is inactive or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthenticatedUser(
        user_id=str(user.id),
        organization_id=str(organization_id),
        email=user.email,
        full_name=user.full_name,
        organization_role=membership.role,
    )