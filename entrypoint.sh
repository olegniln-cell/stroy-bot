#!/bin/sh
set -e

# Обработчик завершения контейнера
trap 'echo "🧩 Caught SIGTERM, shutting down gracefully..."; exit 0' TERM INT

# Запускаем основное приложение
echo "🚀 Starting main process: $@"
exec "$@"
