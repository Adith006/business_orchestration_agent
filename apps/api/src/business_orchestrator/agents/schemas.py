
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentConfigurationCreate(BaseModel):
    instructions: str = Field(min_length=10)
    llm_provider: str = Field(min_length=2, max_length=50)
    llm_model: str = Field(min_length=2, max_length=150)
    tools: list[dict[str, Any]] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    memory_config: dict[str, Any] = Field(default_factory=dict)


class AgentConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ai_employee_id: UUID
    version: int
    instructions: str
    llm_provider: str
    llm_model: str
    tools: list[dict[str, Any]]
    permissions: dict[str, Any]
    memory_config: dict[str, Any]
    approval_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentConfigurationApproval(BaseModel):
    approval_status: str = Field(pattern="^(approved|rejected)$")
