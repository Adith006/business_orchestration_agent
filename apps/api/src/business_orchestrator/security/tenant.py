from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: UUID
    organization_id: UUID
    organization_role: str