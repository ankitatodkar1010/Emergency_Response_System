from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import get_audit_logs
from app.core.dependencies import require_role


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"]
)


# ============================================================
# GET ALL AUDIT LOGS
# ADMIN ONLY
# ============================================================

@router.get(
    "",
    response_model=list[AuditLogResponse]
)
def get_all_audit_logs(
    incident_id: int | None = None,
    assignment_id: int | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN"))
):
    return get_audit_logs(
        db,
        incident_id=incident_id,
        assignment_id=assignment_id,
        user_id=user_id
    )