from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from business_orchestrator.core.config import get_settings
from business_orchestrator.organizations.membership_repository import MembershipRepository
from business_orchestrator.organizations.models import Organization
from business_orchestrator.organizations.repository import OrganizationRepository
from business_orchestrator.security.password import hash_password, verify_password
from business_orchestrator.security.refresh_repository import (
    RefreshSessionRepository,
)
from business_orchestrator.security.repository import UserRepository
from business_orchestrator.security.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.organizations = OrganizationRepository(session)
        self.memberships = MembershipRepository(session)
        self.refresh_sessions = RefreshSessionRepository(session)
    def issue_access_token(self, user, organization) -> str:
         return create_access_token(
              user_id=user.id,
              organization_id=organization.id,
              )
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
        organization_slug: str,
    ) -> tuple:
        if await self.users.get_by_email(email):
            raise ValueError("An account with this email already exists.")

        if await self.organizations.get_by_slug(organization_slug):
            raise ValueError("This organization slug is already taken.")

        try:
            organization = Organization(
                name=organization_name,
                slug=organization_slug,
            )
            self.session.add(organization)
            await self.session.flush()

            user = await self.users.create(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
            )

            membership = await self.memberships.create(
                user_id=user.id,
                organization_id=organization.id,
                role="owner",
            )

            await self.session.commit()
            return user, organization, membership

        except IntegrityError as exc:
            await self.session.rollback()
            raise ValueError(
                "The email or organization slug is already registered."
            ) from exc
        except Exception:
            await self.session.rollback()
            raise

    async def login(
                    self,
                    email: str,
                    password: str,
                    organization_slug: str,
                    ):
                user = await self.users.get_by_email(email)

                if not user or not user.is_active:
                    raise ValueError("Invalid email, password, or organization.")

                if not verify_password(password, user.password_hash):
                    raise ValueError("Invalid email, password, or organization.")

                organization = await self.organizations.get_by_slug(
                    organization_slug
                )

                if not organization or organization.status != "active":
                    raise ValueError("Invalid email, password, or organization.")

                membership = await self.memberships.get_membership(
                    user.id,
                    organization.id,
                )

                if not membership or membership.status != "active":
                    raise ValueError("Invalid email, password, or organization.")

                return user, organization, membership
    async def issue_refresh_token(self, user, organization) -> str:
        settings = get_settings()
        raw_token = generate_refresh_token()

        await self.refresh_sessions.create(
            user_id=user.id,
            organization_id=organization.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            ),
        )

        return raw_token

    async def validate_refresh_token(self, raw_token: str):
        token_hash = hash_refresh_token(raw_token)

        refresh_session = await self.refresh_sessions.get_by_token_hash(
            token_hash
        )

        if not refresh_session:
            raise ValueError("Invalid or expired refresh token.")

        if refresh_session.revoked_at is not None:
            raise ValueError("Invalid or expired refresh token.")

        if refresh_session.expires_at <= datetime.now(UTC):
            raise ValueError("Invalid or expired refresh token.")

        return refresh_session
    
    async def rotate_refresh_token(self, raw_token: str):
        old_session = await self.validate_refresh_token(raw_token)

        old_session.revoked_at = datetime.now(UTC)

        user = await self.users.get_by_id(old_session.user_id)
        organization = await self.organizations.get_by_id(
            old_session.organization_id
        )

        if (
            not user
            or not user.is_active
            or not organization
            or organization.status != "active"
        ):
            raise ValueError("Invalid or expired refresh token.")

        membership = await self.memberships.get_membership(
            user.id,
            organization.id,
        )

        if not membership or membership.status != "active":
            raise ValueError("Invalid or expired refresh token.")

        await self.session.flush()

        new_refresh_token = await self.issue_refresh_token(
            user,
            organization,
        )
        new_access_token = self.issue_access_token(user, organization)

        await self.session.commit()

        return new_access_token, new_refresh_token