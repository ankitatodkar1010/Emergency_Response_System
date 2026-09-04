import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.init_db import init_db

from app.routers.incidents import router as incident_router
from app.routers.assignments import router as assignment_router
from app.routers.auth import router as auth_router
from app.routers.websocket import router as websocket_router
from app.routers.audit import router as audit_router
from app.routers.notifications import router as notification_router
from app.core.redis_pubsub import subscribe_to_events
from app.routers.users import router as user_router


redis_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global redis_task

    # Initialize database tables
    init_db()
    print("Database initialized")

    # Start Redis subscriber
    redis_task = asyncio.create_task(
        subscribe_to_events()
    )

    print("Redis subscriber started")

    try:
        yield

    finally:

        if redis_task:
            redis_task.cancel()

            try:
                await redis_task

            except asyncio.CancelledError:
                pass

        print("Redis subscriber stopped")


app = FastAPI(
    title="Emergency Response System",
    version="0.1.0",
    lifespan=lifespan
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Emergency Response System API"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# Routers
app.include_router(incident_router)
app.include_router(assignment_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(audit_router)
app.include_router(user_router)
app.include_router(notification_router)