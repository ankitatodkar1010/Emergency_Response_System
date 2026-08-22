from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    incident_type: str
    description: str = Field(min_length=10)
    severity: int = Field(ge=1, le=5)


class IncidentUpdate(BaseModel):
    severity: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None


class IncidentResponse(BaseModel):
    id: int
    incident_type: str
    description: str
    severity: int
    priority: str
    status: str

    model_config = {
        "from_attributes": True
    }