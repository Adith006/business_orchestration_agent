from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.core.config import get_settings
from business_orchestrator.database.engine import get_db_session
from business_orchestrator.security.dependencies import get_current_user
from business_orchestrator.security.schemas import (
    AuthenticatedUser,
    LoginRequest,
    OrganizationResponse,
    RefreshResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from business_orchestrator.security.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)

    try:
        user, organization, _ = await service.register(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
            organization_slug=payload.organization_slug,
        )
        return {
            "message": "Registration successful.",
            "user_id": str(user.id),
            "organization_id": str(organization.id),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)

    try:
        user, organization, _ = await service.login(
            email=str(payload.email),
            password=payload.password,
            organization_slug=payload.organization_slug,
        )

        access_token = service.issue_access_token(user, organization)
        refresh_token = await service.issue_refresh_token(user, organization)

        await session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
            ),
            organization=OrganizationResponse(
                id=str(organization.id),
                name=organization.name,
                slug=organization.slug,
            ),
        )

    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_tokens(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RefreshResponse:
    service = AuthService(session)

    try:
        access_token, refresh_token = await service.rotate_refresh_token(
            request.refresh_token
        )
        settings = get_settings()

        return RefreshResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc

@router.get("/me", response_model=AuthenticatedUser)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    return current_user