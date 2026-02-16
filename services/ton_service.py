import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from config.settings import config

logger = logging.getLogger(__name__)

BASE_URL = "https://tonapi.io/v2"

class TONService:
    def __init__(self):
        self.api_key = config.TON_API_KEY
        self.collection_address = config.TON_COLLECTION_ADDRESS
        if not self.api_key:
            logger.error("TON_API_KEY not found in environment variables")
        if not self.collection_address:
            logger.error("TON_COLLECTION_ADDRESS not found in environment variables")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True
    )
    async def _make_request(self, endpoint: str, params: dict = None):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
            response = await client.get(f"{BASE_URL}{endpoint}", params=params)
            if response.status_code != 200:
                logger.error(f"TON API Error: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    async def get_collection_full_stats(self):
        """Получает детальную статистику коллекции через TonAPI."""
        if not self.api_key or not self.collection_address:
            return {"error": "Config missing (API Key or Address)"}

        try:
            # 1. Запрос основной статистики коллекции
            col_data = await self._make_request(f"/nft/collections/{self.collection_address}")

            # 2. Запрос истории транзакций (последние 5)
            history_data = await self._make_request(f"/nft/collections/{self.collection_address}/history", params={"limit": 5})

            stats = col_data.get('stats', {})

            report = {
                "name": col_data.get("metadata", {}).get("name", "NOTAPES"),
                "floor_price": f"{float(stats.get('floor_price_ton', 0)) / 1e9:.2f} TON" if stats.get('floor_price_ton') else "0 TON",
                "holders": stats.get("owners_count", 0),
                "total_items": col_data.get("next_item_index", 0),
                "sales_history": []
            }

            # Парсим только продажи (NftPurchase)
            for event in history_data.get("events", []):
                for action in event.get("actions", []):
                    if action['type'] == 'NftPurchase':
                        p = action['nft_purchase']
                        report["sales_history"].append({
                            "price": f"{float(p['amount']) / 1e9:.2f} TON",
                            "buyer": p['buyer']['address'][:6] + "..."
                        })

            return report

        except Exception as e:
            logger.error(f"Error fetching TON data: {e}")
            return {"error": f"Блокчейн-сигнал потерян в Acid Pixel... ({str(e)})"}

    async def get_wallet_nfts(self, address: str):
        """Проверяет наличие NFT NOTAPES на конкретном кошельке."""
        if not self.api_key or not self.collection_address:
            return {"error": "Config missing"}

        try:
            # Запрос NFT пользователя с фильтром по твоей коллекции
            endpoint = f"/accounts/{address}/nfts"
            params = {"collection": self.collection_address, "limit": 50}
            data = await self._make_request(endpoint, params=params)

            nft_items = data.get("nft_items", [])
            if not nft_items:
                return {"message": f"На кошельке {address[:6]}... пусто. Ни одной обезьяны.", "count": 0}

            names = [n.get("metadata", {}).get("name", "Unknown Ape") for n in nft_items]
            return {
                "owner": address,
                "total": len(nft_items),
                "assets": names
            }
        except Exception as e:
            logger.error(f"Wallet API Error: {e}")
            return {"error": f"Не смог просканировать блокчейн. ({str(e)})"}

ton_service = TONService()
