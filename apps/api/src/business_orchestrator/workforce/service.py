from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.security.tenant import TenantContext
from business_orchestrator.workforce.constants import (
    ALLOWED_STATUS_TRANSITIONS,
    AIEmployeeStatus,
)
from business_orchestrator.workforce.models import AIEmployee
from business_orchestrator.workforce.repository import AIEmployeeRepository


class AIEmployeeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AIEmployeeRepository(session)

    async def create_employee(
        self,
        tenant_context: TenantContext,
        name: str,
        role: str,
        department: str,
        description: str | None = None,
    ) -> AIEmployee:
        try:
            employee = await self.repository.create(
                organization_id=tenant_context.organization_id,
                name=name,
                role=role,
                department=department,
                description=description,
            )
            await self.session.commit()
            await self.session.refresh(employee)
            return employee

        except IntegrityError:
            await self.session.rollback()
            raise ValueError(
                "An AI employee with this name already exists in the organization."
            ) from None

    async def get_employee(
        self,
        employee_id: UUID,
        tenant_context: TenantContext,
    ) -> AIEmployee | None:
        return await self.repository.get_by_id(
            employee_id=employee_id,
            organization_id=tenant_context.organization_id,
        )

    async def list_employees(
        self,
        tenant_context: TenantContext,
    ) -> list[AIEmployee]:
        return await self.repository.list_by_organization(
            organization_id=tenant_context.organization_id,
        )

    async def update_employee_status(
        self,
        employee_id: UUID,
        new_status: AIEmployeeStatus,
        tenant_context: TenantContext,
    ) -> AIEmployee:
        employee = await self.repository.get_by_id(
            employee_id=employee_id,
            organization_id=tenant_context.organization_id,
        )

        if employee is None:
            raise LookupError("AI employee not found.")

        current_status = AIEmployeeStatus(employee.status)

        if new_status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
            raise ValueError(
                f"Cannot transition AI employee from "
                f"'{current_status.value}' to '{new_status.value}'."
            )
        try:
            employee.status = new_status.value
            await self.session.commit()
            await self.session.refresh(employee)
        except Exception:
             await self.session.rollback()
             raise

        return employee
