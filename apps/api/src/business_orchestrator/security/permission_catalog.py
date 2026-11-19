
from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDefinition:
    key: str
    description: str
    resource: str
    action: str


PERMISSIONS = (
    PermissionDefinition(
        "organization.members.read",
        "View organization members.",
        "organization.members",
        "read",
    ),
    PermissionDefinition(
        "organization.members.manage",
        "Invite, update, deactivate, and remove members.",
        "organization.members",
        "manage",
    ),
    PermissionDefinition(
        "organization.roles.read",
        "View organization roles.",
        "organization.roles",
        "read",
    ),
    PermissionDefinition(
        "organization.roles.manage",
        "Create, update, and delete custom roles.",
        "organization.roles",
        "manage",
    ),
    PermissionDefinition(
        "organization.permissions.assign",
        "Assign and revoke permissions from roles.",
        "organization.permissions",
        "assign",
    ),
    PermissionDefinition(
        "organization.policies.manage",
        "Create and manage organization governance policies.",
        "organization.policies",
        "manage",
    ),
    PermissionDefinition(
        "agent.create",
        "Create AI agents.",
        "agent",
        "create",
    ),
    PermissionDefinition(
        "agent.read",
        "View AI agents and their configurations.",
        "agent",
        "read",
    ),
    PermissionDefinition(
        "agent.update",
        "Modify AI agent configurations.",
        "agent",
        "update",
    ),
    PermissionDefinition(
        "agent.delete",
        "Delete AI agents.",
        "agent",
        "delete",
    ),
    PermissionDefinition(
        "agent.approve",
        "Approve or reject AI agent configurations.",
        "agent",
        "approve",
    ),
    PermissionDefinition(
        "agent.activate",
        "Activate approved AI agents.",
        "agent",
        "activate",
    ),
    PermissionDefinition(
        "agent.deactivate",
        "Deactivate AI agents.",
        "agent",
        "deactivate",
    ),
    PermissionDefinition(
        "agent.tools.manage",
        "Manage AI agent tools and MCP integrations.",
        "agent.tools",
        "manage",
    ),
    PermissionDefinition(
        "agent.permissions.manage",
        "Configure AI agent runtime permissions.",
        "agent.permissions",
        "manage",
    ),
    PermissionDefinition(
        "agent.approve_high_risk",
        "Approve high-risk AI agent operations.",
        "agent",
        "approve_high_risk",
    ),
    PermissionDefinition(
        "audit.read",
        "View organization audit records.",
        "audit",
        "read",
    ),
)
