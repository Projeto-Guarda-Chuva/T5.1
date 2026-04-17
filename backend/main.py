from fastapi import FastAPI

app = FastAPI()

print("hello")

@app.get("/")
async def root():
    return {"message": "Hello World"}