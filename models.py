from pydantic import BaseModel, Field
from typing import Optional


class CacheItem(BaseModel):
    """Model for cache item with key and value."""
    key: str = Field(..., description="Cache key", min_length=1, max_length=255)
    value: str = Field(..., description="Cache value", max_length=10000)
    ttl: Optional[int] = Field(None, description="Time to live in seconds", ge=1)


class CacheResponse(BaseModel):
    """Response model for cache operations."""
    key: str
    value: Optional[str] = None
    found: bool = False
    message: str = ""


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str
    timestamp: str
    version: str
    components: dict = {}


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str
    timestamp: str