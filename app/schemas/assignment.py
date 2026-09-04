from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    incident_id: int
    responder_id: int


class AssignmentStatusUpdate(BaseModel):
    status: Literal[
        "ACCEPTED",
        "REJECTED",
        "IN_PROGRESS",
        "COMPLETED"
    ]


class AssignmentResponse(BaseModel):
    id: int
    incident_id: int
    responder_id: int
    status: str
    assigned_at: datetime

    class Config:
        from_attributes = True