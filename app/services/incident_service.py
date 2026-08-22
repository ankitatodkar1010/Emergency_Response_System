from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


def calculate_priority(severity: int) -> str:

    if severity == 5:
        return "CRITICAL"

    if severity == 4:
        return "HIGH"

    if severity == 3:
        return "MEDIUM"

    return "LOW"


# CREATE INCIDENT
def create_incident(db: Session, incident: IncidentCreate):

    priority = calculate_priority(incident.severity)

    new_incident = Incident(
        incident_type=incident.incident_type,
        description=incident.description,
        severity=incident.severity,
        priority=priority,
        status="reported"
    )

    try:
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)

    except Exception:
        db.rollback()
        raise

    return new_incident

    try:
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)

        return new_incident

    except Exception:
        db.rollback()
        raise


# GET ALL INCIDENTS
def get_incidents(db: Session):

    return db.query(Incident).all()


# GET ONE INCIDENT
def get_incident(db: Session, incident_id: int):

    return db.query(Incident).filter(
        Incident.id == incident_id
    ).first()


# UPDATE INCIDENT
def update_incident(
    db: Session,
    incident_id: int,
    data: IncidentUpdate
):

    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if incident is None:
        return None

    try:

        if data.severity is not None:
            incident.severity = data.severity
            incident.priority = calculate_priority(
                data.severity
            )

        if data.status is not None:
            incident.status = data.status

        db.commit()
        db.refresh(incident)

        return incident

    except Exception:
        db.rollback()
        raise


# DELETE INCIDENT
def delete_incident(
    db: Session,
    incident_id: int
):

    incident = db.query(Incident).filter(
        Incident.id == incident_id
    ).first()

    if incident is None:
        return None

    try:

        db.delete(incident)
        db.commit()

        return incident

    except Exception:
        db.rollback()
        raise