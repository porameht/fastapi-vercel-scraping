from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import os

from app.db.mongo import MongoDB
from app.scrapper import goal

load_dotenv()
class Item(BaseModel):
    name: str
    description: str
    price: float
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoDB(os.getenv('MONGO_URI'), os.getenv('MONGO_DB_NAME'))
    print("✅ lifespan start")
    yield
    app.mongodb_client.client.close()
    print("❌ lifespan end")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI! Scraping"}

@app.get('/goal')
async def get():
    try:
        return goal()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/items/")
async def create_item(item: Item):
    try:
        inserted_id = app.mongodb_client.create('items', item.dict())
        return {"inserted_id": str(inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)