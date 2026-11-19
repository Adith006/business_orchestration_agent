
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.agents.models import AgentConfiguration
from business_orchestrator.workforce.models import AIEmployee


class AgentConfigurationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        ai_employee_id: UUID,
        version: int,
        instructions: str,
        llm_provider: str,
        llm_model: str,
        tools: list[dict],
        permissions: dict,
        memory_config: dict,
    ) -> AgentConfiguration:
        configuration = AgentConfiguration(
            ai_employee_id=ai_employee_id,
            version=version,
            instructions=instructions,
            llm_provider=llm_provider,
            llm_model=llm_model,
            tools=tools,
            permissions=permissions,
            memory_config=memory_config,
        )

        self.session.add(configuration)
        await self.session.flush()
        await self.session.refresh(configuration)

        return configuration

    async def get_by_id(
        self,
        configuration_id: UUID,
        organization_id: UUID,
    ) -> AgentConfiguration | None:
        result = await self.session.execute(
            select(AgentConfiguration)
            .join(
                AIEmployee,
                AgentConfiguration.ai_employee_id == AIEmployee.id,
            )
            .where(
                AgentConfiguration.id == configuration_id,
                AIEmployee.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        ai_employee_id: UUID,
        organization_id: UUID,
    ) -> list[AgentConfiguration]:
        result = await self.session.execute(
            select(AgentConfiguration)
            .join(
                AIEmployee,
                AgentConfiguration.ai_employee_id == AIEmployee.id,
            )
            .where(
                AgentConfiguration.ai_employee_id == ai_employee_id,
                AIEmployee.organization_id == organization_id,
            )
            .order_by(AgentConfiguration.version.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        ai_employee_id: UUID,
    ) -> int:
        result = await self.session.execute(
            select(func.max(AgentConfiguration.version)).where(
                AgentConfiguration.ai_employee_id == ai_employee_id,
            )
        )
        return result.scalar_one() or 0

    async def get_active(
        self,
        ai_employee_id: UUID,
        organization_id: UUID,
    ) -> AgentConfiguration | None:
        result = await self.session.execute(
            select(AgentConfiguration)
            .join(
                AIEmployee,
                AgentConfiguration.ai_employee_id == AIEmployee.id,
            )
            .where(
                AgentConfiguration.ai_employee_id == ai_employee_id,
                AIEmployee.organization_id == organization_id,
                AgentConfiguration.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def lock_employee(
    self,
    ai_employee_id: UUID,
    organization_id: UUID,
) -> AIEmployee | None:
        result = await self.session.execute(
            select(AIEmployee)
            .where(
                AIEmployee.id == ai_employee_id,
                AIEmployee.organization_id == organization_id,
                )
                .with_for_update()
                )
        return result.scalar_one_or_none()
