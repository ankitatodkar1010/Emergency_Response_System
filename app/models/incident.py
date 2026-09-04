from sqlalchemy import String, Integer, ForeignKey, Float, Boolean
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

    people_affected: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    people_trapped: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    escalating: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20)
    )

    priority_reason: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30)
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )