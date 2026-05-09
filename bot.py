import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import TOKEN
from handlers.start import router as start_router
from handlers.replenish import router as replenish_router
from handlers.smm import router as smm_router
from handlers.admin import router as admin_router
from utils import init_db, load_service_prices

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_HOST = "https://donat-smm.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def handle_webhook(request: web.Request):
    update_data = await request.json()
    update = Update(**update_data)
    await dp.feed_update(bot, update)
    return web.Response(text="ok")


async def health(request: web.Request):
    return web.Response(text="ok")


async def on_startup(app):
    # FIX: Avval DB, keyin narxlarni yuklash, keyin webhook
    init_db()

    # DB dan saqlangan narxlarni SERVICES ga yuklash
    # Shuning uchun restart bo'lganda narxlar 0 ga qaytmaydi
    from handlers.smm import SERVICES
    saved_prices = load_service_prices()
    for key, price in saved_prices.items():
        if key in SERVICES:
            SERVICES[key]["price"] = price
    logger.info(f"Loaded {len(saved_prices)} saved prices from DB")

    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set: {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


async def main():
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(smm_router)
    dp.include_router(replenish_router)

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.router.add_get("/", health)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()

    logger.info(f"Server started on port {WEBAPP_PORT}")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
    
