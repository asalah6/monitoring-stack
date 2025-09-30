"""
Example FastAPI application with Prometheus metrics and structured logging for Loki.

All metrics follow the naming convention: appname_metricname
This example uses 'myapp' as the prefix.

To run this application:
1. pip install -r requirements.txt
2. uvicorn app:app --host 0.0.0.0 --port 8000

Metrics endpoint: http://localhost:8000/metrics
"""

from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import logging
from pythonjsonlogger import jsonlogger

# Configure structured JSON logging for Loki
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s',
    rename_fields={'asctime': 'timestamp', 'levelname': 'level', 'name': 'logger'}
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = FastAPI(title="MyApp", version="1.0.0")

# ============================================================================
# Prometheus Metrics - IMPORTANT: All metrics MUST start with 'myapp_'
# ============================================================================

# Counter: monotonically increasing value (only goes up)
myapp_http_requests_total = Counter(
    'myapp_http_requests_total',
    'Total HTTP requests received',
    ['method', 'endpoint', 'status']
)

myapp_errors_total = Counter(
    'myapp_errors_total',
    'Total number of errors',
    ['error_type']
)

# Histogram: distributions and quantiles (for timing measurements)
myapp_request_duration_seconds = Histogram(
    'myapp_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Gauge: value that can go up and down
myapp_active_connections = Gauge(
    'myapp_active_connections',
    'Number of currently active connections'
)

myapp_memory_usage_bytes = Gauge(
    'myapp_memory_usage_bytes',
    'Current memory usage in bytes'
)

myapp_database_pool_size = Gauge(
    'myapp_database_pool_size',
    'Current database connection pool size'
)

myapp_queue_size = Gauge(
    'myapp_queue_size',
    'Current size of the processing queue'
)


# ============================================================================
# Middleware for automatic request tracking
# ============================================================================

@app.middleware("http")
async def monitor_requests(request, call_next):
    """Automatically track all HTTP requests with metrics and logs."""
    # Track active connections
    myapp_active_connections.inc()
    
    # Measure request duration
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        myapp_http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        myapp_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Structured log for Loki (JSON format)
        logger.info(
            "HTTP request completed",
            extra={
                'method': request.method,
                'endpoint': request.url.path,
                'status': response.status_code,
                'duration': duration,
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )
        
        return response
    
    except Exception as e:
        myapp_errors_total.labels(error_type=type(e).__name__).inc()
        logger.error(
            "Request failed",
            extra={
                'method': request.method,
                'endpoint': request.url.path,
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        raise
    finally:
        myapp_active_connections.dec()


# ============================================================================
# Application Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Hello World",
        "app": "myapp",
        "version": "1.0.0",
        "metrics": "/metrics"
    }


@app.get("/api/users")
async def get_users():
    """Example API endpoint with simulated work."""
    import random
    
    # Simulate some processing time
    time.sleep(random.uniform(0.01, 0.1))
    
    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]
    
    logger.info("Users endpoint accessed", extra={'user_count': len(users)})
    return {"users": users}


@app.post("/api/users")
async def create_user(user: dict):
    """Example POST endpoint."""
    logger.info(
        "User created",
        extra={
            'user_id': user.get('id'),
            'user_name': user.get('name')
        }
    )
    return {"status": "created", "user": user}


@app.get("/api/error")
async def trigger_error():
    """Endpoint that triggers an error (for testing error metrics)."""
    logger.error("Intentional error triggered", extra={'endpoint': '/api/error'})
    raise ValueError("This is a test error")


@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "app": "myapp"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint for Kubernetes readiness probe."""
    # In production, check database connection, cache, etc.
    # For this example, always return ready
    return {"status": "ready", "app": "myapp"}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    This endpoint exposes all metrics in Prometheus format.
    Prometheus will scrape this endpoint periodically.
    """
    # Update gauge metrics before serving
    try:
        import psutil
        process = psutil.Process()
        myapp_memory_usage_bytes.set(process.memory_info().rss)
    except ImportError:
        # psutil not available, skip memory metric
        pass
    
    # Return metrics in Prometheus format
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(
        "Application starting",
        extra={
            'version': '1.0.0',
            'app': 'myapp'
        }
    )
    # Initialize database pool size (example)
    myapp_database_pool_size.set(10)
    myapp_queue_size.set(0)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Application shutting down", extra={'app': 'myapp'})


# ============================================================================
# Example: Custom business logic with metrics
# ============================================================================

# You can add custom metrics for your business logic
myapp_orders_processed_total = Counter(
    'myapp_orders_processed_total',
    'Total number of orders processed',
    ['status']
)

myapp_payment_amount_total = Counter(
    'myapp_payment_amount_total',
    'Total payment amount processed',
    ['currency']
)

myapp_inventory_level = Gauge(
    'myapp_inventory_level',
    'Current inventory level',
    ['product_id']
)

@app.post("/api/orders")
async def process_order(order: dict):
    """Example business endpoint with custom metrics."""
    try:
        # Simulate order processing
        order_id = order.get('order_id', 'unknown')
        amount = order.get('amount', 0)
        currency = order.get('currency', 'USD')
        
        # Update business metrics
        myapp_orders_processed_total.labels(status='success').inc()
        myapp_payment_amount_total.labels(currency=currency).inc(amount)
        
        logger.info(
            "Order processed successfully",
            extra={
                'order_id': order_id,
                'amount': amount,
                'currency': currency
            }
        )
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": "Order processed"
        }
    
    except Exception as e:
        myapp_orders_processed_total.labels(status='failed').inc()
        logger.error(
            "Order processing failed",
            extra={
                'order_id': order.get('order_id', 'unknown'),
                'error': str(e)
            }
        )
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
