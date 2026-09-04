from pydantic import BaseModel, Field, ConfigDict


class IncidentCreate(BaseModel):
    incident_type: str = Field(
        min_length=3,
        max_length=50
    )

    description: str = Field(
        min_length=10,
        max_length=500
    )

    severity: int = Field(
        ge=1,
        le=5
    )

    people_affected: int = Field(
        default=0,
        ge=0,
        le=100000
    )

    people_trapped: int = Field(
        default=0,
        ge=0,
        le=100000
    )

    escalating: bool = False

    latitude: float = Field(
        ge=-90,
        le=90
    )

    longitude: float = Field(
        ge=-180,
        le=180
    )


class IncidentUpdate(BaseModel):
    severity: int | None = Field(
        default=None,
        ge=1,
        le=5
    )

    people_affected: int | None = Field(
        default=None,
        ge=0,
        le=100000
    )

    people_trapped: int | None = Field(
        default=None,
        ge=0,
        le=100000
    )

    escalating: bool | None = None

    status: str | None = None


class IncidentResponse(BaseModel):
    id: int

    incident_type: str

    description: str

    severity: int

    people_affected: int

    people_trapped: int

    escalating: bool

    risk_score: int

    priority: str

    priority_reason: str

    status: str

    latitude: float

    longitude: float

    created_by: int | None

    model_config = ConfigDict(
        from_attributes=True
    )