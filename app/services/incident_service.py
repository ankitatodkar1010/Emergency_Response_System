from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.assignment_service import auto_assign_nearest_responder
from app.services.audit_service import create_audit_log
from app.core.redis_pubsub import publish_event


# ============================================================
# RISK ASSESSMENT ENGINE
# ============================================================

def assess_incident_risk(
    incident_type: str,
    severity: int,
    people_affected: int,
    people_trapped: int,
    escalating: bool
) -> tuple[int, str, str]:

    score = 0
    reasons = []

    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    severity_points = {
        1: 1,
        2: 2,
        3: 4,
        4: 6,
        5: 8
    }

    severity_score = severity_points[severity]

    score += severity_score

    reasons.append(
        f"severity contributed {severity_score} points"
    )

    # --------------------------------------------------------
    # INCIDENT TYPE
    # --------------------------------------------------------

    type_points = {
        "Fire": 2,
        "Disaster": 3,
        "Medical Emergency": 2,
        "Accident": 1
    }

    type_score = type_points.get(
        incident_type,
        1
    )

    score += type_score

    reasons.append(
        f"{incident_type} contributed {type_score} points"
    )

    # --------------------------------------------------------
    # PEOPLE AFFECTED
    # --------------------------------------------------------

    if people_affected >= 21:

        score += 4

        reasons.append(
            "large number of affected people contributed 4 points"
        )

    elif people_affected >= 6:

        score += 2

        reasons.append(
            "multiple affected people contributed 2 points"
        )

    elif people_affected >= 1:

        score += 1

        reasons.append(
            "affected people contributed 1 point"
        )

    # --------------------------------------------------------
    # PEOPLE TRAPPED
    # --------------------------------------------------------

    if people_trapped > 0:

        score += 4

        reasons.append(
            f"{people_trapped} trapped person(s) contributed 4 points"
        )

    # --------------------------------------------------------
    # ESCALATING SITUATION
    # --------------------------------------------------------

    if escalating:

        score += 3

        reasons.append(
            "escalating situation contributed 3 points"
        )

    # --------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------

    if score >= 14:

        priority = "CRITICAL"

    elif score >= 10:

        priority = "HIGH"

    elif score >= 6:

        priority = "MEDIUM"

    else:

        priority = "LOW"

    reason = (
        f"Risk score {score}. "
        + "; ".join(reasons)
        + f". Priority classified as {priority}."
    )

    return score, priority, reason


# ============================================================
# CREATE INCIDENT
# ============================================================

async def create_incident(
    db: Session,
    incident: IncidentCreate,
    user_id: int
):

    risk_score, priority, priority_reason = assess_incident_risk(
        incident_type=incident.incident_type,
        severity=incident.severity,
        people_affected=incident.people_affected,
        people_trapped=incident.people_trapped,
        escalating=incident.escalating
    )

    new_incident = Incident(
        incident_type=incident.incident_type,
        description=incident.description,
        severity=incident.severity,
        people_affected=incident.people_affected,
        people_trapped=incident.people_trapped,
        escalating=incident.escalating,
        risk_score=risk_score,
        priority=priority,
        priority_reason=priority_reason,
        status="reported",
        latitude=incident.latitude,
        longitude=incident.longitude,
        created_by=user_id
    )

    try:

        # ----------------------------------------------------
        # 1. CREATE INCIDENT
        # ----------------------------------------------------

        db.add(new_incident)

        db.flush()

        # ----------------------------------------------------
        # 2. AUTOMATIC RESPONDER ASSIGNMENT
        # ----------------------------------------------------

        assignment = auto_assign_nearest_responder(
            db,
            new_incident.id
        )

        # ----------------------------------------------------
        # 3. INCIDENT AUDIT LOG
        # ----------------------------------------------------

        create_audit_log(
            db=db,
            action="INCIDENT_CREATED",
            user_id=user_id,
            incident_id=new_incident.id,
            details=(
                f"Incident created. "
                f"Risk score={risk_score}, "
                f"priority={priority}. "
                f"{priority_reason}"
            )
        )

        # ----------------------------------------------------
        # 4. ASSIGNMENT AUDIT LOG
        # ----------------------------------------------------

        if assignment is not None:

            create_audit_log(
                db=db,
                action="RESPONDER_AUTO_ASSIGNED",
                user_id=user_id,
                incident_id=new_incident.id,
                assignment_id=assignment.id,
                details=(
                    f"Responder {assignment.responder_id} "
                    f"automatically assigned."
                )
            )

        # ----------------------------------------------------
        # 5. ATOMIC DATABASE COMMIT
        # ----------------------------------------------------

        db.commit()

        db.refresh(new_incident)

        # ----------------------------------------------------
        # 6. REAL-TIME INCIDENT EVENT
        # ----------------------------------------------------

        await publish_event({
            "type": "incident_created",
            "incident_id": new_incident.id,
            "incident_type": new_incident.incident_type,
            "severity": new_incident.severity,
            "people_affected": new_incident.people_affected,
            "people_trapped": new_incident.people_trapped,
            "escalating": new_incident.escalating,
            "risk_score": new_incident.risk_score,
            "priority": new_incident.priority,
            "priority_reason": new_incident.priority_reason,
            "status": new_incident.status
        })

        # ----------------------------------------------------
        # 7. REAL-TIME ASSIGNMENT EVENT
        # ----------------------------------------------------

        if assignment is not None:

            await publish_event({
                "type": "responder_assigned",
                "incident_id": new_incident.id,
                "responder_id": assignment.responder_id,
                "assignment_id": assignment.id,
                "status": assignment.status
            })

        return new_incident

    except Exception:

        db.rollback()

        raise


# ============================================================
# GET ALL INCIDENTS
# ============================================================

def get_incidents(
    db: Session,
    status: str | None = None,
    severity: int | None = None,
    priority: str | None = None,
    page: int = 1,
    limit: int = 10
):

    query = db.query(Incident)

    if status is not None:

        query = query.filter(
            Incident.status == status
        )

    if severity is not None:

        query = query.filter(
            Incident.severity == severity
        )

    if priority is not None:

        query = query.filter(
            Incident.priority == priority
        )

    offset = (page - 1) * limit

    return (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )


# ============================================================
# GET ONE INCIDENT
# ============================================================

def get_incident(
    db: Session,
    incident_id: int
):

    return (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )


# ============================================================
# UPDATE INCIDENT
# ============================================================

async def update_incident(
    db: Session,
    incident_id: int,
    data: IncidentUpdate,
    current_user_id: int
):

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        return None

    old_severity = incident.severity
    old_priority = incident.priority
    old_status = incident.status
    old_risk_score = incident.risk_score

    try:

        # ----------------------------------------------------
        # UPDATE VALUES
        # ----------------------------------------------------

        if data.severity is not None:

            incident.severity = data.severity

        if data.people_affected is not None:

            incident.people_affected = data.people_affected

        if data.people_trapped is not None:

            incident.people_trapped = data.people_trapped

        if data.escalating is not None:

            incident.escalating = data.escalating

        if data.status is not None:

            incident.status = data.status

        # ----------------------------------------------------
        # RECALCULATE RISK
        # ----------------------------------------------------

        (
            incident.risk_score,
            incident.priority,
            incident.priority_reason
        ) = assess_incident_risk(
            incident_type=incident.incident_type,
            severity=incident.severity,
            people_affected=incident.people_affected,
            people_trapped=incident.people_trapped,
            escalating=incident.escalating
        )

        # ----------------------------------------------------
        # AUDIT
        # ----------------------------------------------------

        create_audit_log(
            db=db,
            action="INCIDENT_UPDATED",
            user_id=current_user_id,
            incident_id=incident.id,
            details=(
                f"Risk score: {old_risk_score} -> "
                f"{incident.risk_score}, "
                f"Severity: {old_severity} -> "
                f"{incident.severity}, "
                f"Priority: {old_priority} -> "
                f"{incident.priority}, "
                f"Status: {old_status} -> "
                f"{incident.status}"
            )
        )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        db.commit()

        db.refresh(incident)

        # ----------------------------------------------------
        # REAL-TIME UPDATE
        # ----------------------------------------------------

        await publish_event({
            "type": "incident_updated",
            "incident_id": incident.id,
            "old_severity": old_severity,
            "new_severity": incident.severity,
            "old_risk_score": old_risk_score,
            "new_risk_score": incident.risk_score,
            "old_priority": old_priority,
            "new_priority": incident.priority,
            "old_status": old_status,
            "new_status": incident.status,
            "priority_reason": incident.priority_reason
        })

        return incident

    except Exception:

        db.rollback()

        raise


# ============================================================
# DELETE INCIDENT
# ============================================================

def delete_incident(
    db: Session,
    incident_id: int
):

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        return None

    try:

        db.delete(incident)

        db.commit()

        return incident

    except Exception:

        db.rollback()

        raise