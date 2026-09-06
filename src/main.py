from fastapi import FastAPI

app: FastAPI = FastAPI()

@app.post("/api/properties")
async def create_properties():
    return {"message": "properties"}

@app.get("/api/properties/search")
async def search_properties():
    return {"running": "in progresss"}

@app.get("/api/geo-buckets/stats")
async def geo_bucket_stats():
    return {"stats": "bucket stats"}