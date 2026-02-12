import os
import httpx
import logging

# Настройка логирования для Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подтягиваем данные из Environment Variables
API_KEY = os.getenv("TON_API_KEY")
COLLECTION_ADDRESS = os.getenv("TON_COLLECTION_ADDRESS")
BASE_URL = "https://tonapi.io/v2"

async def get_collection_full_stats():
    """Получает детальную статистику коллекции через TonAPI."""
    if not API_KEY:
        return {"error": "API Key not found in environment variables"}

    headers = {"Authorization": f"Bearer {API_KEY}"}

    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        try:
            # 1. Запрос основной статистики коллекции
            col_res = await client.get(f"{BASE_URL}/nft/collections/{COLLECTION_ADDRESS}")
            col_res.raise_for_status()
            col_data = col_res.json()

            # 2. Запрос истории транзакций (последние 5)
            history_res = await client.get(f"{BASE_URL}/nft/collections/{COLLECTION_ADDRESS}/history?limit=5")
            history_data = history_res.json()

            stats = col_data.get('stats', {})

            report = {
                "name": col_data.get("metadata", {}).get("name", "NOTAPES"),
                "floor_price": stats.get("floor_price_ton", "0"),
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
                            "buyer": p['buyer']['address'][:6] + "..." # Маскируем адрес
                        })

            return report

        except Exception as e:
            logger.error(f"Error fetching TON data: {e}")
            return {"error": "Блокчейн-сигнал потерян в Acid Pixel..."}

async def get_wallet_nfts(address: str):
    """Проверяет наличие NFT NOTAPES на конкретном кошельке."""
    if not API_KEY: return {"error": "No API Key"}

    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(headers=headers, timeout=10.0) as client:
        try:
            # Запрос NFT пользователя с фильтром по твоей коллекции
            url = f"{BASE_URL}/accounts/{address}/nfts?collection={COLLECTION_ADDRESS}&limit=50"
            res = await client.get(url)
            res.raise_for_status()
            data = res.json()

            nft_items = data.get("nft_items", [])
            if not nft_items:
                return f"На кошельке {address[:6]}... пусто. Ни одной обезьяны."

            names = [n.get("metadata", {}).get("name", "Unknown Ape") for n in nft_items]
            return {
                "owner": address,
                "total": len(nft_items),
                "assets": names
            }
        except Exception as e:
            logger.error(f"Wallet API Error: {e}")
            return {"error": "Не смог просканировать блокчейн."}
