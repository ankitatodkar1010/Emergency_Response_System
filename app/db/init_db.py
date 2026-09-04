from app.db.database import Base, engine

# Import all models so SQLAlchemy knows about every table
from app.models.user import User
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit_log import AuditLog


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created successfully.")

