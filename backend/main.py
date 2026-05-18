from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import close_pool, init_db
from .routers import records, settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_pool()

app = FastAPI(title="WorkTime API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(records.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
