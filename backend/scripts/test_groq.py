"""
Тест Groq API: подключение, кэш, rate limiter, чат, карьерный план.
Запуск: py -X utf8 scripts/test_groq.py
"""
import asyncio
import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

from database import init_db
from services.groq_service import get_groq_service, SYSTEM_PROMPT_CHAT
from services.career_service import get_career_service


def print_section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)


async def test_connection():
    """Тест 1: Базовое подключение к Groq API."""
    print_section("Тест 1: Подключение к Groq API")
    groq = get_groq_service()
    t0 = time.time()
    response, model = await groq.chat(
        messages=[{"role": "user", "content": "Скажи только 'OK' без объяснений."}],
        max_tokens=10,
        use_cache=False,
    )
    elapsed = time.time() - t0
    print(f"  Ответ: {response!r}")
    print(f"  Модель: {model}")
    print(f"  Время: {elapsed:.2f}с")
    assert response, "Пустой ответ!"
    print("  [PASS] Подключение работает")
    return True


async def test_cache():
    """Тест 2: Кэширование ответов."""
    print_section("Тест 2: Кэш AI-ответов")
    groq = get_groq_service()
    messages = [{"role": "user", "content": "Сколько регионов в Казахстане? Ответь одним числом."}]

    # Первый запрос — к API
    t0 = time.time()
    r1, m1 = await groq.chat(messages, max_tokens=20, use_cache=True)
    t1 = time.time() - t0
    print(f"  1-й запрос: {r1!r} [{t1:.2f}с] ({m1})")

    # Второй запрос — из кэша
    t0 = time.time()
    r2, m2 = await groq.chat(messages, max_tokens=20, use_cache=True)
    t2 = time.time() - t0
    print(f"  2-й запрос: {r2!r} [{t2:.4f}с] ({m2})")

    assert r1 == r2, "Ответы должны совпадать!"
    assert "cached" in m2, f"Второй запрос должен быть из кэша, получили: {m2}"
    assert t2 < 0.5, f"Кэш должен работать быстро, получили {t2:.2f}с"
    print("  [PASS] Кэш работает корректно")
    return True


async def test_chat_with_context():
    """Тест 3: Чат с контекстом рынка труда."""
    print_section("Тест 3: AI-чат с контекстом")
    groq = get_groq_service()

    context = """[DATA] Данные из базы EnbekAI:
- Профессия: разработчик
- Регион: Астана
- Вакансий найдено: 42
- Средняя зарплата: 473,713 T

Вопрос пользователя: Какие перспективы у разработчиков в Астане?"""

    t0 = time.time()
    response, model = await groq.chat(
        messages=[{"role": "user", "content": context}],
        system_prompt=SYSTEM_PROMPT_CHAT,
        max_tokens=400,
        use_cache=False,
    )
    elapsed = time.time() - t0

    print(f"  Время: {elapsed:.2f}с, Модель: {model}")
    print(f"  Длина ответа: {len(response)} символов")
    print(f"  Первые 300 символов ответа:")
    print(f"  {response[:300]}")
    print("  ...")
    assert len(response) > 50, "Ответ слишком короткий"
    print("  [PASS] Чат с контекстом работает")
    return True


async def test_career_plan():
    """Тест 4: Генерация карьерного плана."""
    print_section("Тест 4: Генерация карьерного плана")
    svc = get_career_service()

    t0 = time.time()
    plan, stats, alternatives = await svc.generate_plan(
        specialty="программист",
        region="Алматы",
        skills=["Python", "SQL", "Git"],
        experience_years=2,
    )
    elapsed = time.time() - t0

    print(f"  Время генерации: {elapsed:.2f}с")
    print(f"  Статистика: {stats['vacancy_count']} вак, avg {stats.get('avg_salary', 0):,} T")
    print(f"  Альтернатив: {len(alternatives)}")
    print(f"  Длина плана: {len(plan)} символов")
    print(f"\n  Начало плана:")
    print(f"  {plan[:400]}")
    print("  ...")
    assert len(plan) > 100, "План слишком короткий"
    print("  [PASS] Карьерный план генерируется")
    return True


async def test_rate_limiter():
    """Тест 5: Rate limiter не блокирует единичные запросы."""
    print_section("Тест 5: Rate limiter")
    groq = get_groq_service()

    # Проверяем что rate limiter не блокирует 3 быстрых запроса
    t0 = time.time()
    for i in range(3):
        await groq.rate_limiter.acquire()
        groq.rate_limiter.requests.append(time.time())
    elapsed = time.time() - t0

    queue_len = len(groq.rate_limiter.requests)
    print(f"  3 acquire за {elapsed:.3f}с, в очереди: {queue_len} запросов")
    assert elapsed < 1.0, f"Rate limiter заблокировал при малом числе запросов: {elapsed:.2f}с"
    print("  [PASS] Rate limiter не блокирует при нормальной нагрузке")
    return True


async def main():
    print("=" * 55)
    print("  EnbekAI — Тест Groq API")
    print("=" * 55)

    await init_db()

    results = {}
    tests = [
        ("connection", test_connection),
        ("cache", test_cache),
        ("chat_context", test_chat_with_context),
        ("career_plan", test_career_plan),
        ("rate_limiter", test_rate_limiter),
    ]

    for name, test_fn in tests:
        try:
            results[name] = await test_fn()
        except Exception as e:
            print(f"\n  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    print_section("Итоги")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  Результат: {passed}/{total} тестов прошли")
    if passed == total:
        print("  [OK] Groq API полностью работоспособен!")
    else:
        print("  [WARN] Некоторые тесты не прошли, проверьте логи выше")


if __name__ == "__main__":
    asyncio.run(main())
