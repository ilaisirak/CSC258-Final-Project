# Entry point for the user service.
#
# This service is not the identity provider — service-auth owns login,
# refresh, logout, register, and token introspection. service-user
# exposes only profile CRUD:
#   - GET/PATCH /users/me                  (gateway, header-authenticated)
#   - GET       /users, /users/search,
#               /users/by-id/{id}          (gateway, header-authenticated)
#   - /users/internal/*                    (cluster-internal, service-auth)

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routes import internal_router, router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the users table on startup if it does not already exist.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Public profile routes — gateway-injected X-Auth-User-* headers.
app.include_router(router)

# Internal routes — service-auth only, cluster-internal mTLS.
app.include_router(internal_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "service-user"}