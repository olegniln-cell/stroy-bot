import uuid

# Хранилище сгенерированных ID (только для текущего запуска тестов)
_issued_tg_ids: set[int] = set()


def unique_tg_id() -> int:
    """Генерирует уникальный tg_id для тестов (без повторов в рамках одного запуска)."""
    while True:
        tg_id = int(uuid.uuid4().int % 1_000_000_000)
        if tg_id not in _issued_tg_ids:
            _issued_tg_ids.add(tg_id)
            return tg_id
