
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.organizations.rbac_repository import RBACRepository


class OrganizationRBACService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = RBACRepository(session)

    async def provision_default_roles(
        self,
        organization_id: UUID,
    ) -> tuple[UUID, UUID]:
        permissions = await self.repository.ensure_permissions()

        owner_role = await self.repository.get_role(
            organization_id,
            "Owner",
        )

        if owner_role is None:
            owner_role = await self.repository.create_role(
                organization_id=organization_id,
                name="Owner",
                description="Full administrative authority over the organization.",
                is_system=True,
            )

        member_role = await self.repository.get_role(
            organization_id,
            "Member",
        )

        if member_role is None:
            member_role = await self.repository.create_role(
                organization_id=organization_id,
                name="Member",
                description="Standard organization member with read-only agent access.",
                is_system=True,
            )

        owner_permission_ids = [
            permission.id for permission in permissions.values()
        ]

        member_permission_ids = [
            permissions["agent.read"].id,
        ]

        await self.repository.assign_permissions(
            role_id=owner_role.id,
            permission_ids=owner_permission_ids,
        )

        await self.repository.assign_permissions(
            role_id=member_role.id,
            permission_ids=member_permission_ids,
        )

        await self.session.flush()

        return owner_role.id, member_role.id
