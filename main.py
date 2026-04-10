import asyncio
import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from database import init_db, ensure_5_slots
from config import settings
from web_dashboard import app as web_app
from handlers.user import router as user_router
from handlers.admin import router as admin_router

# --- BOT SETUP ---
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def start_bot():
    """Logic to start the Telegram Bot polling."""
    await init_db()
    await ensure_5_slots()
    
    # Inject bot into dashboard state for web interaction
    web_app.state.bot = bot
    
    dp.include_router(admin_router)
    dp.include_router(user_router)

    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🚀 Telegram Bot starting...")
    await dp.start_polling(bot)

# --- WEB & BOT RUNNER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the bot in the background when the web server starts
    bot_task = asyncio.create_task(start_bot())
    yield
    # Cleanup
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

# Wrap the existing web_app with lifespan
web_app.router.lifespan_context = lifespan

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Run the unified server
    logging.info(f"🌐 Dashboard available at http://localhost:{settings.PORT}")
    uvicorn.run(web_app, host="0.0.0.0", port=settings.PORT)
