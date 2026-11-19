
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from business_orchestrator.database.base import Base


class ApprovalPolicy(Base):
    __tablename__ = "approval_policies"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "operation",
            "risk_level",
            name="uq_approval_policies_org_operation_risk",
        ),
        CheckConstraint(
            "required_approvals >= 1",
            name="ck_approval_policies_positive_approvals",
        ),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')",
            name="ck_approval_policies_valid_risk_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    required_approvals: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    allow_requester_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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


class ApprovalPolicyApprover(Base):
    __tablename__ = "approval_policy_approvers"
    __table_args__ = (
        CheckConstraint(
            """
            (approver_type = 'role' AND role_id IS NOT NULL AND user_id IS NULL)
            OR
            (approver_type = 'user' AND user_id IS NOT NULL AND role_id IS NULL)
            """,
            name="ck_approval_policy_approvers_valid_target",
        ),
        UniqueConstraint(
            "policy_id",
            "role_id",
            name="uq_approval_policy_approvers_policy_role",
        ),
        UniqueConstraint(
            "policy_id",
            "user_id",
            name="uq_approval_policy_approvers_policy_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approver_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization_roles.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
