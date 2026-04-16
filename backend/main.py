from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.cors import setup_cors

# Import routers
from app.routers import auth, listings, expenses, income, reports, export, users, blocked_dates

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Backend API for Airbnb Property Manager",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS
setup_cors(app)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(listings.router, prefix="/listings", tags=["Listings"])
app.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
app.include_router(income.router, prefix="/income", tags=["Income"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(blocked_dates.router, prefix="/blocked-dates", tags=["Blocked Dates"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Airbnb Property Manager API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
