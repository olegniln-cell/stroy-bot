import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Счётчики запросов
REQUEST_COUNT = Counter("requests_total", "Total requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram(
    "requests_latency_seconds", "Request latency (s)", ["endpoint"]
)


# Middleware — для FastAPI или aiohttp
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    return response


# Endpoint /metrics
async def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
