from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import require_role

from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentStatusUpdate,
    AssignmentResponse
)

from app.services.assignment_service import (
    assign_responder,
    get_assignments,
    get_assignment,
    update_assignment_status
)


router = APIRouter()


# ============================================================
# MANUAL ASSIGN RESPONDER
# ADMIN ONLY
# ============================================================

@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=201
)
async def assign_responder_route(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    try:
        assignment = await  assign_responder(
            db=db,
            incident_id=data.incident_id,
            responder_id=data.responder_id,
            current_user_id=current_user.id
        )

        if assignment is None:
            raise HTTPException(
                status_code=404,
                detail="Incident or responder not found"
            )

        return assignment

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )


# ============================================================
# GET ALL ASSIGNMENTS
# ADMIN ONLY
# ============================================================

@router.get(
    "/assignments",
    response_model=list[AssignmentResponse]
)
def get_assignments_route(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    return get_assignments(db)


# ============================================================
# GET ONE ASSIGNMENT
# ADMIN ONLY
# ============================================================

@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse
)
def get_assignment_route(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("ADMIN"))
):
    assignment = get_assignment(
        db=db,
        assignment_id=assignment_id
    )

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    return assignment


# ============================================================
# UPDATE ASSIGNMENT STATUS
# RESPONDER ONLY
# ============================================================

@router.patch(
    "/assignments/{assignment_id}/status",
    response_model=AssignmentResponse
)
async def update_assignment_status_route(
    assignment_id: int,
    data: AssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESPONDER"))
):
    try:
        assignment = await update_assignment_status(
            db=db,
            assignment_id=assignment_id,
            new_status=data.status,
            current_user_id=current_user.id
        )

        if assignment is None:
            raise HTTPException(
                status_code=404,
                detail="Assignment not found"
            )

        return assignment

    except PermissionError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )