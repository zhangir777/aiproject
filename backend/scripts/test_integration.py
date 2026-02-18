"""
Интеграционный тест: CORS + все эндпоинты, имитация браузерных запросов.
Запуск: py -X utf8 scripts/test_integration.py
"""
import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

API = "http://127.0.0.1:8000"
FRONTEND_ORIGIN_3000 = "http://localhost:3000"
FRONTEND_ORIGIN_3001 = "http://localhost:3001"

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


async def test_cors_preflight(client: httpx.AsyncClient, origin: str, path: str) -> bool:
    """Simulate browser CORS preflight (OPTIONS request)."""
    r = await client.options(
        f"{API}{path}",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    acao = r.headers.get("access-control-allow-origin", "")
    allowed = acao == origin or acao == "*"
    return allowed


async def test_cors_get(client: httpx.AsyncClient, origin: str, path: str) -> tuple[bool, int]:
    """Simulate browser cross-origin GET with Origin header."""
    r = await client.get(
        f"{API}{path}",
        headers={"Origin": origin},
    )
    acao = r.headers.get("access-control-allow-origin", "")
    cors_ok = acao == origin or acao == "*"
    return cors_ok and r.status_code == 200, r.status_code


async def run_tests():
    results = []

    async with httpx.AsyncClient(timeout=20) as client:

        # ── 1. Health check ───────────────────────────────────────
        print("\n[1] Health & Root")
        r = await client.get(f"{API}/")
        ok = r.status_code == 200 and r.json().get("status") == "running"
        results.append(ok)
        print(f"  {PASS if ok else FAIL} GET /  ->  {r.json().get('status')}")

        r = await client.get(f"{API}/health")
        ok = r.status_code == 200
        results.append(ok)
        print(f"  {PASS if ok else FAIL} GET /health  ->  {r.status_code}")

        # ── 2. CORS from port 3001 ────────────────────────────────
        print("\n[2] CORS — Origin: localhost:3001")
        for path in ["/api/dashboard/overview", "/api/vacancies/regions"]:
            cors_ok, status = await test_cors_get(client, FRONTEND_ORIGIN_3001, path)
            results.append(cors_ok)
            print(f"  {PASS if cors_ok else FAIL} GET {path}  ->  {status}, CORS={'OK' if cors_ok else 'BLOCKED'}")

        # ── 3. CORS from port 3000 ────────────────────────────────
        print("\n[3] CORS — Origin: localhost:3000")
        cors_ok, status = await test_cors_get(client, FRONTEND_ORIGIN_3000, "/api/dashboard/overview")
        results.append(cors_ok)
        print(f"  {PASS if cors_ok else FAIL} GET /api/dashboard/overview  ->  {status}, CORS={'OK' if cors_ok else 'BLOCKED'}")

        # ── 4. CORS preflight for POST (chat) ─────────────────────
        print("\n[4] CORS — Preflight POST /api/chat")
        for origin in [FRONTEND_ORIGIN_3001, FRONTEND_ORIGIN_3000]:
            ok = await test_cors_preflight(client, origin, "/api/chat")
            results.append(ok)
            print(f"  {PASS if ok else FAIL} OPTIONS /api/chat  Origin={origin}  ->  {'allowed' if ok else 'BLOCKED'}")

        # ── 5. Dashboard endpoints ────────────────────────────────
        print("\n[5] Dashboard endpoints")
        dash_endpoints = [
            ("/api/dashboard/overview", "dict"),
            ("/api/dashboard/map", "list"),
            ("/api/dashboard/top-professions?limit=5", "list"),
            ("/api/dashboard/salary-by-region", "list"),
            ("/api/dashboard/trends?months=6", "list"),
        ]
        for path, expected_type in dash_endpoints:
            r = await client.get(f"{API}{path}", headers={"Origin": FRONTEND_ORIGIN_3001})
            data = r.json()
            ok = r.status_code == 200 and (
                (expected_type == "dict" and isinstance(data, dict)) or
                (expected_type == "list" and isinstance(data, list))
            )
            results.append(ok)
            size = len(data) if isinstance(data, list) else "dict"
            print(f"  {PASS if ok else FAIL} {path}  ->  {r.status_code} ({size})")

        # ── 6. Vacancies endpoints ────────────────────────────────
        print("\n[6] Vacancies endpoints")
        vac_tests = [
            "/api/vacancies?per_page=5",
            "/api/vacancies?region=Алматы&per_page=3",
            "/api/vacancies?industry=IT&per_page=3",
            "/api/vacancies/industries",
            "/api/vacancies/regions",
            "/api/vacancies/skills",
            "/api/vacancies/skills?profession=программист",
        ]
        for path in vac_tests:
            r = await client.get(f"{API}{path}", headers={"Origin": FRONTEND_ORIGIN_3001})
            ok = r.status_code == 200
            results.append(ok)
            data = r.json()
            size = len(data) if isinstance(data, list) else f"total={data.get('total',0)}"
            print(f"  {PASS if ok else FAIL} {path[:55]}  ->  {r.status_code} ({size})")

        # ── 7. AI Chat (with Origin header) ──────────────────────
        print("\n[7] POST /api/chat")
        r = await client.post(
            f"{API}/api/chat",
            json={"message": "Привет", "history": []},
            headers={"Origin": FRONTEND_ORIGIN_3001, "Content-Type": "application/json"},
        )
        acao = r.headers.get("access-control-allow-origin", "")
        ok = r.status_code == 200 and (acao == FRONTEND_ORIGIN_3001 or acao == "*")
        results.append(ok)
        resp_len = len(r.json().get("response", "")) if r.status_code == 200 else 0
        print(f"  {PASS if ok else FAIL} POST /api/chat  ->  {r.status_code}, CORS={'OK' if acao else 'missing'}, resp={resp_len} chars")

        # ── 8. Career plan ────────────────────────────────────────
        print("\n[8] POST /api/career-plan")
        r = await client.post(
            f"{API}/api/career-plan",
            json={"specialty": "аналитик", "region": "Астана", "skills": ["Excel"], "experience_years": 2},
            headers={"Origin": FRONTEND_ORIGIN_3001, "Content-Type": "application/json"},
            timeout=30,
        )
        acao = r.headers.get("access-control-allow-origin", "")
        ok = r.status_code == 200 and (acao == FRONTEND_ORIGIN_3001 or acao == "*")
        results.append(ok)
        plan_len = len(r.json().get("plan", "")) if r.status_code == 200 else 0
        print(f"  {PASS if ok else FAIL} POST /api/career-plan  ->  {r.status_code}, plan={plan_len} chars")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 55)
    passed = sum(results)
    total = len(results)
    print(f"  Integration tests: {passed}/{total} passed")
    if passed == total:
        print("  [OK] Frontend <-> Backend integration полностью работает!")
    else:
        failed = [(i + 1) for i, ok in enumerate(results) if not ok]
        print(f"  [WARN] Проваленные тесты: {failed}")
    print("=" * 55)
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_tests())
