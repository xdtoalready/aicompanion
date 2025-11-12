# ⚡ FastStart - Быстрый запуск на сервере

**Цель:** Развернуть AI Companion на VPS/сервере за 10-15 минут с автозапуском

**Требования:**
- Ubuntu/Debian Linux (20.04+)
- Root или sudo доступ
- 512 MB RAM минимум (1 GB рекомендуется)
- 2 GB свободного места на диске

---

## 🚀 Вариант 1: Быстрый запуск (Python)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.12 (если нет)
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Установка дополнительных инструментов
sudo apt install -y git curl wget
```

### Шаг 2: Клонирование репозитория

```bash
# Создаём директорию для проекта
sudo mkdir -p /opt/aicompanion
sudo chown $USER:$USER /opt/aicompanion
cd /opt/aicompanion

# Клонирование
git clone <your-repo-url> .

# Или если репозиторий уже локальный - загрузите через scp/rsync
```

### Шаг 3: Настройка виртуального окружения

```bash
# Создание venv
python3.12 -m venv venv

# Активация
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 4: Конфигурация

```bash
# Копирование примера конфигурации
cp config/config.example.json config/config.json

# Редактирование (используйте nano, vim или любой редактор)
nano config/config.json
```

**Обязательно заполните:**

```json
{
  "ai": {
    "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE"
  },
  "integrations": {
    "telegram": {
      "bot_token": "YOUR_BOT_TOKEN_HERE",
      "allowed_users": [YOUR_TELEGRAM_ID]
    }
  }
}
```

**Получение ключей:**
- Gemini API: https://aistudio.google.com/app/apikey
- Telegram Bot: напишите @BotFather в Telegram
- Ваш ID: напишите @userinfobot

### Шаг 5: Тестовый запуск

```bash
# Проверка конфигурации
python main.py

# Должно появиться:
# 🚀 AI Companion starting...
# ✅ Configuration loaded
# ✅ Database initialized
# ✅ ChromaDB vector memory ready
# ✅ Gemini API connected
# ✅ Telegram bot started
# 🎉 AI Companion is running!

# Нажмите Ctrl+C для остановки
```

---

## 🔄 Настройка автозапуска (systemd)

### Создание systemd service

```bash
# Создаём service файл
sudo nano /etc/systemd/system/aicompanion.service
```

**Содержимое файла:**

```ini
[Unit]
Description=AI Companion Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/opt/aicompanion
Environment="PATH=/opt/aicompanion/venv/bin"
ExecStart=/opt/aicompanion/venv/bin/python /opt/aicompanion/main.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/aicompanion/logs/systemd.log
StandardError=append:/opt/aicompanion/logs/systemd_error.log

# Ограничения ресурсов
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

**Замените:**
- `YOUR_USERNAME` на ваше имя пользователя (выполните `whoami` для проверки)

### Активация сервиса

```bash
# Создание директории для логов (если нет)
mkdir -p /opt/aicompanion/logs

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable aicompanion.service

# Запуск сервиса
sudo systemctl start aicompanion.service

# Проверка статуса
sudo systemctl status aicompanion.service
```

**Ожидаемый вывод:**

```
● aicompanion.service - AI Companion Service
   Loaded: loaded (/etc/systemd/system/aicompanion.service; enabled)
   Active: active (running) since Mon 2025-11-12 10:00:00 UTC; 5s ago
```

### Управление сервисом

```bash
# Остановка
sudo systemctl stop aicompanion.service

# Перезапуск
sudo systemctl restart aicompanion.service

# Просмотр логов
sudo journalctl -u aicompanion.service -f

# Последние 100 строк логов
sudo journalctl -u aicompanion.service -n 100

# Просмотр логов приложения
tail -f /opt/aicompanion/logs/companion.log
```

---

## 🐳 Вариант 2: Запуск через Docker (рекомендуется)

### Шаг 1: Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения прав
sudo reboot
```

### Шаг 2: Подготовка проекта

```bash
# Клонирование
cd /opt
sudo mkdir aicompanion
sudo chown $USER:$USER aicompanion
cd aicompanion
git clone <your-repo-url> .

# Настройка конфигурации
cp config/config.example.json config/config.json
nano config/config.json
```

### Шаг 3: Создание Dockerfile (если нет)

```bash
nano Dockerfile
```

**Содержимое Dockerfile:**

```dockerfile
FROM python:3.12-slim

# Метаданные
LABEL maintainer="your-email@example.com"
LABEL version="3.0"
LABEL description="AI Companion with Gemini API and ChromaDB"

# Рабочая директория
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python пакетов
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директорий для данных
RUN mkdir -p /app/data /app/logs /app/data/chroma_memory

# Экспозиция порта (если используется веб-интерфейс)
EXPOSE 5000

# Команда запуска
CMD ["python", "main.py"]
```

### Шаг 4: Создание docker-compose.yml

```bash
nano docker-compose.yml
```

**Содержимое docker-compose.yml:**

```yaml
version: '3.8'

services:
  aicompanion:
    build: .
    container_name: aicompanion
    restart: unless-stopped

    volumes:
      # Конфигурация (read-only)
      - ./config:/app/config:ro
      # Персонажи (read-only)
      - ./characters:/app/characters:ro
      # Промпты (read-only)
      - ./prompts:/app/prompts:ro
      # Данные (read-write)
      - ./data:/app/data
      # Логи (read-write)
      - ./logs:/app/logs

    environment:
      - TZ=Europe/Moscow  # Ваш часовой пояс
      - PYTHONUNBUFFERED=1

    # Ограничения ресурсов
    mem_limit: 512m
    cpus: 1.0

    # Логирование
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

# Опционально: сеть для будущих расширений
networks:
  default:
    name: aicompanion-network
```

### Шаг 5: Запуск Docker

```bash
# Сборка образа
docker-compose build

# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

### Автозапуск Docker при старте системы

Docker с флагом `restart: unless-stopped` автоматически запустится при старте системы.

**Дополнительно можно создать systemd service:**

```bash
sudo nano /etc/systemd/system/aicompanion-docker.service
```

```ini
[Unit]
Description=AI Companion Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/aicompanion
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable aicompanion-docker.service
sudo systemctl start aicompanion-docker.service
```

---

## 🔍 Мониторинг и обслуживание

### Проверка работоспособности

```bash
# Для Python варианта
sudo systemctl status aicompanion.service
tail -f /opt/aicompanion/logs/companion.log

# Для Docker варианта
docker-compose ps
docker-compose logs -f aicompanion
```

### Обновление приложения

**Python вариант:**

```bash
cd /opt/aicompanion

# Остановка сервиса
sudo systemctl stop aicompanion.service

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Запуск
sudo systemctl start aicompanion.service
```

**Docker вариант:**

```bash
cd /opt/aicompanion

# Остановка
docker-compose down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose up -d --build
```

### Резервное копирование

```bash
# Создание backup директории
mkdir -p ~/backups

# Backup данных и конфигурации
tar -czf ~/backups/aicompanion-backup-$(date +%Y%m%d).tar.gz \
  /opt/aicompanion/data \
  /opt/aicompanion/config/config.json \
  /opt/aicompanion/characters

# Автоматический backup через cron (каждый день в 3:00)
crontab -e

# Добавить строку:
0 3 * * * tar -czf ~/backups/aicompanion-backup-$(date +\%Y\%m\%d).tar.gz /opt/aicompanion/data /opt/aicompanion/config/config.json
```

### Восстановление из backup

```bash
# Остановка сервиса
sudo systemctl stop aicompanion.service
# или
docker-compose down

# Восстановление
cd /opt/aicompanion
tar -xzf ~/backups/aicompanion-backup-20251112.tar.gz

# Запуск
sudo systemctl start aicompanion.service
# или
docker-compose up -d
```

---

## 🔒 Безопасность

### 1. Файрвол (UFW)

```bash
# Установка UFW
sudo apt install ufw

# Разрешение SSH (ВАЖНО! Иначе потеряете доступ)
sudo ufw allow 22/tcp

# Если используете веб-интерфейс
sudo ufw allow 5000/tcp

# Включение файрвола
sudo ufw enable

# Проверка статуса
sudo ufw status
```

### 2. Защита конфигурационных файлов

```bash
# Ограничение прав доступа
chmod 600 /opt/aicompanion/config/config.json

# Владелец только ваш пользователь
chown $USER:$USER /opt/aicompanion/config/config.json
```

### 3. Обновления безопасности

```bash
# Автоматические обновления безопасности
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🐛 Решение проблем

### Проблема 1: Сервис не запускается

```bash
# Проверка логов systemd
sudo journalctl -u aicompanion.service -n 50

# Проверка логов приложения
tail -n 100 /opt/aicompanion/logs/companion.log

# Проверка прав доступа
ls -la /opt/aicompanion/config/config.json

# Ручной запуск для диагностики
cd /opt/aicompanion
source venv/bin/activate
python main.py
```

### Проблема 2: API не работает

```bash
# Тест Gemini API
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_KEY"

# Тест Telegram Bot
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"

# Проверка сетевого подключения
ping -c 3 api.telegram.org
ping -c 3 generativelanguage.googleapis.com
```

### Проблема 3: Нехватка памяти

```bash
# Проверка использования памяти
free -h

# Мониторинг процесса
htop
# или
top

# Увеличение swap (если RAM < 1GB)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Добавить в /etc/fstab для постоянства
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Проблема 4: ChromaDB ошибки

```bash
# Пересоздание векторной БД
cd /opt/aicompanion
rm -rf data/chroma_memory
mkdir -p data/chroma_memory

# Перезапуск сервиса
sudo systemctl restart aicompanion.service
```

---

## 📊 Мониторинг производительности

### Установка мониторинга

```bash
# Установка htop для мониторинга
sudo apt install htop

# Просмотр ресурсов
htop
```

### Проверка использования дисков

```bash
# Размер БД
du -sh /opt/aicompanion/data

# Размер логов
du -sh /opt/aicompanion/logs

# Очистка старых логов (старше 7 дней)
find /opt/aicompanion/logs -name "*.log" -mtime +7 -delete
```

---

## ✅ Чек-лист успешного развёртывания

- [ ] Сервер обновлён (`apt update && apt upgrade`)
- [ ] Python 3.12 установлен
- [ ] Проект склонирован в `/opt/aicompanion`
- [ ] Virtual environment создан и активирован
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] Конфигурация заполнена (`config/config.json`)
- [ ] Gemini API ключ валиден
- [ ] Telegram Bot токен валиден
- [ ] Telegram User ID добавлен в `allowed_users`
- [ ] Приложение запускается вручную (`python main.py`)
- [ ] Systemd service создан и активирован
- [ ] Сервис запускается автоматически (`systemctl status`)
- [ ] Резервное копирование настроено (cron)
- [ ] Файрвол настроен (UFW)
- [ ] Логи пишутся корректно

---

## 🎯 Быстрая команда для copy-paste

```bash
# Полный скрипт установки (выполнить последовательно)

# 1. Обновление и установка зависимостей
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common git curl
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 2. Подготовка директории
sudo mkdir -p /opt/aicompanion
sudo chown $USER:$USER /opt/aicompanion
cd /opt/aicompanion

# 3. Клонирование (замените URL)
git clone <your-repo-url> .

# 4. Настройка venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Конфигурация
cp config/config.example.json config/config.json
nano config/config.json  # Заполните API ключи

# 6. Тестовый запуск
python main.py  # Ctrl+C для остановки

# 7. Systemd service (замените YOUR_USERNAME)
sudo tee /etc/systemd/system/aicompanion.service > /dev/null <<EOF
[Unit]
Description=AI Companion Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/aicompanion
Environment="PATH=/opt/aicompanion/venv/bin"
ExecStart=/opt/aicompanion/venv/bin/python /opt/aicompanion/main.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/aicompanion/logs/systemd.log
StandardError=append:/opt/aicompanion/logs/systemd_error.log
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
EOF

# 8. Активация сервиса
mkdir -p /opt/aicompanion/logs
sudo systemctl daemon-reload
sudo systemctl enable aicompanion.service
sudo systemctl start aicompanion.service
sudo systemctl status aicompanion.service

# 9. Готово! Проверка логов
tail -f /opt/aicompanion/logs/companion.log
```

---

## 🎉 Поздравляем!

Ваш AI Companion теперь работает на сервере 24/7!

**Что дальше:**
1. Напишите вашему боту в Telegram
2. Проверьте работу инициатив (придут через 2-4 часа)
3. Настройте персонажа через `characters/*.json`
4. Мониторьте логи первые дни

**Полезные команды:**

```bash
# Статус
sudo systemctl status aicompanion.service

# Перезапуск
sudo systemctl restart aicompanion.service

# Логи в реальном времени
tail -f /opt/aicompanion/logs/companion.log

# Обновление
cd /opt/aicompanion && git pull && sudo systemctl restart aicompanion.service
```

---

**📅 Обновлено:** 2025-11-12
**📝 Версия:** 1.0
**⏱️ Время развёртывания:** ~10-15 минут
