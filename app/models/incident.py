from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    incident_type: Mapped[str] = mapped_column(
        String(50)
    )

    description: Mapped[str] = mapped_column(
        String(500)
    )

    severity: Mapped[int] = mapped_column(
        Integer
    )

    priority: Mapped[str] = mapped_column(
        String(20)
    )

    status: Mapped[str] = mapped_column(
        String(30)
    )