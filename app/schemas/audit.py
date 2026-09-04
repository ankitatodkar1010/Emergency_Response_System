from pydantic import BaseModel
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    incident_id: int | None
    assignment_id: int | None
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True
