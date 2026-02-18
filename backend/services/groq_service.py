"""
Groq API Service — обёртка с rate limiting, retry и кэшированием.
"""
import asyncio
import hashlib
import json
import time
import logging
from typing import Optional

import aiosqlite
from groq import Groq, RateLimitError, APIError

from config import (
    GROQ_API_KEY,
    GROQ_MODEL_MAIN,
    GROQ_MODEL_FAST,
    GROQ_MAX_REQUESTS_PER_MINUTE,
    GROQ_RETRY_AFTER_SECONDS,
    GROQ_MAX_RETRIES,
    DATABASE_URL,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_CHAT = """Ты — EnbekAI, AI-аналитик рынка труда Казахстана.
Твоя задача — давать точные, полезные рекомендации на основе реальных данных о вакансиях и рынке труда.

Правила:
- ВСЕГДА опирайся на предоставленные данные из базы. Не выдумывай цифры.
- Указывай конкретные числа: зарплаты, количество вакансий, процент конкуренции.
- Давай практичные, действенные рекомендации.
- Если данных недостаточно — честно скажи об этом.
- Отвечай на языке вопроса (казахский или русский).
- Будь лаконичным, но информативным. Не лей воду.
- Форматируй ответ с использованием markdown (заголовки, списки, жирный текст).

Ты НЕ должен:
- Давать медицинские, юридические или финансовые советы
- Обсуждать темы не связанные с рынком труда и карьерой
- Выдумывать данные которых нет в контексте"""

SYSTEM_PROMPT_CAREER = """Ты — карьерный AI-консультант EnbekAI. На основе данных о рынке труда Казахстана, составь персональный карьерный план.

Входные данные: специальность, регион, текущие навыки пользователя.
Данные из базы: статистика вакансий, зарплат, конкуренции.

Структура ответа:
1. **Текущая ситуация** — средняя зарплата, количество вакансий, уровень конкуренции
2. **Сильные стороны** — какие навыки пользователя востребованы
3. **Что доучить** — конкретные навыки для роста зарплаты (с примерами курсов)
4. **Альтернативные профессии** — смежные направления с лучшими перспективами
5. **План на 6 месяцев** — пошаговый план действий"""


class RateLimiter:
    """Простой rate limiter: не более N запросов в минуту."""
    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.requests: list[float] = []

    async def acquire(self):
        now = time.time()
        # Убираем запросы старше 60 секунд
        self.requests = [t for t in self.requests if now - t < 60]
        if len(self.requests) >= self.max_per_minute:
            wait_time = 60 - (now - self.requests[0])
            if wait_time > 0:
                logger.info(f"Rate limit: ожидание {wait_time:.1f}с")
                await asyncio.sleep(wait_time)
        self.requests.append(time.time())


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.rate_limiter = RateLimiter(GROQ_MAX_REQUESTS_PER_MINUTE)

    def _hash_request(self, messages: list, model: str) -> str:
        """SHA256 хэш для кэширования."""
        key = json.dumps({"messages": messages, "model": model}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(key.encode()).hexdigest()

    async def _get_cached(self, query_hash: str) -> Optional[str]:
        """Проверить кэш AI-ответов."""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute(
                    "SELECT response_text FROM ai_cache WHERE query_hash = ?",
                    (query_hash,)
                )
                row = await cursor.fetchone()
                if row:
                    logger.info(f"Кэш HIT: {query_hash[:8]}...")
                    return row[0]
        except Exception as e:
            logger.warning(f"Ошибка чтения кэша: {e}")
        return None

    async def _save_cache(self, query_hash: str, query_text: str, response: str, model: str, tokens: int):
        """Сохранить ответ в кэш."""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO ai_cache
                       (query_hash, query_text, response_text, model_used, tokens_used)
                       VALUES (?, ?, ?, ?, ?)""",
                    (query_hash, query_text[:500], response, model, tokens)
                )
                await db.commit()
        except Exception as e:
            logger.warning(f"Ошибка сохранения кэша: {e}")

    async def _call_groq(self, messages: list, model: str, max_tokens: int, temperature: float) -> tuple[str, int]:
        """Базовый вызов Groq API с retry при 429."""
        await self.rate_limiter.acquire()

        for attempt in range(GROQ_MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                )
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else 0
                logger.info(f"Groq {model}: {tokens} токенов")
                return content, tokens

            except RateLimitError as e:
                wait = GROQ_RETRY_AFTER_SECONDS
                logger.warning(f"Groq 429 (попытка {attempt+1}/{GROQ_MAX_RETRIES}), ждём {wait}с")
                if attempt < GROQ_MAX_RETRIES - 1:
                    await asyncio.sleep(wait)
                else:
                    raise

            except APIError as e:
                logger.error(f"Groq API ошибка: {e}")
                # Fallback на быструю модель если основная недоступна
                if model == GROQ_MODEL_MAIN and attempt == 0:
                    logger.info(f"Fallback на {GROQ_MODEL_FAST}")
                    model = GROQ_MODEL_FAST
                else:
                    raise

        raise RuntimeError("Groq API: превышено количество попыток")

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str = SYSTEM_PROMPT_CHAT,
        model: str = GROQ_MODEL_MAIN,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        use_cache: bool = True,
    ) -> tuple[str, str]:
        """
        Отправить сообщение в AI чат.
        Возвращает (ответ, модель_которая_использовалась).
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        query_hash = self._hash_request(full_messages, model)

        if use_cache:
            cached = await self._get_cached(query_hash)
            if cached:
                return cached, f"{model} (cached)"

        response, tokens = await self._call_groq(full_messages, model, max_tokens, temperature)

        if use_cache:
            user_text = messages[-1].get("content", "") if messages else ""
            await self._save_cache(query_hash, user_text, response, model, tokens)

        return response, model

    async def classify(
        self,
        text: str,
        instruction: str,
        model: str = GROQ_MODEL_FAST,
        max_tokens: int = 512,
    ) -> str:
        """
        Быстрая классификация/извлечение данных (для обработки вакансий).
        """
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": text},
        ]
        query_hash = self._hash_request(messages, model)
        cached = await self._get_cached(query_hash)
        if cached:
            return cached

        response, tokens = await self._call_groq(messages, model, max_tokens, temperature=0.1)
        await self._save_cache(query_hash, text[:200], response, model, tokens)
        return response


# Синглтон
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
