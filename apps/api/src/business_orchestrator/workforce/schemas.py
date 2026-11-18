from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIEmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    role: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    description: str | None = None


class AIEmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    role: str
    department: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime