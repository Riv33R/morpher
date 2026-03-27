"""
Локальный микросервис для склонения русских слов по падежам.
Полностью локальная альтернатива сервису morpher.me.
"""

import pymorphy3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- Инициализация анализатора ---
morph = pymorphy3.MorphAnalyzer()

# --- Допустимые теги падежей pymorphy3 ---
VALID_CASES: set[str] = {"nomn", "gent", "datv", "accs", "ablt", "loct"}

# Человекочитаемые названия падежей для документации
CASE_DESCRIPTIONS = {
    "nomn": "Именительный (кто? что?)",
    "gent": "Родительный (кого? чего?)",
    "datv": "Дательный (кому? чему?)",
    "accs": "Винительный (кого? что?)",
    "ablt": "Творительный (кем? чем?)",
    "loct": "Предложный (о ком? о чём?)",
}

# --- Pydantic-схемы ---

class InflectRequest(BaseModel):
    """Запрос на склонение слова."""

    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["стол"],
        description="Слово для склонения (на русском языке).",
    )
    case: str = Field(
        ...,
        examples=["gent"],
        description=(
            "Тег падежа в формате pymorphy3. "
            "Допустимые значения: nomn, gent, datv, accs, ablt, loct."
        ),
    )


class InflectResponse(BaseModel):
    """Ответ с просклонённым словом."""

    original: str = Field(..., description="Исходное слово из запроса.")
    inflected: str = Field(..., description="Просклонённое слово.")
    case: str = Field(..., description="Применённый тег падежа.")
    case_description: str = Field(..., description="Название падежа на русском.")


class HealthResponse(BaseModel):
    """Ответ эндпоинта проверки состояния сервиса."""

    status: str = Field(..., description="Статус сервиса.", examples=["ok"])


# --- Инициализация приложения ---

app = FastAPI(
    title="Morpher API",
    summary="Локальный сервис склонения русских слов по падежам.",
    description=(
        "REST API для морфологического анализа и склонения слов русского языка. "
        "Использует библиотеку **PyMorphy3** и работает полностью локально, "
        "не требуя подключения к интернету.\n\n"
        "### Доступные падежи\n"
        "| Тег | Падеж |\n"
        "|-----|-------|\n"
        "| `nomn` | Именительный (кто? что?) |\n"
        "| `gent` | Родительный (кого? чего?) |\n"
        "| `datv` | Дательный (кому? чему?) |\n"
        "| `accs` | Винительный (кого? что?) |\n"
        "| `ablt` | Творительный (кем? чем?) |\n"
        "| `loct` | Предложный (о ком? о чём?) |\n"
    ),
    version="1.0.0",
    contact={
        "name": "Morpher API",
    },
)


# --- Эндпоинты ---

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния сервиса",
    tags=["Monitoring"],
)
async def health_check() -> HealthResponse:
    """Возвращает статус `ok`, если сервис работает нормально."""
    return HealthResponse(status="ok")


@app.post(
    "/api/v1/inflect",
    response_model=InflectResponse,
    summary="Склонение слова по падежу",
    tags=["Morphology"],
    responses={
        400: {"description": "Невозможно просклонять слово или неверный тег падежа."}
    },
)
async def inflect_word(request: InflectRequest) -> InflectResponse:
    """
    Принимает слово и тег падежа, возвращает просклонённую форму.

    - Используется **первый (наиболее вероятный)** вариант морфологического разбора.
    - Если слово не удаётся просклонять, возвращается HTTP 400.
    """
    # Нормализуем тег падежа к нижнему регистру
    case_tag = request.case.strip().lower()

    # Проверяем корректность тега падежа
    if case_tag not in VALID_CASES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Некорректный тег падежа: '{request.case}'. "
                f"Допустимые значения: {', '.join(sorted(VALID_CASES))}."
            ),
        )

    # Морфологический анализ слова (берём первый, наиболее вероятный разбор)
    parsed = morph.parse(request.word.strip())
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail=f"Не удалось выполнить морфологический анализ слова: '{request.word}'.",
        )

    best_parse = parsed[0]

    # Попытка склонения в нужный падеж
    inflected = best_parse.inflect({case_tag})
    if inflected is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Не удалось просклонять слово '{request.word}' "
                f"в падеж '{case_tag}'. "
                "Возможно, слово является несклоняемым."
            ),
        )

    return InflectResponse(
        original=request.word,
        inflected=inflected.word,
        case=case_tag,
        case_description=CASE_DESCRIPTIONS[case_tag],
    )
