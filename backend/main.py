from fastapi import FastAPI
from .routers import participantes 

app = FastAPI(title="T5.1 API")

app.include_router(participantes.router) 

@app.get("/")
async def root():
    return {"message": "T5.1 API running"}