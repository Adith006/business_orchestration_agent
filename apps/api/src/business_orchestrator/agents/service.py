
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.agents.models import AgentConfiguration
from business_orchestrator.agents.repository import AgentConfigurationRepository
from business_orchestrator.security.tenant import TenantContext
from business_orchestrator.workforce.repository import AIEmployeeRepository


class AgentConfigurationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AgentConfigurationRepository(session)
        self.employee_repository = AIEmployeeRepository(session)

    async def create_configuration(
        self,
        ai_employee_id: UUID,
        tenant_context: TenantContext,
        instructions: str,
        llm_provider: str,
        llm_model: str,
        tools: list[dict],
        permissions: dict,
        memory_config: dict,
    ) -> AgentConfiguration:
        try:
            employee = await self.repository.lock_employee(
                ai_employee_id=ai_employee_id,
                organization_id=tenant_context.organization_id,
            )

            if employee is None:
                raise LookupError("AI employee not found.")

            latest_version = await self.repository.get_latest_version(
                ai_employee_id
            )

            configuration = await self.repository.create(
                ai_employee_id=ai_employee_id,
                version=latest_version + 1,
                instructions=instructions,
                llm_provider=llm_provider,
                llm_model=llm_model,
                tools=tools,
                permissions=permissions,
                memory_config=memory_config,
            )

            await self.session.commit()
            await self.session.refresh(configuration)

            return configuration

        except IntegrityError:
            await self.session.rollback()
            raise ValueError(
                "Configuration version conflict. Please retry."
            ) from None

        except Exception:
            await self.session.rollback()
            raise

    async def list_configurations(
        self,
        ai_employee_id: UUID,
        tenant_context: TenantContext,
    ) -> list[AgentConfiguration]:
        employee = await self.employee_repository.get_by_id(
            employee_id=ai_employee_id,
            organization_id=tenant_context.organization_id,
        )

        if employee is None:
            raise LookupError("AI employee not found.")

        return await self.repository.list_versions(
            ai_employee_id=ai_employee_id,
            organization_id=tenant_context.organization_id,
        )

    async def get_configuration(
        self,
        configuration_id: UUID,
        tenant_context: TenantContext,
    ) -> AgentConfiguration | None:
        return await self.repository.get_by_id(
            configuration_id=configuration_id,
            organization_id=tenant_context.organization_id,
        )

    async def review_configuration(
        self,
        configuration_id: UUID,
        approval_status: str,
        tenant_context: TenantContext,
    ) -> AgentConfiguration:
        try:
            configuration = await self.repository.get_by_id(
                configuration_id=configuration_id,
                organization_id=tenant_context.organization_id,
            )

            if configuration is None:
                raise LookupError("Agent configuration not found.")

            employee = await self.repository.lock_employee(
                ai_employee_id=configuration.ai_employee_id,
                organization_id=tenant_context.organization_id,
            )

            if employee is None:
                raise LookupError("AI employee not found.")

            await self.session.refresh(configuration)

            if configuration.is_active:
                raise ValueError(
                    "An active configuration cannot be reviewed again."
                )

            if configuration.approval_status != "pending":
                raise ValueError(
                    "Only pending configurations can be reviewed."
                )

            if approval_status not in {"approved", "rejected"}:
                raise ValueError(
                    "Invalid configuration approval status."
                )

            configuration.approval_status = approval_status

            await self.session.commit()
            await self.session.refresh(configuration)

            return configuration

        except Exception:
            await self.session.rollback()
            raise

    async def activate_configuration(
        self,
        configuration_id: UUID,
        tenant_context: TenantContext,
    ) -> AgentConfiguration:
        try:
            configuration = await self.repository.get_by_id(
                configuration_id=configuration_id,
                organization_id=tenant_context.organization_id,
            )

            if configuration is None:
                raise LookupError("Agent configuration not found.")

            employee = await self.repository.lock_employee(
                ai_employee_id=configuration.ai_employee_id,
                organization_id=tenant_context.organization_id,
            )

            if employee is None:
                raise LookupError("AI employee not found.")

            await self.session.refresh(configuration)

            if configuration.approval_status != "approved":
                raise ValueError(
                    "Only approved configurations can be activated."
                )

            if configuration.is_active:
                return configuration

            current_active = await self.repository.get_active(
                ai_employee_id=configuration.ai_employee_id,
                organization_id=tenant_context.organization_id,
            )

            if current_active is not None:
                current_active.is_active = False

            configuration.is_active = True

            await self.session.commit()
            await self.session.refresh(configuration)

            return configuration

        except IntegrityError:
            await self.session.rollback()
            raise ValueError(
                "Another configuration version is already active. "
                "Please retry."
            ) from None

        except Exception:
            await self.session.rollback()
            raise
