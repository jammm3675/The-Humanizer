from aiohttp import web
import asyncio

async def health_check(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    print("Starting server...")
    await site.start()
    print("Server started on 8080")
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
