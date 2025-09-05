"""
FastAPI main application for co-lending backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables, init_sample_data
from app.api import allocate, batch, admin

# Create FastAPI app
app = FastAPI(
    title="Co-Lending FastAPI Backend",
    description="FastAPI backend for co-lending loan allocation using weighted random selection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(allocate.router)
app.include_router(batch.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and sample data on startup"""
    create_tables()
    init_sample_data()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Co-Lending FastAPI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "co-lending-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)