from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User

from app.db.database import SessionLocal
from app.core.redis_pubsub import publish_event


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )

    db.add(notification)
    db.flush()

    return notification


# ============================================================
# GET USER NOTIFICATIONS
# ============================================================

def get_user_notifications(
    db: Session,
    user_id: int
):
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )


# ============================================================
# GET UNREAD NOTIFICATIONS
# ============================================================

def get_unread_notifications(
    db: Session,
    user_id: int
):
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )


# ============================================================
# MARK NOTIFICATION AS READ
# ============================================================

def mark_notification_as_read(
    db: Session,
    notification_id: int,
    user_id: int
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        .first()
    )

    if notification is None:
        return None

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


# ============================================================
# SEND INCIDENT NOTIFICATION
# ============================================================

async def send_incident_notification(
    incident_id: int,
    incident_type: str,
    severity: int,
    priority: str
):
    """
    Background task for sending incident notifications.

    Creates its own database session because this function
    runs after the HTTP request has completed.
    """

    db = SessionLocal()

    try:

        title = "New Emergency Incident"

        message = (
            f"New {incident_type} incident created. "
            f"Incident ID: {incident_id}, "
            f"Severity: {severity}, "
            f"Priority: {priority}"
        )

        # ----------------------------------------------------
        # Find available responders
        # ----------------------------------------------------

        responders = (
            db.query(User)
            .filter(
                User.role == "RESPONDER",
                User.availability_status == "ONLINE"
            )
            .all()
        )

        # ----------------------------------------------------
        # Create notification for each responder
        # ----------------------------------------------------

        notification_count = 0

        for responder in responders:

            create_notification(
                db=db,
                user_id=responder.id,
                title=title,
                message=message,
                notification_type="INCIDENT"
            )

            notification_count += 1

        # ----------------------------------------------------
        # Save notifications to PostgreSQL
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # Publish real-time Redis event
        # ----------------------------------------------------

        if notification_count > 0:

            await publish_event({
                "type": "new_incident",
                "incident_id": incident_id,
                "incident_type": incident_type,
                "severity": severity,
                "priority": priority,
                "notification_type": "INCIDENT",
                "message": message,
                "recipient_count": notification_count
            })

        return notification_count

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()