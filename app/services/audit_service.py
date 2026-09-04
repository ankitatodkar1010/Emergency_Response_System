from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    action: str,
    user_id: int | None = None,
    incident_id: int | None = None,
    assignment_id: int | None = None,
    details: str | None = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        incident_id=incident_id,
        assignment_id=assignment_id,
        details=details
    )

    db.add(audit_log)
    db.flush()

    return audit_log


def get_audit_logs(
    db: Session,
    incident_id: int | None = None,
    assignment_id: int | None = None,
    user_id: int | None = None
):
    query = db.query(AuditLog)

    if incident_id is not None:
        query = query.filter(
            AuditLog.incident_id == incident_id
        )

    if assignment_id is not None:
        query = query.filter(
            AuditLog.assignment_id == assignment_id
        )

    if user_id is not None:
        query = query.filter(
            AuditLog.user_id == user_id
        )

    return (
        query
        .order_by(AuditLog.created_at.desc())
        .all()
    )
