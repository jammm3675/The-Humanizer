# -*- coding: utf-8 -*-
import logging
import httpx
from config.settings import config

logger = logging.getLogger(__name__)

class GetgemsService:
    def __init__(self):
        self.api_key = config.GETGEMS_API_KEY
        self.collection_address = config.TON_COLLECTION_ADDRESS or "EQDwLDJcRXegHyvvRHXouGrUODuF0eagnWzLvUMUSTw8tv3Y"
        if not self.api_key:
            logger.warning("GETGEMS_API_KEY not found in environment variables")

    async def get_collection_stats(self):
        """Получает статистику коллекции через Getgems Public API v1."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        base_url = "https://api.getgems.io/public-api/v1/collection"
        addr = self.collection_address

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                r_stats = await client.get(f"{base_url}/stats/{addr}")
                r_stats.raise_for_status()
                res = r_stats.json().get("response", {})

                # floorPrice, holders, itemsCount, totalVolumeSold
                volume = res.get("totalVolumeSold")
                if isinstance(volume, (int, float)):
                    volume = round(volume, 2)

                return {
                    "floor": res.get("floorPrice"),
                    "holders": res.get("holders"),
                    "items": res.get("itemsCount"),
                    "volume": volume
                }
        except Exception as e:
            logger.error(f"Error fetching Getgems stats: {e}")
            return {"error": "Связь с Getgems прервана 🔌"}

    async def get_top_owners(self, limit: int = 5):
        """Получает топ владельцев коллекции."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        base_url = "https://api.getgems.io/public-api/v1/collection"
        addr = self.collection_address

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                url = f"{base_url}/top-owners/{addr}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json().get("response", {}).get("items", [])

                owners = []
                for item in data[:limit]:
                    owners.append({
                        "address": item.get("ownerAddress"),
                        "count": item.get("count")
                    })
                return owners
        except Exception as e:
            logger.error(f"Error fetching top owners: {e}")
            return []

    async def get_last_sales(self, limit: int = 3):
        """Получает последние продажи из истории коллекции."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        base_url = "https://api.getgems.io/public-api/v1/collection"
        addr = self.collection_address

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                url = f"{base_url}/history/{addr}"
                params = {"types": "sold"}
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json().get("response", {}).get("items", [])

                sales = []
                for item in data[:limit]:
                    sales.append({
                        "price": item.get("price"),
                        "nft_name": item.get("nft", {}).get("name", "NFT"),
                        "timestamp": item.get("timestamp")
                    })
                return sales
        except Exception as e:
            logger.error(f"Error fetching last sales: {e}")
            return []

    async def check_user_nft(self, user_address: str):
        """Проверяет наличие NFT коллекции у пользователя."""
        headers = {"accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        base_url = "https://api.getgems.io/public-api/v1/collection"
        addr = self.collection_address

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
                url = f"{base_url}/user-search/{addr}/{user_address}"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json().get("response", {}).get("items", [])

                return {
                    "is_holder": len(data) > 0,
                    "count": len(data),
                    "items": [item.get("name") for item in data[:5]]
                }
        except Exception as e:
            logger.error(f"Error checking user NFT: {e}")
            return {"is_holder": False, "error": str(e)}

    async def get_wallet_nfts(self, address: str):
        """Legacy compatibility method."""
        return await self.check_user_nft(address)

getgems_service = GetgemsService()
