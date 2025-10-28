# FastAPI Redis Cache API

A simple FastAPI application with Azure Redis cache integration and Application Insights telemetry.

## Features

- **FastAPI** with automatic OpenAPI documentation
- **Azure Redis Cache** integration for high-performance caching
- **Application Insights** for comprehensive telemetry and monitoring
- **Health checks** with liveness, readiness, and health endpoints
- **Pydantic models** for request/response validation
- **Comprehensive error handling** and logging
- **Environment-based configuration**

## Endpoints

### Cache Operations
- `GET /cache/{key}` - Get value by key from cache
- `GET /cache?key=<key>` - Get value by key (optional query parameter)
- `POST /cache` - Store key-value pair in cache
- `DELETE /cache/{key}` - Delete key from cache

### Health Endpoints
- `GET /health` - Comprehensive health check with component status
- `GET /health/live` - Liveness probe (Kubernetes compatible)
- `GET /health/ready` - Readiness probe (Kubernetes compatible)

### Documentation
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Setup

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and update with your values:

```powershell
Copy-Item .env.example .env
```

Edit `.env` file with your configuration:

```env
# Redis Configuration
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_SSL=true

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string

# App Settings
DEFAULT_KEY=default
DEBUG=false
```

### 3. Run the Application

#### Development
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production
```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

### Redis Settings
- `REDIS_HOST` - Redis server hostname
- `REDIS_PORT` - Redis server port (default: 6379)
- `REDIS_PASSWORD` - Redis authentication password
- `REDIS_SSL` - Enable SSL connection (true/false)
- `REDIS_DB` - Redis database number (default: 0)

### Application Insights
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - Connection string for Azure Application Insights

### Application Settings
- `DEFAULT_KEY` - Default key used when no key is provided to GET endpoint
- `APP_NAME` - Application name for logging and health checks
- `APP_VERSION` - Application version
- `DEBUG` - Enable debug mode (true/false)

## API Usage Examples

### Store a value
```bash
curl -X POST "http://localhost:8000/cache" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "user:123",
    "value": "John Doe",
    "ttl": 3600
  }'
```

### Get a value by key
```bash
curl "http://localhost:8000/cache/user:123"
```

### Get default value
```bash
curl "http://localhost:8000/cache"
```

### Delete a value
```bash
curl -X DELETE "http://localhost:8000/cache/user:123"
```

### Check health
```bash
curl "http://localhost:8000/health"
```

## Docker Support

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and run
```powershell
docker build -t fastapi-redis-cache .
docker run -p 8000:8000 --env-file .env fastapi-redis-cache
```

## Monitoring

The application includes comprehensive telemetry with Application Insights:

- **Request tracking** - All HTTP requests are automatically tracked
- **Dependency tracking** - Redis operations are tracked as dependencies
- **Custom events** - Cache hits, misses, and application lifecycle events
- **Error tracking** - Exceptions and errors are automatically captured
- **Performance metrics** - Response times and throughput metrics

## Security Considerations

- Use Azure Managed Identity for Redis authentication when possible
- Store sensitive configuration in Azure Key Vault
- Enable SSL/TLS for Redis connections in production
- Implement proper authentication and authorization for your API endpoints
- Use HTTPS in production environments

## Error Handling

The application includes comprehensive error handling:

- **Global exception handler** for unhandled errors
- **Specific error responses** for cache operations
- **Structured error responses** with timestamps and details
- **Automatic error logging** to Application Insights

## Best Practices Implemented

- **Connection pooling** for Redis with health checks
- **Retry logic** for transient failures
- **Proper resource cleanup** on application shutdown
- **Environment-based configuration** for different deployment environments
- **Structured logging** with correlation IDs
- **Health check endpoints** for container orchestration
- **Input validation** with Pydantic models