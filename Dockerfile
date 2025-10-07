FROM python:3.12-slim

WORKDIR /app

# ставим зависимости
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# копируем весь код
COPY . .

# для красивых логов
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
