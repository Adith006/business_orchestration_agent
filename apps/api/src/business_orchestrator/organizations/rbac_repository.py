
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.organizations.rbac_models import (
    OrganizationRole,
    Permission,
    RolePermission,
)
from business_orchestrator.security.permission_catalog import PERMISSIONS


class RBACRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_permissions(self) -> dict[str, Permission]:
        result = await self.session.execute(select(Permission))
        existing = {permission.key: permission for permission in result.scalars()}

        for definition in PERMISSIONS:
            if definition.key not in existing:
                permission = Permission(
                    key=definition.key,
                    description=definition.description,
                    resource=definition.resource,
                    action=definition.action,
                )
                self.session.add(permission)
                existing[definition.key] = permission

        await self.session.flush()
        return existing

    async def get_role(
        self,
        organization_id: UUID,
        name: str,
    ) -> OrganizationRole | None:
        result = await self.session.execute(
            select(OrganizationRole).where(
                OrganizationRole.organization_id == organization_id,
                OrganizationRole.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create_role(
        self,
        organization_id: UUID,
        name: str,
        description: str,
        is_system: bool = False,
    ) -> OrganizationRole:
        role = OrganizationRole(
            organization_id=organization_id,
            name=name,
            description=description,
            is_system=is_system,
        )
        self.session.add(role)
        await self.session.flush()
        return role

    async def assign_permissions(
        self,
        role_id: UUID,
        permission_ids: list[UUID],
    ) -> None:
        if not permission_ids:
            return

        result = await self.session.execute(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(permission_ids),
            )
        )
        existing_ids = set(result.scalars().all())

        for permission_id in permission_ids:
            if permission_id not in existing_ids:
                self.session.add(
                    RolePermission(
                        role_id=role_id,
                        permission_id=permission_id,
                    )
                )

        await self.session.flush()
