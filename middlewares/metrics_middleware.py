# middlewares/metrics_middleware.py
import time
from prometheus_client import Counter, Histogram, CollectorRegistry

# Используем внешний registry, в main.py будем импортировать registry и эти метрики с ним создавать.
# Можно вызвать init_metrics(registry) один раз в main.py при старте приложения.
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
        "bot_latency_seconds",
        "Bot handler latency",
        ["handler"],
        registry=registry,
    )


class MetricsMiddleware:
    def __init__(self):
        pass

    async def __call__(self, handler, event, data):
        handler_name = getattr(handler, "__name__", "unknown")

        # ✅ Добавляем вот этот блок:
        if REQUESTS is None:
            # Метрики не инициализированы (например, локальный запуск без Prometheus)
            return await handler(event, data)

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
