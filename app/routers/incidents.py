from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
    Query
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User

from app.services.notification_service import send_incident_notification

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)

from app.services.incident_service import (
    create_incident,
    get_incidents,
    get_incident,
    update_incident,
    delete_incident,
)

from app.core.dependencies import (
    get_current_user,
)


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


# ============================================================
# CREATE INCIDENT
# ADMIN + RESPONDER
# ============================================================

@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_incident_route(
    incident: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --------------------------------------------------------
    # USER, RESPONDER and ADMIN can report emergencies
    # --------------------------------------------------------

    if current_user.role not in ["USER", "RESPONDER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    created_incident = await create_incident(
        db,
        incident,
        current_user.id
    )

    # --------------------------------------------------------
    # Send notification to available responders
    # --------------------------------------------------------

    background_tasks.add_task(
        send_incident_notification,
        created_incident.id,
        created_incident.incident_type,
        created_incident.severity,
        created_incident.priority
    )

    return created_incident


# ============================================================
# GET ALL INCIDENTS
# ADMIN ONLY
# ============================================================

@router.get(
    "",
    response_model=list[IncidentResponse]
)
def get_incidents_route(
    status: str | None = None,
    severity: int | None = None,
    priority: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return get_incidents(
        db,
        status=status,
        severity=severity,
        priority=priority,
        page=page,
        limit=limit
    )


# ============================================================
# GET ONE INCIDENT
# ADMIN ONLY
# ============================================================

@router.get(
    "/{incident_id}",
    response_model=IncidentResponse
)
def get_incident_route(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    incident = get_incident(
        db,
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    return incident


# ============================================================
# UPDATE INCIDENT
# ADMIN ONLY
# ============================================================

@router.put(
    "/{incident_id}",
    response_model=IncidentResponse
)
async def update_incident_route(
    incident_id: int,
    data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    try:
        incident = await update_incident(
            db,
            incident_id,
            data,
            current_user.id
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    return incident


# ============================================================
# DELETE INCIDENT
# ADMIN ONLY
# ============================================================

@router.delete(
    "/{incident_id}"
)
def delete_incident_route(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    incident = delete_incident(
        db,
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

    return {
        "message": "Incident deleted successfully",
        "incident_id": incident_id
    }

