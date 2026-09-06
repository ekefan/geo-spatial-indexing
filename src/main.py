from fastapi import FastAPI, APIRouter

app: FastAPI = FastAPI(
    title="Geo-Spatial Indexing and Property Retrival (GSIPR)",
    version="1.0.0",
    description="API documentation for GSIPR API"
)


api_router = APIRouter(prefix="/api")
# api_router.include_router(property_router)
app.include_router(api_router)


@app.post("/api/properties")
async def create_properties():
    return {"message": "properties"}

@app.get("/api/properties/search")
async def search_properties():
    return {"running": "in progresss"}

@app.get("/api/geo-buckets/stats")
async def geo_bucket_stats():
    return {"stats": "bucket stats"}