import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# APPLICATION
# ============================================================

APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY is not set"
    )

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60"
    )
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set"
    )


# ============================================================
# REDIS
# ============================================================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

REDIS_CHANNEL_NAME = os.getenv(
    "REDIS_CHANNEL_NAME",
    "emergency_events"
)