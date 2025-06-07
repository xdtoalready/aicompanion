FROM python:3.11-slim

# Метаданные
LABEL maintainer="AI Companion Developer"
LABEL description="Психологически достоверный AI-компаньон"
LABEL version="1.0"

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для приложения
RUN useradd --create-home --shell /bin/bash companion
WORKDIR /home/companion

# Копируем файлы зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY --chown=companion:companion . .

# Создаем необходимые директории
RUN mkdir -p data logs config && \
    chown -R companion:companion /home/companion

# Переключаемся на пользователя приложения
USER companion

# Порт для веб-интерфейса (если будет)
EXPOSE 5000

# Переменные окружения
ENV PYTHONPATH=/home/companion
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]