from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from typing import Optional

from config import settings
from models import CacheItem, CacheResponse, HealthResponse, ErrorResponse
from redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    
    yield
    
    redis_client.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A simple FastAPI application with Azure Redis cache integration and Application Insights",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic application information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/cache/{key}", response_model=CacheResponse)
async def get_cache_value(key: str):
    """
    Get value from Redis cache by key.
    
    Args:
        key: The cache key to retrieve
        
    Returns:
        CacheResponse with the cached value if found
    """
    try:
        
        value = await redis_client.get_value(key)
        
        if value is not None:
            return CacheResponse(
                key=key,
                value=value,
                found=True,
                message="Value retrieved successfully"
            )
        else:
            return CacheResponse(
                key=key,
                found=False,
                message="Key not found in cache"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache value: {str(e)}")


@app.get("/cache", response_model=CacheResponse)
async def get_default_cache_value(key: Optional[str] = Query(None, description="Cache key to retrieve")):
    """
    Get value from Redis cache. If no key is provided, uses the default key from environment.
    
    Args:
        key: Optional cache key. If not provided, uses settings.default_key
        
    Returns:
        CacheResponse with the cached value if found
    """
    cache_key = key if key is not None else settings.default_key
    
    return await get_cache_value(cache_key)


@app.post("/cache", response_model=CacheResponse)
async def set_cache_value(item: CacheItem):
    """
    Store key-value pair in Redis cache.
    
    Args:
        item: CacheItem containing key, value, and optional TTL
        
    Returns:
        CacheResponse confirming the operation
    """
    try:
        success = await redis_client.set_value(item.key, item.value, item.ttl)
        
        if success:
            return CacheResponse(
                key=item.key,
                value=item.value,
                found=True,
                message="Value stored successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to store value in cache")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set cache value: {str(e)}")


@app.delete("/cache/{key}", response_model=CacheResponse)
async def delete_cache_value(key: str):
    """
    Delete value from Redis cache by key.
    
    Args:
        key: The cache key to delete
        
    Returns:
        CacheResponse confirming the deletion
    """
    try:
        success = await redis_client.delete_value(key)
        
        if success:
            return CacheResponse(
                key=key,
                found=True,
                message="Value deleted successfully"
            )
        else:
            return CacheResponse(
                key=key,
                found=False,
                message="Key not found in cache"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache value: {str(e)}")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint that verifies the application and its dependencies.
    
    Returns:
        HealthResponse with overall health status and component details
    """
    try:
        
        # Check Redis health
        redis_health = await redis_client.health_check()
        
        # Determine overall status
        overall_status = "healthy" if redis_health["status"] == "healthy" else "unhealthy"
        
        response = HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version=settings.app_version,
            components={
                "redis": redis_health,
                "api": {
                    "status": "healthy",
                    "name": settings.app_name,
                    "version": settings.app_version
                }
            }
        )
        
        return response
    
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version=settings.app_version,
            components={
                "error": str(e)
            }
        )


@app.get("/health/live", response_model=dict)
async def liveness_check():
    """
    Liveness probe endpoint for Kubernetes/container orchestration.
    This endpoint should return 200 if the application is running.
    
    Returns:
        Simple status response
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/ready", response_model=dict)
async def readiness_check():
    """
    Readiness probe endpoint for Kubernetes/container orchestration.
    This endpoint should return 200 if the application is ready to serve traffic.
    
    Returns:
        Readiness status with dependency checks
    """
    try:
        
        # Check if Redis is accessible
        redis_health = await redis_client.health_check()
        is_ready = redis_health["status"] == "healthy"
        
        if is_ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {
                    "redis": "healthy"
                }
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "dependencies": {
                        "redis": "unhealthy"
                    }
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )