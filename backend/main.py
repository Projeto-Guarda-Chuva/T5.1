from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

from app.routers.auth import router as auth_router
from app.routers.configurations import router as configurations_router
from app.routers.operation_logs import router as operation_logs_router
from app.routers.participantes import router as participantes_router


async def _seed_admin() -> None:
    from app.repositories.user_repository import UserRepository
    repo = UserRepository()
    if not await repo.exists_any():
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        await repo.create({
            "username": "admin",
            "hashed_password": ctx.hash("admin123"),
            "is_active": True,
        })


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _seed_admin()
    yield


app = FastAPI(title="T5.1 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(configurations_router)
app.include_router(operation_logs_router)

@app.get("/")
async def read_root() -> dict[str, str]:
    """
    Return a simple status message for the API root endpoint.

    Args:
        None.

    Returns:
        dict[str, str]: A short message confirming that the API is running.
    """
    return {"message": "T5.1 API running"}
