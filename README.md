# Morpher API

Локальный REST API сервис для склонения слов русского языка по падежам.  
Полностью локальная альтернатива [morpher.me](https://morpher.me), работающая без доступа в интернет.

**Стек:** Python 3.11 · FastAPI · PyMorphy3 · Uvicorn · Docker

---

## Способ 1: Локальный запуск (venv)

Подходит для разработки и отладки.

```bash
# 1. Создать виртуальное окружение
python -m venv .venv

# 2. Активировать окружение
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить сервис
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Флаг `--reload` включает горячую перезагрузку при изменении кода.

---

## Способ 2: Запуск через Docker Compose

Подходит для продакшена и воспроизводимой среды.

```bash
# Собрать образ и запустить контейнер в фоне
docker compose up --build -d

# Остановить сервис
docker compose down
```

---

## Использование API

После запуска сервис доступен на `http://localhost:8000`.

### Swagger UI (интерактивная документация)

```
http://localhost:8000/docs
```

### Проверка состояния сервиса

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### Склонение слова

```bash
curl -X POST http://localhost:8000/api/v1/inflect \
     -H "Content-Type: application/json" \
     -d '{"word": "стол", "case": "gent"}'
```

```json
{
  "original": "стол",
  "inflected": "стола",
  "case": "gent",
  "case_description": "Родительный (кого? чего?)"
}
```

### Доступные падежи

| Тег    | Падеж                       |
|--------|-----------------------------|
| `nomn` | Именительный (кто? что?)    |
| `gent` | Родительный (кого? чего?)   |
| `datv` | Дательный (кому? чему?)     |
| `accs` | Винительный (кого? что?)    |
| `ablt` | Творительный (кем? чем?)    |
| `loct` | Предложный (о ком? о чём?)  |

---

## Структура проекта

```
morpher/
├── main.py              # FastAPI приложение
├── requirements.txt     # Зависимости Python
├── Dockerfile           # Образ Docker
├── docker-compose.yml   # Конфигурация Docker Compose
└── README.md            # Документация
```
