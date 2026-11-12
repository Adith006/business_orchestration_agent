import uuid

from business_orchestrator.organizations.models import Organization


def test_organization_model_defaults() -> None:
    organization = Organization(
        name="NEXORA Technologies",
        slug="nexora-technologies",
    )

    assert organization.name == "NEXORA Technologies"
    assert organization.slug == "nexora-technologies"
    assert Organization.status.default.arg == "active"


def test_organization_model_has_uuid_default() -> None:
    uuid_default = Organization.id.default.arg

    first_id = uuid_default(None)
    second_id = uuid_default(None)

    assert isinstance(first_id, uuid.UUID)
    assert isinstance(second_id, uuid.UUID)
    assert first_id != second_id