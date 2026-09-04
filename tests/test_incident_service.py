from pydantic import ValidationError

from app.schemas.incident import IncidentCreate
from app.services.incident_service import calculate_priority


# ============================================================
# PRIORITY TESTS
# ============================================================

def test_calculate_priority_critical():
    assert calculate_priority(5) == "CRITICAL"


def test_calculate_priority_high():
    assert calculate_priority(4) == "HIGH"


def test_calculate_priority_medium():
    assert calculate_priority(3) == "MEDIUM"


def test_calculate_priority_low():
    assert calculate_priority(2) == "LOW"


def test_calculate_priority_low_for_severity_one():
    assert calculate_priority(1) == "LOW"


# ============================================================
# INCIDENT VALIDATION TESTS
# ============================================================

def test_incident_create_valid_data():

    incident = IncidentCreate(
        incident_type="Accident",
        description="Major road accident near city centre",
        severity=5,
        latitude=12.3765,
        longitude=10.3765
    )

    assert incident.severity == 5
    assert incident.incident_type == "Accident"


def test_incident_create_rejects_invalid_severity():

    try:
        IncidentCreate(
            incident_type="Accident",
            description="Major road accident near city centre",
            severity=6,
            latitude=12.3765,
            longitude=10.3765
        )

        assert False, "Expected ValidationError"

    except ValidationError:
        assert True


def test_incident_create_rejects_short_description():

    try:
        IncidentCreate(
            incident_type="Accident",
            description="Short",
            severity=5,
            latitude=12.3765,
            longitude=10.3765
        )

        assert False, "Expected ValidationError"

    except ValidationError:
        assert True
