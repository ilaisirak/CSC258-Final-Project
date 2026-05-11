from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import DEFAULT_BUCKET
from app.database import Base, engine
from app.routes import router
from app.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Best-effort bucket bootstrap. If MinIO isn't reachable yet,
    # the first request will retry via ensure_bucket() in routes.
    try:
        ensure_bucket(DEFAULT_BUCKET)
    except Exception:  # noqa: BLE001
        pass
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "service-file-storage"}
