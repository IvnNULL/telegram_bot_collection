# YesNo GIF Bot

Telegram-бот, который отвечает на вопросы случайным «да» или «нет» с анимированной GIF.

Бот демонстрирует:

- интеграцию с внешним API
- асинхронный HTTP клиент
- кэширование файлов
- отказоустойчивую архитектуру
- Docker деплой

## Структура проекта

```
yesno_bot/
│   .env.example
│   docker-compose.yml
│   Dockerfile
│   main.py
│   requirements.txt
│   
├───assets/
│   ├───no/
│   └───yes/
│           
├───config/
│   └───config.py
│           
├───handlers/
│   ├───other.py
│   └───user.py
│           
├───services/
│   └───services.py
│           
├───texts/
│   └───texts.py
│           
└───utils/
    └───http_client.py
```

## Запуск

### Конфигурация

Создать `.env` на основе `.env.example`

```
# Logging
LOG_LEVEL=INFO
LOG_FORMAT="[%(asctime)s] #%(levelname)-8s %(filename)s:%(lineno)d - %(name)s - %(message)s"

# Bot
BOT_TOKEN=your_token_here
```

### Локальный запуск

```commandline
pip install -r requirements.txt
python main.py
```

### Docker

```commandline
docker build -t yesno_bot .
docker run -d --env-file .env -v ./assets:/app/assets yesno_bot
```

### Docker-compose

```commandline
docker compose up -d --build yesno_bot
```

## GIF Cache

GIF-файлы сохраняются в `assets/yes` и `assets/no.`  
Папка `assets/` монтируется в образ контейнера Docker и при перезапуске файлы сохраняться.

## Архитектура

- handlers - слой Telegram интерфейса
- services - бизнес-логика
- utils - инфраструктурные компоненты (HTTP client)
- texts - централизованные UI-строки

Такой подход позволяет легко:

- тестировать код
- масштабировать проект
- выносить бота в отдельный сервис