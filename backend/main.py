from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.configurations import router as configurations_router

app = FastAPI(title="T5.1 API")

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

app.include_router(configurations_router)

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
