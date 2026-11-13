from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.database.engine import get_db_session
from business_orchestrator.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
)
from business_orchestrator.organizations.service import OrganizationService
from business_orchestrator.security.dependencies import get_current_user
from business_orchestrator.security.schemas import AuthenticatedUser

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    payload: OrganizationCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OrganizationResponse:
    service = OrganizationService(session)

    try:
        organization = await service.create_organization(
            name=payload.name,
            slug=payload.slug,
            user_id=UUID(current_user.user_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return OrganizationResponse.model_validate(organization)

@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
async def get_organization(
    organization_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OrganizationResponse:
    # Restrict access to the authenticated user's active organization.
    if str(organization_id) != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    service = OrganizationService(session)
    organization = await service.repository.get_by_id(organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    return OrganizationResponse.model_validate(organization)