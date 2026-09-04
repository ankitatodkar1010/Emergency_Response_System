import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.user import User

from app.services.assignment_service import update_assignment_status


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_user(
    db,
    role="RESPONDER",
    availability_status="AVAILABLE",
    latitude=12.3765,
    longitude=10.3765
):
    user = User(
        name="Test Responder",
        email=f"test_responder_{uuid.uuid4().hex}@example.com",
        password_hash="test_password",
        role=role,
        availability_status=availability_status,
        latitude=latitude,
        longitude=longitude
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_incident(db):
    incident = Incident(
        incident_type="Accident",
        description="Major road accident for testing",
        severity=5,
        priority="CRITICAL",
        status="reported",
        latitude=12.3765,
        longitude=10.3765,
        created_by=1
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


# ============================================================
# MODEL TESTS
# ============================================================

def test_assignment_model_can_be_created(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="ASSIGNED"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    assert assignment.id is not None
    assert assignment.incident_id == incident.id
    assert assignment.responder_id == responder.id
    assert assignment.status == "ASSIGNED"


# ============================================================
# RESPONDER ROLE TEST
# ============================================================

def test_user_is_responder(db_session):

    responder = create_user(
        db_session,
        role="RESPONDER"
    )

    assert responder.role == "RESPONDER"


# ============================================================
# RESPONDER AVAILABILITY TEST
# ============================================================

def test_responder_is_available(db_session):

    responder = create_user(
        db_session,
        availability_status="AVAILABLE"
    )

    assert responder.availability_status == "AVAILABLE"


# ============================================================
# RESPONDER LOCATION TEST
# ============================================================

def test_responder_has_location(db_session):

    responder = create_user(
        db_session,
        latitude=12.3765,
        longitude=10.3765
    )

    assert responder.latitude is not None
    assert responder.longitude is not None


# ============================================================
# ASSIGNMENT STATUS TEST
# ============================================================

def test_assignment_status_is_assigned(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="ASSIGNED"
    )

    db_session.add(assignment)
    db_session.commit()

    assert assignment.status == "ASSIGNED"

# ============================================================
# ASSIGNMENT LIFECYCLE TESTS
# ============================================================

@pytest.mark.asyncio
async def test_assignment_can_be_accepted(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="ASSIGNED"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    with patch(
        "app.services.assignment_service.publish_event",
        new_callable=AsyncMock
    ):
        result = await update_assignment_status(
            db=db_session,
            assignment_id=assignment.id,
            new_status="ACCEPTED",
            current_user_id=responder.id
        )

    assert result.status == "ACCEPTED"

    db_session.refresh(incident)

    assert incident.status == "ASSIGNED"


# ============================================================
# IN PROGRESS TEST
# ============================================================

@pytest.mark.asyncio
async def test_assignment_can_move_to_in_progress(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="ACCEPTED"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    with patch(
        "app.services.assignment_service.publish_event",
        new_callable=AsyncMock
    ):
        result = await update_assignment_status(
            db=db_session,
            assignment_id=assignment.id,
            new_status="IN_PROGRESS",
            current_user_id=responder.id
        )

    assert result.status == "IN_PROGRESS"

    db_session.refresh(incident)

    assert incident.status == "IN_PROGRESS"


# ============================================================
# COMPLETION TEST
# ============================================================

@pytest.mark.asyncio
async def test_assignment_can_be_completed(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="IN_PROGRESS"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    with patch(
        "app.services.assignment_service.publish_event",
        new_callable=AsyncMock
    ):
        result = await update_assignment_status(
            db=db_session,
            assignment_id=assignment.id,
            new_status="COMPLETED",
            current_user_id=responder.id
        )

    assert result.status == "COMPLETED"

    db_session.refresh(incident)
    db_session.refresh(responder)

    assert incident.status == "RESOLVED"
    assert responder.availability_status == "AVAILABLE"


# ============================================================
# INVALID TRANSITION TEST
# ============================================================

@pytest.mark.asyncio
async def test_invalid_assignment_transition(db_session):

    responder = create_user(db_session)
    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=responder.id,
        status="ASSIGNED"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    with pytest.raises(ValueError):

        await update_assignment_status(
            db=db_session,
            assignment_id=assignment.id,
            new_status="COMPLETED",
            current_user_id=responder.id
        )


# ============================================================
# UNAUTHORIZED RESPONDER TEST
# ============================================================

@pytest.mark.asyncio
async def test_only_assigned_responder_can_update_assignment(
    db_session
):

    assigned_responder = create_user(db_session)

    another_responder = create_user(
        db_session,
        latitude=12.4000,
        longitude=10.4000
    )

    incident = create_incident(db_session)

    assignment = Assignment(
        incident_id=incident.id,
        responder_id=assigned_responder.id,
        status="ASSIGNED"
    )

    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    with pytest.raises(PermissionError):

        await update_assignment_status(
            db=db_session,
            assignment_id=assignment.id,
            new_status="ACCEPTED",
            current_user_id=another_responder.id
        )