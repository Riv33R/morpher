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

### Полное склонение слова (JSON)

```bash
curl "http://localhost:8000/api/v1/inflect?word=привет&format=json"
```

```json
{
  "original": "привет",
  "singular": {
    "gent": "привета",
    "datv": "привету",
    "accs": "привет",
    "ablt": "приветом",
    "loct": "привете"
  },
  "plural": {
    "nomn": "приветы",
    "gent": "приветов",
    "datv": "приветам",
    "accs": "приветы",
    "ablt": "приветами",
    "loct": "приветах"
  }
}
```

### Полное склонение слова (XML)

Совместимый с `morpher.me` XML-формат с кириллическими тегами падежей.

```bash
curl "http://localhost:8000/api/v1/inflect?word=привет&format=xml"
```

```xml
<xml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <И>привет</И>
  <Р>привета</Р>
  <Д>привету</Д>
  <В>привет</В>
  <Т>приветом</Т>
  <П>привете</П>
  <множественное>
    <И>приветы</И>
    <Р>приветов</Р>
    <Д>приветам</Д>
    <В>приветы</В>
    <Т>приветами</Т>
    <П>приветах</П>
  </множественное>
</xml>
```

### Склонение в конкретный падеж (JSON)

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
