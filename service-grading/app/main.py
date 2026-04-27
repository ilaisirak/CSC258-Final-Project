# Entry point for the grading service. Configures the FastAPI application,
# registers routes, and handles startup/shutdown events via lifespan.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.routes import router

# Creates all database tables on startup if they don't already exist,
# and disposes of the connection pool cleanly on shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router)

# Basic health check endpoint used by Docker and Kubernetes to confirm
# the service is running and ready to accept requests.
@app.get("/health")
def health():
    return {"status": "ok", "service": "service-grading"}