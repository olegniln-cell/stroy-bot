# middlewares/metrics_middleware.py
import time
from prometheus_client import Counter, Histogram, CollectorRegistry

# Используем внешний registry, в main.py будем импортировать registry и эти метрики с ним создавать.
REQUESTS = None
ERRORS = None
LATENCY = None


def init_metrics(registry: CollectorRegistry):
    global REQUESTS, ERRORS, LATENCY
    REQUESTS = Counter(
        "bot_requests_total",
        "Total bot requests handled",
        ["handler"],
        registry=registry,
    )
    ERRORS = Counter(
        "bot_errors_total", "Total bot errors", ["handler"], registry=registry
    )
    LATENCY = Histogram(
        "bot_handler_latency_seconds",
        "Bot handler latency",
        ["handler"],
        registry=registry,
    )


class MetricsMiddleware:
    def __init__(self):
        pass

    async def __call__(self, handler, event, data):
        handler_name = getattr(handler, "__name__", "unknown")
        start = time.time()
        try:
            REQUESTS.labels(handler=handler_name).inc()
            result = await handler(event, data)
            return result
        except Exception:
            ERRORS.labels(handler=handler_name).inc()
            raise
        finally:
            LATENCY.labels(handler=handler_name).observe(time.time() - start)
