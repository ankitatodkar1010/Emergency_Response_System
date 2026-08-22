from fastapi import FastAPI
from app.routers.incidents import router as incident_router


app = FastAPI()

app.include_router(incident_router)


@app.get("/")
def home():
    return {"message": "Emergency Response System API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}