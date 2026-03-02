# -*- coding: utf-8 -*-
import logging
import httpx
from config.settings import config

logger = logging.getLogger(__name__)

class GetgemsService:
    def __init__(self):
        self.api_key = config.GETGEMS_API_KEY
        self.collection_address = "EQDwLDJcRXegHyvvRHXouGrUODuF0eagnWzLvUMUSTw8tv3Y"
        if not self.api_key:
            logger.error("GETGEMS_API_KEY not found in environment variables")

    async def get_collection_stats(self):
        """Получает статистику коллекции через Getgems Public API v1."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        base_url = "https://api.getgems.io/public-api/v1/collection"
        addr = self.collection_address

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                # Согласно запросу используем оба эндпоинта
                await client.get(f"{base_url}/basic-info/{addr}")
                r_stats = await client.get(f"{base_url}/stats/{addr}")
                r_stats.raise_for_status()
                res = r_stats.json().get("response", {})

                # По спецификации от пользователя: floorPrice, holders, itemsCount
                return {
                    "floor": res.get("floorPrice"),
                    "holders": res.get("holders"),
                    "items": res.get("itemsCount")
                }
        except Exception as e:
            logger.error(f"Error fetching Getgems stats: {e}")
            return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

    async def get_collection_full_stats(self):
        # Обертка для совместимости, если где-то еще вызывается старое имя
        return await self.get_collection_stats()

    async def get_wallet_nfts(self, address: str):
        """Метод для получения NFT кошелька (оставлен как есть для совместимости)."""
        if not self.api_key:
            return {"error": "Config missing"}

        # Для упрощения и по просьбе пользователя, пока не переписываем под новый URL
        # Если сломается - будет закомментировано или возвращать ошибку
        try:
            headers = {
                "X-API-KEY": self.api_key,
                "Accept": "application/json"
            }
            async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
                url = f"https://api.getgems.io/nft/user/{address}/items"
                params = {"collectionAddress": self.collection_address}
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                items = data if isinstance(data, list) else data.get("items", [])

                if not items:
                    return {"message": f"На кошельке {address[:6]}... пусто. Ни одной обезьяны.", "count": 0}

                names = [item.get("metadata", {}).get("name", "Unknown NFT") for item in items]
                return {
                    "owner": address,
                    "total": len(items),
                    "assets": names
                }
        except Exception as e:
            logger.error(f"Getgems Wallet API Error: {e}")
            return {"error": "Связь с Getgems прервана, сижу без данных 🔌"}

getgems_service = GetgemsService()
