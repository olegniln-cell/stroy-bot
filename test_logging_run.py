import asyncio
from core.logging_setup import setup_logging
from middlewares.context_middleware import ContextMiddleware
import structlog

logger = structlog.get_logger(__name__)

class DummyEvent:
    type = "test_event"
    from_user = type("User", (), {"id": 123456})()

async def test_handler(event, data):
    logger.info("handler.start", event_type=event.type)
    logger.info("handler.finish")

async def main():
    setup_logging()
    mw = ContextMiddleware()
    event = DummyEvent()
    await mw(test_handler, event, {})

asyncio.run(main())
