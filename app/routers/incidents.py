from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate
)

from app.services.incident_service import (
    create_incident,
    get_incidents,
    get_incident,
    update_incident,
    delete_incident
)

from app.db.database import get_db


router = APIRouter()


# CREATE INCIDENT
@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=201
)
def create_incident_route(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    return create_incident(db, incident)


# GET ALL INCIDENTS
@router.get(
    "/incidents",
    response_model=list[IncidentResponse]
)
def get_incidents_route(
    db: Session = Depends(get_db)
):
    return get_incidents(db)


# GET ONE INCIDENT
@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse
)
def get_incident_route(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = get_incident(db, incident_id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return incident


# UPDATE INCIDENT
@router.put(
    "/incidents/{incident_id}",
    response_model=IncidentResponse
)
def update_incident_route(
    incident_id: int,
    data: IncidentUpdate,
    db: Session = Depends(get_db)
):
    incident = update_incident(
        db,
        incident_id,
        data
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return incident


# DELETE INCIDENT
@router.delete(
    "/incidents/{incident_id}",
    status_code=204
)
def delete_incident_route(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = delete_incident(
        db,
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return None