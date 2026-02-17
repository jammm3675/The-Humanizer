# -*- coding: utf-8 -*-
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from config.settings import config

logger = logging.getLogger(__name__)

REST_URL = "https://api.getgems.io"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
COLLECTION_ADDRESS = "EQDwLDJcRXegHyvvRHXouGrUODuF0eagnWzLvUMUSTw8tv3Y"

class GetgemsService:
    def __init__(self):
        self.api_key = config.GETGEMS_API_KEY
        if not self.api_key:
            logger.error("GETGEMS_API_KEY not found in environment variables")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def _make_rest_request(self, endpoint: str, params: dict = None):
        headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "User-Agent": USER_AGENT
        }
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            url = f"{REST_URL}{endpoint}"
            response = await client.get(url, params=params)

            if response.status_code == 429:
                logger.warning("Getgems API Rate Limit (429). Waiting...")
                await asyncio.sleep(2)
                response.raise_for_status()

            if response.status_code != 200:
                logger.error(f"Getgems API Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            return response.json()

    async def get_collection_full_stats(self):
        """Получает детальную статистику коллекции через Getgems Public API v1."""
        if not self.api_key:
            return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

        try:
            endpoint = "/public-api/v1/collection-stats"
            params = {"address": COLLECTION_ADDRESS}
            data = await self._make_rest_request(endpoint, params=params)

            if not data:
                logger.warning(f"Getgems returned empty stats for {COLLECTION_ADDRESS}")
                return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

            # Getgems возвращает JSON. Извлекаем floorPrice, volume, itemsCount.
            floor_price_nano = data.get("floorPrice")
            volume_nano = data.get("volume")
            items_count = data.get("itemsCount") or 0

            report = {
                "name": "NOTAPES",
                "floor_price": f"{float(floor_price_nano) / 1_000_000_000:.2f} TON" if floor_price_nano is not None else "0.00 TON",
                "total_volume": f"{float(volume_nano) / 1_000_000_000:.2f} TON" if volume_nano is not None else "0.00 TON",
                "total_items": items_count
            }

            return report

        except Exception as e:
            logger.error(f"Error fetching Getgems data: {e}")
            return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

    async def get_wallet_nfts(self, address: str):
        """Получает NFT конкретного кошелька, отфильтрованных по COLLECTION_ADDRESS."""
        if not self.api_key:
            return {"error": "Config missing"}

        try:
            # Endpoint для получения NFT кошелька
            endpoint = f"/nft/user/{address}/items"
            params = {"collectionAddress": COLLECTION_ADDRESS}
            data = await self._make_rest_request(endpoint, params=params)

            items = data if isinstance(data, list) else data.get("items", [])

            if not items:
                return {"message": f"На кошельке {address[:6]}... пусто. Ни одной обезьяны.", "count": 0}

            names = []
            for item in items:
                metadata = item.get("metadata", {})
                name = metadata.get("name", "Unknown NFT")
                names.append(name)

            return {
                "owner": address,
                "total": len(items),
                "assets": names
            }
        except Exception as e:
            logger.error(f"Getgems Wallet API Error: {e}")
            return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

getgems_service = GetgemsService()
