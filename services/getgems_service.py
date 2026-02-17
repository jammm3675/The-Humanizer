# -*- coding: utf-8 -*-
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from config.settings import config

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.getgems.io/graphql"
REST_URL = "https://api.getgems.io"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class GetgemsService:
    def __init__(self):
        self.api_key = config.GETGEMS_API_KEY
        self.collection_address = config.TON_COLLECTION_ADDRESS
        if not self.api_key:
            logger.error("GETGEMS_API_KEY not found in environment variables")
        if not self.collection_address:
            logger.error("TON_COLLECTION_ADDRESS not found in environment variables")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def _make_graphql_request(self, query: str, variables: dict = None):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            response = await client.post(GRAPHQL_URL, json=payload)

            if response.status_code != 200:
                logger.error(f"Getgems GraphQL Error: {response.status_code} - {response.text}")
                response.raise_for_status()

            result = response.json()
            if "errors" in result:
                logger.error(f"Getgems GraphQL Errors: {result['errors']}")

            return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def _make_rest_request(self, endpoint: str, params: dict = None):
        headers = {
            "x-api-key": self.api_key,
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
        """Получает детальную статистику коллекции через Getgems REST API."""
        if not self.api_key or not self.collection_address:
            return {"error": "Config missing (API Key or Address)"}

        try:
            endpoint = f"/public-api/v1/collections/{self.collection_address}/stats"
            data = await self._make_rest_request(endpoint)

            if not data:
                logger.warning(f"Getgems returned empty stats for {self.collection_address}")
                return {"error": "Пустой ответ от Getgems API"}

            # Извлекаем данные из REST ответа
            stats = data.get("data", data) if isinstance(data, dict) else {}

            floor_price_nano = stats.get("floorPrice") or stats.get("floor_price")
            volume_nano = stats.get("volume") or stats.get("total_volume")
            items_count = stats.get("itemsCount") or stats.get("items_count") or 0
            owner_count = stats.get("ownerCount") or stats.get("owner_count") or 0

            report = {
                "name": "NOTAPES",
                "floor_price": f"{float(floor_price_nano) / 1e9:.2f} TON" if floor_price_nano else "0.00 TON",
                "total_volume": f"{float(volume_nano) / 1e9:.2f} TON" if volume_nano else "0.00 TON",
                "holders": owner_count,
                "total_items": items_count
            }

            return report

        except Exception as e:
            logger.error(f"Error fetching Getgems data: {e}")
            return {"error": f"Сигнал Getgems потерян... ({str(e)})"}
    async def get_wallet_nfts(self, address: str):
        """Получает NFT конкретного кошелька, отфильтрованных по collection_address."""
        if not self.api_key or not self.collection_address:
            return {"error": "Config missing"}

        try:
            # Endpoint для получения NFT кошелька
            endpoint = f"/nft/user/{address}/items"
            params = {"collectionAddress": self.collection_address}
            data = await self._make_rest_request(endpoint, params=params)

            # data может быть списком или содержать поле items
            items = data if isinstance(data, list) else data.get("items", [])

            if not items:
                return {"message": f"На кошельке {address[:6]}... пусто. Ни одной обезьяны.", "count": 0}

            # Возвращаем список имен (metadata -> name)
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
            return {"error": f"Не смог просканировать Getgems. ({str(e)})"}

getgems_service = GetgemsService()
