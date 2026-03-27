"""
Локальный микросервис для склонения русских слов по падежам.
Полностью локальная альтернатива сервису morpher.me.
"""

import json

import pymorphy3
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class UTF8JSONResponse(JSONResponse):
    """JSONResponse с ensure_ascii=False — кириллица передаётся как есть, не экранируется."""

    # Явно объявляем charset=utf-8, иначе клиенты (PowerShell, curl и др.)
    # могут интерпретировать тело как latin-1 по умолчанию для application/json
    media_type = "application/json; charset=utf-8"

    def render(self, content: object) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,   # <-- ключевое: не экранировать не-ASCII символы
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

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


class AllFormsResponse(BaseModel):
    """Полная таблица склонений слова (ед. и мн. число)."""

    original: str = Field(..., description="Исходное слово (Именительный, ед.ч.).")
    singular: dict[str, str | None] = Field(
        ...,
        description="Формы единственного числа. Ключ — тег падежа pymorphy3.",
        examples=[{"gent": "стола", "datv": "столу", "accs": "стол", "ablt": "столом", "loct": "столе"}],
    )
    plural: dict[str, str | None] = Field(
        ...,
        description="Формы множественного числа. Ключ — тег падежа pymorphy3.",
        examples=[{"nomn": "столы", "gent": "столов", "datv": "столам", "accs": "столы", "ablt": "столами", "loct": "столах"}],
    )


# --- Инициализация приложения ---

app = FastAPI(
    title="Morpher API",
    summary="Локальный сервис склонения русских слов по падежам.",
    default_response_class=UTF8JSONResponse,  # UTF-8 JSON для всех эндпоинтов
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
    version="1.1.0",
    contact={
        "name": "Morpher API",
    },
)


# --- Вспомогательные функции ---

# Соответствие тегов pymorphy3 → русскоязычным XML-тегам (как у morpher.me)
_CASE_TO_XML_TAG: dict[str, str] = {
    # "nomn": "И",
    "gent": "Р",
    "datv": "Д",
    "accs": "В",
    "ablt": "Т",
    "loct": "П",
}

# Порядок падежей в XML: единственное число (без Именительного — он является входным словом)
_SINGULAR_CASE_ORDER: list[str] = ["gent", "datv", "accs", "ablt", "loct"]
# Множественное число — все шесть падежей
_PLURAL_CASE_ORDER: list[str] = ["nomn", "gent", "datv", "accs", "ablt", "loct"]


def _inflect_phrase(phrase: str, grammemes: set[str]) -> str:
    """
    Склоняет каждое слово в фразе в заданный падеж (и/или число).
    Токены, которые нельзя просклонять (числа, несклоняемые слова), оставляются без изменений.
    Сохраняет регистр первой буквы исходного токена (заглавная буква).
    """
    result_tokens: list[str] = []
    for token in phrase.split():
        parsed = morph.parse(token)
        if not parsed:
            # Не удалось проанализировать — оставляем как есть
            result_tokens.append(token)
            continue

        best = parsed[0]
        inflected = best.inflect(grammemes)

        if inflected is None:
            # Несклоняемое слово — оставляем без изменений
            result_tokens.append(token)
        else:
            word = inflected.word
            # Сохраняем заглавный регистр, если он был в исходном токене
            if token[0].isupper():
                word = word[0].upper() + word[1:]
            result_tokens.append(word)

    return " ".join(result_tokens)


def _compute_all_forms(phrase: str) -> AllFormsResponse:
    """Вычисляет все падежные формы фразы (ед. и мн. число)."""
    # Проверяем, что вход не пустой
    phrase = phrase.strip()
    if not phrase:
        raise HTTPException(status_code=400, detail="Передана пустая строка.")

    # Единственное число: все падежи кроме Именительного (он — исходная фраза)
    singular: dict[str, str | None] = {
        case: _inflect_phrase(phrase, {case}) for case in _SINGULAR_CASE_ORDER
    }

    # Множественное число: все шесть падежей
    plural: dict[str, str | None] = {
        case: _inflect_phrase(phrase, {"plur", case}) for case in _PLURAL_CASE_ORDER
    }

    return AllFormsResponse(original=phrase, singular=singular, plural=plural)


def _build_xml(data: AllFormsResponse) -> bytes:
    """Строит XML в формате morpher.me и возвращает байты в UTF-8."""
    import xml.etree.ElementTree as ET

    root = ET.Element("xml")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xmlns:xsd", "http://www.w3.org/2001/XMLSchema")

    # Именительный ед.ч. — исходное слово (первый тег в выдаче morpher.me)
    # ET.SubElement(root, "И").text = data.original

    # Остальные падежи единственного числа
    for case in _SINGULAR_CASE_ORDER:
        value = data.singular.get(case)
        if value is not None:
            ET.SubElement(root, _CASE_TO_XML_TAG[case]).text = value

    # Множественное число — вложенный блок <множественное>
    plural_elem = ET.SubElement(root, "множественное")
    for case in _PLURAL_CASE_ORDER:
        value = data.plural.get(case)
        if value is not None:
            ET.SubElement(plural_elem, _CASE_TO_XML_TAG[case]).text = value

    # Явно кодируем в UTF-8, чтобы клиенты корректно интерпретировали кириллицу
    return ET.tostring(root, encoding="unicode").encode("utf-8")


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


@app.get(
    "/api/v1/inflect",
    summary="Полное склонение слова (все падежи, JSON или XML)",
    tags=["Morphology"],
    responses={
        200: {
            "content": {
                "application/json": {},
                "application/xml": {"example": "<xml>...</xml>"},
            }
        },
        400: {"description": "Невозможно просклонять слово."},
    },
)
async def inflect_all(
    word: str = Query(..., description="Слово на русском языке для полного склонения."),
    format: str = Query("json", description="Формат ответа: json или xml."),
) -> object:
    """
    Возвращает **все падежные формы** слова (единственное и множественное число).

    - **word** — слово на русском языке.
    - **format** — формат ответа: `json` (по умолчанию) или `xml`.

    XML-формат совместим с morpher.me и содержит кириллические теги падежей:  
    `<И>` `<Р>` `<Д>` `<В>` `<Т>` `<П>` и блок `<множественное>`.
    """
    fmt = format.strip().lower()
    if fmt not in {"json", "xml"}:
        raise HTTPException(
            status_code=400,
            detail="Параметр 'format' должен быть 'json' или 'xml'.",
        )

    data = _compute_all_forms(word)

    if fmt == "xml":
        xml_body = _build_xml(data)
        return Response(content=xml_body, media_type="application/xml; charset=utf-8")

    return data


@app.post(
    "/api/v1/inflect",
    response_model=InflectResponse,
    summary="Склонение слова по одному падежу",
    tags=["Morphology"],
    responses={
        400: {"description": "Невозможно просклонять слово или неверный тег падежа."}
    },
)
async def inflect_word(request: InflectRequest) -> InflectResponse:
    """
    Принимает фразу (одно или несколько слов) и тег падежа, возвращает просклонённую форму.

    - Каждое слово в фразе склоняется независимо.
    - Используется **первый (наиболее вероятный)** вариант морфологического разбора.
    - Несклоняемые слова остаются без изменений.
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

    # Склоняем каждое слово фразы независимо
    inflected_phrase = _inflect_phrase(request.word.strip(), {case_tag})

    return InflectResponse(
        original=request.word,
        inflected=inflected_phrase,
        case=case_tag,
        case_description=CASE_DESCRIPTIONS[case_tag],
    )
