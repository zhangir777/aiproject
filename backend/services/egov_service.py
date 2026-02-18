"""
Клиент для data.egov.kz Open Data API
"""
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

EGOV_BASE_URL = "https://data.egov.kz/api/v4"

HEADERS = {
    "User-Agent": "EnbekAI Research Bot/1.0 (student project for alem.ai battle)",
    "Accept": "application/json",
}


class EgovService:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def get_datasets(self, keywords: list[str] = None) -> list[dict]:
        """Получить список доступных датасетов."""
        try:
            # Поиск по ключевым словам через мета-API
            url = f"{EGOV_BASE_URL}/dataset/v1"
            params = {"source": json.dumps({"size": 100})}
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("hits", {}).get("hits", [])
        except Exception as e:
            logger.error(f"Ошибка получения датасетов: {e}")
        return []

    async def get_dataset_mapping(self, dataset_name: str) -> dict:
        """Получить структуру (маппинг) датасета."""
        try:
            url = f"{EGOV_BASE_URL}/mapping/{dataset_name}"
            response = await self.client.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Ошибка маппинга {dataset_name}: {e}")
        return {}

    async def get_dataset_data(
        self,
        dataset_name: str,
        size: int = 100,
        from_: int = 0,
        query: dict = None,
    ) -> list[dict]:
        """Получить данные из датасета."""
        try:
            source = {"size": size, "from": from_}
            if query:
                source["query"] = query

            url = f"{EGOV_BASE_URL}/{dataset_name}/v1"
            params = {"source": json.dumps(source)}
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                return [h.get("_source", {}) for h in hits]
        except Exception as e:
            logger.error(f"Ошибка данных {dataset_name}: {e}")
        return []

    async def search_education_data(self) -> list[dict]:
        """Получить данные об образовании."""
        education_datasets = [
            "universities",
            "colleges",
            "graduates",
            "education_statistics",
        ]
        results = []
        for ds in education_datasets:
            data = await self.get_dataset_data(ds, size=200)
            if data:
                logger.info(f"Получено {len(data)} записей из {ds}")
                results.extend(data)
        return results

    async def get_employment_data(self) -> list[dict]:
        """Получить данные о занятости."""
        datasets = ["employment", "labour_market", "unemployment"]
        results = []
        for ds in datasets:
            data = await self.get_dataset_data(ds, size=200)
            if data:
                results.extend(data)
        return results

    async def discover_relevant_datasets(self) -> list[dict]:
        """Найти релевантные датасеты по ключевым словам."""
        relevant = []
        keywords = ["труд", "занятость", "образование", "рынок", "вакансии"]

        try:
            # Попробуем получить медицинские организации как пример
            medorg = await self.get_dataset_data("medorg", size=10)
            if medorg:
                relevant.append({"name": "medorg", "count": len(medorg), "sample": medorg[0]})
        except Exception:
            pass

        return relevant


_egov_service: Optional[EgovService] = None


def get_egov_service() -> EgovService:
    global _egov_service
    if _egov_service is None:
        _egov_service = EgovService()
    return _egov_service
