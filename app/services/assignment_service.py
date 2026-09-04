from sqlalchemy.orm import Session

from app.services.geolocation_service import calculate_distance
from app.services.audit_service import create_audit_log
from app.services.notification_service import create_notification

from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.user import User

from app.core.redis_pubsub import publish_event


# ============================================================
# ACTIVE ASSIGNMENT STATUSES
# ============================================================

ACTIVE_ASSIGNMENT_STATUSES = [
    "ASSIGNED",
    "ACCEPTED",
    "IN_PROGRESS",
]


# ============================================================
# MANUAL ASSIGNMENT
# ADMIN ONLY — assigns an available responder
# ============================================================

async def assign_responder(
    db: Session,
    incident_id: int,
    responder_id: int,
    current_user_id: int
):
    # --------------------------------------------------------
    # 1. Check incident exists
    # --------------------------------------------------------

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return None

    # --------------------------------------------------------
    # 2. Prevent assigning an incident that already has
    #    an active assignment
    # --------------------------------------------------------

    existing_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.incident_id == incident_id,
            Assignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES)
        )
        .first()
    )

    if existing_assignment is not None:
        raise ValueError(
            "Incident already has an active assignment"
        )

    # --------------------------------------------------------
    # 3. Find responder and lock the row
    # --------------------------------------------------------

    responder = (
        db.query(User)
        .filter(User.id == responder_id)
        .with_for_update()
        .first()
    )

    if responder is None:
        return None

    # --------------------------------------------------------
    # 4. User must be a responder
    # --------------------------------------------------------

    if responder.role != "RESPONDER":
        raise ValueError(
            "Selected user is not a responder"
        )

    # --------------------------------------------------------
    # 5. Responder must be available
    # --------------------------------------------------------

    if responder.availability_status != "AVAILABLE":
        raise ValueError(
            "Responder is not available"
        )

    # --------------------------------------------------------
    # 6. Responder must have location
    # --------------------------------------------------------

    if (
        responder.latitude is None
        or responder.longitude is None
    ):
        raise ValueError(
            "Responder location is not available"
        )

    # --------------------------------------------------------
    # 7. Prevent duplicate assignment of the same responder
    #    to the same incident
    # --------------------------------------------------------

    existing_responder_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.incident_id == incident_id,
            Assignment.responder_id == responder_id,
            Assignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES)
        )
        .first()
    )

    if existing_responder_assignment is not None:
        raise ValueError(
            "Responder is already assigned to this incident"
        )

    try:
        # ----------------------------------------------------
        # 8. Create assignment
        # ----------------------------------------------------

        assignment = Assignment(
            incident_id=incident_id,
            responder_id=responder.id,
            status="ASSIGNED"
        )

        # ----------------------------------------------------
        # 9. Responder becomes busy
        # ----------------------------------------------------

        responder.availability_status = "BUSY"

        db.add(assignment)

        # Generate assignment ID
        db.flush()

        # ----------------------------------------------------
        # 10. Create audit log
        # ----------------------------------------------------

        create_audit_log(
            db=db,
            action="MANUAL_ASSIGNMENT",
            user_id=current_user_id,
            incident_id=incident_id,
            assignment_id=assignment.id,
            details=(
                f"Responder {responder_id} "
                f"manually assigned"
            )
        )

        # ----------------------------------------------------
        # 11. Create notification
        # ----------------------------------------------------

        create_notification(
            db=db,
            user_id=responder.id,
            title="New Emergency Assignment",
            message=(
                f"You have been assigned to incident "
                f"#{incident_id}"
            ),
            notification_type="ASSIGNMENT"
        )

        # ----------------------------------------------------
        # 12. Commit transaction
        # ----------------------------------------------------

        db.commit()

        db.refresh(assignment)

        # ----------------------------------------------------
        # 13. Publish real-time event
        # ----------------------------------------------------

        await publish_event({
            "type": "responder_assigned",
            "target_user_id": assignment.responder_id,
            "incident_id": assignment.incident_id,
            "responder_id": assignment.responder_id,
            "assignment_id": assignment.id,
            "status": assignment.status,
            "assignment_type": "MANUAL"
        })

        return assignment

    except Exception:
        db.rollback()
        raise


# ============================================================
# GET ALL ASSIGNMENTS
# ============================================================

def get_assignments(db: Session):
    return db.query(Assignment).all()


# ============================================================
# GET ONE ASSIGNMENT
# ============================================================

def get_assignment(
    db: Session,
    assignment_id: int
):
    return (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )


# ============================================================
# FIND NEAREST AVAILABLE RESPONDER
# ============================================================

def find_nearest_responder(
    db: Session,
    incident_id: int,
    exclude_responder_id: int | None = None
):
    # --------------------------------------------------------
    # 1. Find incident
    # --------------------------------------------------------

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        return None

    # --------------------------------------------------------
    # 2. Prevent duplicate active assignment
    # --------------------------------------------------------

    existing_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.incident_id == incident_id,
            Assignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES)
        )
        .first()
    )

    if existing_assignment is not None:
        raise ValueError(
            "Incident already has an active assignment"
        )

    # --------------------------------------------------------
    # 3. Incident must have location
    # --------------------------------------------------------

    if (
        incident.latitude is None
        or incident.longitude is None
    ):
        return None

    # --------------------------------------------------------
    # 4. Find available responders
    # --------------------------------------------------------

    query = (
        db.query(User)
        .filter(
            User.role == "RESPONDER",
            User.availability_status == "AVAILABLE",
            User.latitude.isnot(None),
            User.longitude.isnot(None)
        )
    )

    # --------------------------------------------------------
    # 5. Exclude a responder if requested
    # --------------------------------------------------------

    if exclude_responder_id is not None:
        query = query.filter(
            User.id != exclude_responder_id
        )

    # --------------------------------------------------------
    # 6. Lock available responders
    # --------------------------------------------------------

    responders = (
        query
        .with_for_update()
        .all()
    )

    if not responders:
        return None

    # --------------------------------------------------------
    # 7. Find nearest responder
    # --------------------------------------------------------

    nearest_responder = None
    shortest_distance = float("inf")

    for responder in responders:

        distance = calculate_distance(
            incident.latitude,
            incident.longitude,
            responder.latitude,
            responder.longitude
        )

        if distance < shortest_distance:
            shortest_distance = distance
            nearest_responder = responder

    if nearest_responder is None:
        return None

    return nearest_responder, shortest_distance


# ============================================================
# AUTOMATICALLY ASSIGN NEAREST RESPONDER
# ============================================================

def auto_assign_nearest_responder(
    db: Session,
    incident_id: int,
    current_user_id: int | None = None
):
    # --------------------------------------------------------
    # 1. Prevent duplicate active assignment
    # --------------------------------------------------------

    existing_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.incident_id == incident_id,
            Assignment.status.in_(ACTIVE_ASSIGNMENT_STATUSES)
        )
        .first()
    )

    if existing_assignment is not None:
        raise ValueError(
            "Incident already has an active assignment"
        )

    # --------------------------------------------------------
    # 2. Find nearest responder
    # --------------------------------------------------------

    result = find_nearest_responder(
        db=db,
        incident_id=incident_id
    )

    if result is None:
        return None

    responder, distance = result

    try:
        # ----------------------------------------------------
        # 3. Responder becomes busy
        # ----------------------------------------------------

        responder.availability_status = "BUSY"

        # ----------------------------------------------------
        # 4. Create assignment
        # ----------------------------------------------------

        assignment = Assignment(
            incident_id=incident_id,
            responder_id=responder.id,
            status="ASSIGNED"
        )

        db.add(assignment)

        # Generate assignment ID
        db.flush()

        # ----------------------------------------------------
        # 5. Create audit log
        # ----------------------------------------------------

        create_audit_log(
            db=db,
            action="AUTO_ASSIGNMENT",
            user_id=current_user_id,
            incident_id=incident_id,
            assignment_id=assignment.id,
            details=(
                f"Nearest responder {responder.id} "
                f"automatically assigned. "
                f"Distance: {distance:.2f} km"
            )
        )

        # ----------------------------------------------------
        # 6. Create notification for responder
        # ----------------------------------------------------

        create_notification(
            db=db,
            user_id=responder.id,
            title="New Emergency Assignment",
            message=(
                f"You have been assigned to incident "
                f"#{incident_id}"
            ),
            notification_type="ASSIGNMENT"
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Do NOT commit here.
        #
        # The incident service controls the transaction.
        # ----------------------------------------------------

        return assignment

    except Exception:
        raise


# ============================================================
# UPDATE ASSIGNMENT STATUS
# ============================================================

async def update_assignment_status(
    db: Session,
    assignment_id: int,
    new_status: str,
    current_user_id: int
):
    # --------------------------------------------------------
    # 1. Find assignment
    # --------------------------------------------------------

    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )

    if assignment is None:
        return None

    # --------------------------------------------------------
    # 2. Only assigned responder can update assignment
    # --------------------------------------------------------

    if assignment.responder_id != current_user_id:
        raise PermissionError(
            "Only the assigned responder can update this assignment"
        )

    # --------------------------------------------------------
    # 3. Valid state transitions
    # --------------------------------------------------------

    current_status = assignment.status

    allowed_transitions = {
        "ASSIGNED": [
            "ACCEPTED",
            "REJECTED"
        ],
        "ACCEPTED": [
            "IN_PROGRESS"
        ],
        "IN_PROGRESS": [
            "COMPLETED"
        ]
    }

    if new_status not in allowed_transitions.get(
        current_status,
        []
    ):
        raise ValueError(
            f"Invalid transition: "
            f"{current_status} -> {new_status}"
        )

    try:
        # ----------------------------------------------------
        # 4. Update assignment status
        # ----------------------------------------------------

        assignment.status = new_status

        # ----------------------------------------------------
        # 5. Find related incident
        # ----------------------------------------------------

        incident = (
            db.query(Incident)
            .filter(
                Incident.id == assignment.incident_id
            )
            .first()
        )

        # ----------------------------------------------------
        # 6. Synchronize incident status
        # ----------------------------------------------------

        if incident:

            if new_status == "ACCEPTED":
                incident.status = "ASSIGNED"

            elif new_status == "IN_PROGRESS":
                incident.status = "IN_PROGRESS"

            elif new_status == "COMPLETED":
                incident.status = "RESOLVED"

            elif new_status == "REJECTED":
                incident.status = "OPEN"

        # ----------------------------------------------------
        # 7. Create audit log
        # ----------------------------------------------------

        create_audit_log(
            db=db,
            action=f"ASSIGNMENT_{new_status}",
            user_id=current_user_id,
            incident_id=assignment.incident_id,
            assignment_id=assignment.id,
            details=(
                f"Assignment status changed "
                f"from {current_status} "
                f"to {new_status}"
            )
        )

        # ----------------------------------------------------
        # 8. Find responder
        # ----------------------------------------------------

        responder = (
            db.query(User)
            .filter(
                User.id == assignment.responder_id
            )
            .with_for_update()
            .first()
        )

        # ----------------------------------------------------
        # 9. Free responder after rejection/completion
        # ----------------------------------------------------

        if responder and new_status in [
            "REJECTED",
            "COMPLETED"
        ]:
            responder.availability_status = "AVAILABLE"

        # ----------------------------------------------------
        # 10. Automatic reassignment after rejection
        # ----------------------------------------------------

        replacement_assignment = None
        replacement_distance = None

        if new_status == "REJECTED":

            result = find_nearest_responder(
                db=db,
                incident_id=assignment.incident_id,
                exclude_responder_id=assignment.responder_id
            )

            if result is not None:

                new_responder, replacement_distance = result

                # --------------------------------------------
                # New responder becomes busy
                # --------------------------------------------

                new_responder.availability_status = "BUSY"

                # --------------------------------------------
                # Create replacement assignment
                # --------------------------------------------

                replacement_assignment = Assignment(
                    incident_id=assignment.incident_id,
                    responder_id=new_responder.id,
                    status="ASSIGNED"
                )

                db.add(replacement_assignment)

                # Generate ID
                db.flush()

                # --------------------------------------------
                # Audit reassignment
                # --------------------------------------------

                create_audit_log(
                    db=db,
                    action="AUTO_REASSIGNMENT",
                    user_id=current_user_id,
                    incident_id=assignment.incident_id,
                    assignment_id=replacement_assignment.id,
                    details=(
                        f"Responder "
                        f"{assignment.responder_id} "
                        f"rejected the assignment. "
                        f"New responder "
                        f"{new_responder.id} "
                        f"automatically assigned. "
                        f"Distance: "
                        f"{replacement_distance:.2f} km"
                    )
                )

                # --------------------------------------------
                # Create notification for NEW responder
                # --------------------------------------------

                create_notification(
                    db=db,
                    user_id=new_responder.id,
                    title="New Emergency Assignment",
                    message=(
                        f"You have been assigned to incident "
                        f"#{assignment.incident_id}"
                    ),
                    notification_type="ASSIGNMENT"
                )

        # ----------------------------------------------------
        # 11. Commit database transaction
        # ----------------------------------------------------

        db.commit()

        db.refresh(assignment)

        if replacement_assignment is not None:
            db.refresh(replacement_assignment)

        # ----------------------------------------------------
        # 12. Publish reassignment event
        # ----------------------------------------------------

        if replacement_assignment is not None:

            await publish_event({
                "type": "assignment_reassigned",
                "target_user_id": assignment.responder_id,
                "incident_id": assignment.incident_id,
                "old_responder_id": assignment.responder_id,
                "new_responder_id": replacement_assignment.responder_id,
                "new_assignment_id": replacement_assignment.id,
                "distance_km": round(
                    replacement_distance,
                    2
                )
            })

        # ----------------------------------------------------
        # 13. Publish assignment status event
        # ----------------------------------------------------

        await publish_event({
            "type": "assignment_status_updated",
            "assignment_id": assignment.id,
            "incident_id": assignment.incident_id,
            "responder_id": assignment.responder_id,
            "old_status": current_status,
            "new_status": assignment.status
        })

        return assignment

    except Exception:
        db.rollback()
        raise