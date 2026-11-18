from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.workforce.models import AIEmployee


class AIEmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        organization_id: UUID,
        name: str,
        role: str,
        department: str,
        description: str | None = None,
    ) -> AIEmployee:
        employee = AIEmployee(
            organization_id=organization_id,
            name=name,
            role=role,
            department=department,
            description=description,
        )
        self.session.add(employee)
        await self.session.flush()
        await self.session.refresh(employee)
        return employee

    async def get_by_id(
        self,
        employee_id: UUID,
        organization_id: UUID,
    ) -> AIEmployee | None:
        result = await self.session.execute(
            select(AIEmployee).where(
                AIEmployee.id == employee_id,
                AIEmployee.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[AIEmployee]:
        result = await self.session.execute(
            select(AIEmployee)
            .where(AIEmployee.organization_id == organization_id)
            .order_by(AIEmployee.created_at.desc())
        )
        return list(result.scalars().all())
