from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.database.engine import get_db_session
from business_orchestrator.security.dependencies import get_current_tenant
from business_orchestrator.security.tenant import TenantContext
from business_orchestrator.workforce.schemas import (
    AIEmployeeCreate,
    AIEmployeeResponse,
    AIEmployeeStatusUpdate,
)
from business_orchestrator.workforce.service import AIEmployeeService

router = APIRouter(prefix="/ai-employees", tags=["AI Employees"])


@router.post(
    "",
    response_model=AIEmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ai_employee(
    payload: AIEmployeeCreate,
    session: AsyncSession = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> AIEmployeeResponse:
    service = AIEmployeeService(session)
    employee = await service.create_employee(
        tenant_context=tenant_context,
        name=payload.name,
        role=payload.role,
        department=payload.department,
        description=payload.description,
    )
    return AIEmployeeResponse.model_validate(employee)


@router.get(
    "",
    response_model=list[AIEmployeeResponse],
)
async def list_ai_employees(
    session: AsyncSession = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> list[AIEmployeeResponse]:
    service = AIEmployeeService(session)
    employees = await service.list_employees(tenant_context)
    return [AIEmployeeResponse.model_validate(employee) for employee in employees]


@router.get(
    "/{employee_id}",
    response_model=AIEmployeeResponse,
)
async def get_ai_employee(
    employee_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> AIEmployeeResponse:
    service = AIEmployeeService(session)
    employee = await service.get_employee(employee_id, tenant_context)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI employee not found.",
        )

    return AIEmployeeResponse.model_validate(employee)


@router.patch(
    "/{employee_id}/status",
    response_model=AIEmployeeResponse,
)
async def update_ai_employee_status(
    employee_id: UUID,
    payload: AIEmployeeStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant),
) -> AIEmployeeResponse:
    service = AIEmployeeService(session)

    try:
        employee = await service.update_employee_status(
            employee_id=employee_id,
            new_status=payload.status,
            tenant_context=tenant_context,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AIEmployeeResponse.model_validate(employee)
