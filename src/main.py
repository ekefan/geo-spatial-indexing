from fastapi import FastAPI

from geo_bucket import router as bucket_router
from property import router as property_router


app = FastAPI(
    title="Geo-Spatial Indexing and Property Retrieval",
    version="1.0.0",
)
app.include_router(property_router, prefix="/api")
app.include_router(bucket_router, prefix="/api")
