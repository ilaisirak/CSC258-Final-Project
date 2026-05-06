# Entry point for the submission service. Configures the FastAPI application,
# registers routes, and handles startup/shutdown via lifespan.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "service-submission"}