from typing import Literal

from pydantic import BaseModel


class AvailabilityUpdate(BaseModel):
    availability_status: Literal[
        "AVAILABLE",
        "OFFLINE"
    ]