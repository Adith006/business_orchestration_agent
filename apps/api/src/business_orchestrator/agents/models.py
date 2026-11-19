
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from business_orchestrator.database.base import Base


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"

    __table_args__ = (
        UniqueConstraint(
            "ai_employee_id",
            "version",
            name="uq_agent_configurations_employee_version",
        ),
        CheckConstraint(
            "version > 0",
            name="ck_agent_configurations_positive_version",
        ),
        CheckConstraint(
            "is_active = false OR approval_status = 'approved'",
            name="ck_agent_configurations_active_requires_approval",
        ),
        Index(
            "uq_agent_configurations_active_version",
            "ai_employee_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ai_employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    llm_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    llm_model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    tools: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    permissions: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    memory_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    approval_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
