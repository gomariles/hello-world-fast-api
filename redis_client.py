import redis
import logging
from typing import Optional, Dict, Any, Tuple, Union
from azure.identity import DefaultAzureCredential
from redis.credentials import CredentialProvider
from config import settings


class EntraIDCredentialProvider(CredentialProvider):
    """Credential provider for Azure Entra ID authentication with Managed Identity."""
    
    def __init__(self, username: str = "default"):
        """
        Initialize the Entra ID credential provider.
        
        Args:
            username: The username for Redis authentication (typically "default" or object ID)
        """
        self.username = username
        self.credential = DefaultAzureCredential()
        self.logger = logging.getLogger(__name__)
        self._token = None
        self._token_expiry = 0
    
    def get_credentials(self) -> Union[Tuple[str], Tuple[str, str]]:
        """
        Get credentials for Redis authentication.
        Returns a tuple of (username, token) for Entra ID authentication.
        """
        import time
        
        # Refresh token if it's expired or about to expire (5 minutes buffer)
        current_time = time.time()
        if self._token is None or current_time >= (self._token_expiry - 300):
            try:
                # Azure Redis Cache scope
                token = self.credential.get_token("https://redis.azure.com/.default")
                self._token = token.token
                self._token_expiry = token.expires_on
                self.logger.info("Successfully obtained new Entra ID token for Redis")
            except Exception as e:
                self.logger.error(f"Failed to obtain Entra ID token: {str(e)}")
                raise
        
        return (self.username, self._token)


class RedisClient:
    """Redis client wrapper with connection management and error handling."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
    
    def _get_client(self) -> redis.Redis:
        """Get or create Redis client with proper configuration."""
        if self._client is None:
            try:
                # Create credential provider for Entra ID or use password authentication
                if settings.redis_use_entraid:
                    self.logger.info("Configuring Redis client with Entra ID authentication")
                    credential_provider = EntraIDCredentialProvider(username=settings.redis_username)
                    
                    self._client = redis.Redis(
                        host=settings.redis_host,
                        port=settings.redis_port,
                        ssl=settings.redis_ssl,
                        db=settings.redis_db,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        credential_provider=credential_provider
                    )
                else:
                    self.logger.info("Configuring Redis client with password authentication")
                    self._client = redis.Redis(
                        host=settings.redis_host,
                        port=settings.redis_port,
                        password=settings.redis_password,
                        ssl=settings.redis_ssl,
                        db=settings.redis_db,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                
                # Test connection
                self._client.ping()
                self.logger.info("Redis connection established successfully")
            except Exception as e:
                self.logger.error(f"Failed to connect to Redis: {str(e)}")
                raise
        return self._client
    
    async def get_value(self, key: str) -> Optional[str]:
        """Get value from Redis cache."""
        try:
            client = self._get_client()
            value = client.get(key)
            self.logger.info(f"Retrieved key '{key}' from Redis")
            return value
        except Exception as e:
            self.logger.error(f"Error getting key '{key}' from Redis: {str(e)}")
            raise
    
    async def set_value(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache with optional TTL."""
        try:
            client = self._get_client()
            result = client.set(key, value, ex=ttl)
            self.logger.info(f"Set key '{key}' in Redis with TTL: {ttl}")
            return result
        except Exception as e:
            self.logger.error(f"Error setting key '{key}' in Redis: {str(e)}")
            raise
    
    async def delete_value(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            client = self._get_client()
            result = client.delete(key) > 0
            self.logger.info(f"Deleted key '{key}' from Redis")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting key '{key}' from Redis: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        try:
            client = self._get_client()
            ping_result = client.ping()
            info = client.info()
            
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "ping": ping_result,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown")
            }
        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
            self.logger.info("Redis connection closed")


# Global Redis client instance
redis_client = RedisClient()