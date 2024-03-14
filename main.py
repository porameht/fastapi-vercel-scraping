from fastapi import FastAPI
import uvicorn

from app.scrapper import goal1

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

@app.get('/goal1')
def goal():
    return goal1()

# @app.get("/api/cron/1h")
# async def cron():
#     return {"message": "Hello cron 1h from FastAPI!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)