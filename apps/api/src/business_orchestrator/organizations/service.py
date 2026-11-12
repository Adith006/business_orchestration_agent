from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.organizations.models import Organization
from business_orchestrator.organizations.repository import OrganizationRepository


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = OrganizationRepository(session)

    async def create_organization(
        self,
        name: str,
        slug: str,
    ) -> Organization:
        existing = await self.repository.get_by_slug(slug)

        if existing:
            raise ValueError("An organization with this slug already exists.")

        organization = await self.repository.create(name=name, slug=slug)

        try:
            await self.session.commit()
            await self.session.refresh(organization)
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("An organization with this slug already exists.") from None

        return organization