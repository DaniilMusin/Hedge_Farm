from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import price
from .config import settings

app = FastAPI(title="HedgeFarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(price.router)

@app.get("/health")
def health():
    return {"status": "ok"}