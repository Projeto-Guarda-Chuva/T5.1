from fastapi import FastAPI

app = FastAPI(title="T5.1 API")


@app.get("/")
async def root():
    return {"message": "T5.1 API running"}
