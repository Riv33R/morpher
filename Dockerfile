# Базовый образ: официальный Python 3.11 минимального размера
FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="morpher-api" \
      description="Локальный сервис склонения русских слов по падежам"

# Переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# --- Слой с зависимостями (кэшируется отдельно от кода) ---
# Копируем только файл зависимостей, чтобы слой пересобирался
# только при изменении requirements.txt, а не при изменении кода приложения
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Слой с кодом приложения ---
COPY main.py .

# Создаём непривилегированного пользователя и переключаемся на него.
# Запуск от root в контейнере — риск безопасности.
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

USER appuser

# Открываем порт, на котором будет работать uvicorn
EXPOSE 8000

# Команда запуска сервиса
# --host 0.0.0.0 необходим для доступа извне контейнера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
