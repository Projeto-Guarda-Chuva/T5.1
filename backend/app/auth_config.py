import os

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
RESET_TOKEN_EXPIRE_MINUTES: int = 15
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
