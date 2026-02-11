import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

async def get_collection_stats(collection_address: str):
    """Получает Floor Price и статы коллекции через TonAPI."""
    api_key = os.environ.get("TONAPI_KEY")
    url = f"https://tonapi.io/v2/nfts/collections/{collection_address}"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    stats = data.get('stats', {})
                    floor = stats.get('floor_price_ton', 0) / 1e9 if stats.get('floor_price_ton') else "???"
                    return {
                        "floor": floor,
                        "items": data.get('next_item_index', 0),
                        "owners": stats.get('owner_count', 0)
                    }
    except Exception as e:
        logger.error(f"NFT Data Error: {e}")
    return None
