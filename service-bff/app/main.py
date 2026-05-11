from fastapi import FastAPI

from app.routes import router


# BFF has no persistent state, so no lifespan / engine setup.
app = FastAPI()
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "service-bff"}
