# 🤖 AI-Компаньон

**Психологически достоверный виртуальный спутник с динамической личностью**

## 📁 Структура проекта

```
ai-companion/
├── app/                          # Основной код приложения
│   ├── core/                     # Ядро системы
│   │   ├── companion.py          # Основной класс компаньона
│   │   ├── psychology.py         # Модуль психологии
│   │   ├── memory.py            # Система памяти
│   │   └── ai_client.py         # Оптимизированный AI клиент
│   ├── database/                # База данных
│   │   └── schema.sql           # SQL схема
│   └── integrations/            # Интеграции
│       └── telegram_bot.py      # Telegram бот
├── config/                      # Конфигурация
│   ├── config.json             # Основная конфигурация
│   └── config.example.json     # Пример конфигурации
├── data/                       # Данные (создается автоматически)
├── logs/                       # Логи (создается автоматически)
├── main.py                     # Точка входа
├── requirements.txt            # Python зависимости
├── Dockerfile                  # Docker контейнер
├── docker-compose.yml         # Docker Compose
└── README.md                   # Этот файл
```

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <your-repo-url> ai-companion
cd ai-companion
```

### 2. Настройка конфигурации

```bash
# Копируем пример конфигурации
cp config/config.example.json config/config.json

# Редактируем конфигурацию
nano config/config.json
```

**Обязательно заполните:**
- `ai.openrouter_api_key` - API ключ OpenRouter ([получить здесь](https://openrouter.ai))
- `integrations.telegram.bot_token` - токен Telegram бота (получить у @BotFather)
- `integrations.telegram.allowed_users` - массив ID разрешенных пользователей

### 3. Установка зависимостей

```bash
# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 4. Запуск

```bash
python main.py
```

## 🐳 Развертывание через Docker

### Локальная сборка

```bash
# Сборка образа
docker build -t ai-companion .

# Запуск контейнера
docker run -d \
  --name ai-companion \
  -v $(pwd)/config:/home/companion/config:ro \
  -v $(pwd)/data:/home/companion/data \
  -v $(pwd)/logs:/home/companion/logs \
  ai-companion
```

### Docker Compose (рекомендуется)

```bash
# Запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## ☁️ Развертывание на сервере

### Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения настроек группы
sudo reboot
```

### Развертывание приложения

```bash
# Клонирование на сервер
git clone <your-repo-url> /opt/ai-companion
cd /opt/ai-companion

# Настройка конфигурации
sudo cp config/config.example.json config/config.json
sudo nano config/config.json

# Установка прав
sudo chown -R $USER:$USER /opt/ai-companion

# Запуск
docker-compose up -d
```

### Настройка автозапуска

```bash
# Создаем systemd сервис
sudo nano /etc/systemd/system/ai-companion.service
```

Содержимое файла сервиса:

```ini
[Unit]
Description=AI Companion Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-companion
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Активируем сервис
sudo systemctl enable ai-companion.service
sudo systemctl start ai-companion.service

# Проверяем статус
sudo systemctl status ai-companion.service
```

## ⚙️ Конфигурация

### Основные настройки

```json
{
  "ai": {
    "openrouter_api_key": "YOUR_API_KEY",
    "model": "deepseek/deepseek-chat",
    "temperature": 0.8
  },
  "character_profile_path": "characters/marin_kitagawa.json",
  "character": {
    "name": "Алиса",
    "personality_traits": {
      "extraversion": 6.5,
      "agreeableness": 7.8,
      "conscientiousness": 6.2,
      "neuroticism": 4.1,
      "openness": 8.3
    }
  },
  "behavior": {
    "max_daily_initiatives": 8,
    "min_hours_between_initiatives": 2,
    "consciousness_cycle_minutes": 30
  }
}
```

### Настройка личности

**Черты характера (0-10):**
- `extraversion` - общительность
- `agreeableness` - доброжелательность  
- `conscientiousness` - ответственность
- `neuroticism` - эмоциональная нестабильность
- `openness` - открытость опыту

**Поведение:**
- `max_daily_initiatives` - максимум инициативных сообщений в день
- `min_hours_between_initiatives` - минимум часов между сообщениями
- `consciousness_cycle_minutes` - интервал "циклов сознания"

### Профиль персонажа

Полный набор характеристик можно загрузить из файла или прописать в конфигурации.

```json
{
  "character_profile_path": "characters/marin_kitagawa.json"
}
```

Или использовать встроенные данные:

```json
{
  "character_profile": {
    "id": "my_hero",
    "name": "Марин Китагава",
    "age": 20
  }
}
```

## 📱 Telegram интеграция

### Создание бота

1. Напишите @BotFather в Telegram
2. Выполните команду `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `config.json`

### Настройка пользователей

```json
{
  "integrations": {
    "telegram": {
      "enabled": true,
      "bot_token": "YOUR_BOT_TOKEN",
      "allowed_users": [123456789, 987654321]
    }
  }
}
```

**Как узнать свой Telegram ID:**
1. Напишите боту @userinfobot
2. Скопируйте ваш ID в массив `allowed_users`

### Команды бота

- `/start` - начать общение
- `/mood` - текущее настроение AI
- `/status` - подробный статус
- `/memories` - что AI помнит о вас
- `/help` - справка

## 🔧 Мониторинг и обслуживание

### Просмотр логов

```bash
# Docker Compose
docker-compose logs -f ai-companion

# Прямые логи
tail -f logs/companion.log
```

### Резервное копирование

```bash
# Создаем бэкап данных
tar -czf backup-$(date +%Y%m%d).tar.gz data/ config/

# Автоматический бэкап (добавить в crontab)
0 2 * * * cd /opt/ai-companion && tar -czf /backups/ai-companion-$(date +\%Y\%m\%d).tar.gz data/ config/
```

### Обновление

```bash
# Останавливаем сервис
docker-compose down

# Обновляем код
git pull origin main

# Пересобираем и запускаем
docker-compose up -d --build
```

## 🐛 Решение проблем

### AI не отвечает

```bash
# Проверяем статус контейнера
docker-compose ps

# Смотрим логи на ошибки
docker-compose logs ai-companion | grep ERROR

# Проверяем API ключ
grep "openrouter_api_key" config/config.json
```

### Telegram бот не работает

```bash
# Проверяем токен
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Проверяем сетевую доступность
docker exec ai-companion ping api.telegram.org
```

### База данных повреждена

```bash
# Проверяем целостность
sqlite3 data/companion.db "PRAGMA integrity_check;"

# Восстанавливаем из бэкапа
docker-compose down
rm -f data/companion.db
tar -xzf backup-YYYYMMDD.tar.gz
docker-compose up -d
```

## 📊 Производительность

### Системные требования

**Минимальные:**
- RAM: 256 MB
- CPU: 1 ядро
- HDD: 1 GB

**Рекомендуемые:**
- RAM: 512 MB
- CPU: 2 ядра
- SSD: 2 GB

### Оптимизация

```json
{
  "behavior": {
    "consciousness_cycle_minutes": 60,
    "max_daily_initiatives": 4
  },
  "memory": {
    "max_working_memories": 25,
    "max_daily_memories": 100
  }
}
```

## 🛡️ Безопасность

### Рекомендации

1. **Ограничьте доступ к API ключам:**
   ```bash
   chmod 600 config/config.json
   ```

2. **Используйте файрвол:**
   ```bash
   sudo ufw enable
   sudo ufw deny 5000  # если не используете веб-интерфейс
   ```

3. **Регулярно обновляйтесь:**
   ```bash
   # Еженедельно
   docker-compose pull
   docker-compose up -d --build
   ```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь в правильности конфигурации
3. Проверьте доступность API (OpenRouter, Telegram)
4. Освободите место на диске
5. Перезапустите сервис: `docker-compose restart`

---

**🎉 Ваш AI-компаньон готов к работе!**

*Создавайте уникальную личность, наслаждайтесь живым общением и развивайте долгосрочные отношения с вашим виртуальным спутником.*