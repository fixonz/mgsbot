import asyncio
import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from database import init_db, ensure_5_slots, log_activity, DB_PATH
from config import settings
from web_dashboard import app as web_app
from handlers.user import router as user_router
from handlers.admin import router as admin_router
import aiosqlite
import os
import time

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

# --- ACTIVITY MIDDLEWARE ---
_BLACKLIST_PREFIXES = (
    'adm_', 'admin_', 'silent_', 'silent',
    '/admin', '/silent', '/check',
    '/pending', '/all', '/info', '/setdropwallet', '/specialdrop', '/link',
)

class ActivityMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        result = await handler(event, data)
        try:
            user = None
            activity_text = None
            if isinstance(event, Message):
                user = event.from_user
                if user.id in settings.ADMIN_IDS: return result
                text = event.text or ''
                if any(text.startswith(p) for p in _BLACKLIST_PREFIXES): return result
                activity_text = f"Mesaj: {text[:60]}" if text else "[Media]"
            elif isinstance(event, CallbackQuery):
                user = event.from_user
                if user.id in settings.ADMIN_IDS: return result
                cb = event.data or ''
                if any(cb.startswith(p) for p in _BLACKLIST_PREFIXES): return result
                activity_text = await _resolve_callback_label(cb)
            
            if user and activity_text:
                asyncio.create_task(_log_and_cache_user(user, activity_text))
        except Exception as e:
            logging.debug(f"ActivityMiddleware error: {e}")
        return result

async def _resolve_callback_label(cb: str) -> str:
    if not cb: return "Buton: [Fără date]"
    if cb.startswith('shop_cat_'):
        try:
            cat_id = cb.split('_')[2]
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT name FROM categories WHERE id = ?", (int(cat_id),)) as cur:
                    row = await cur.fetchone()
                    if row: return f"🛍 Categorie: {row[0]}"
        except: pass
    if cb.startswith('shop_item_'):
        try:
            item_id = cb.split('_')[2]
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT name FROM items WHERE id = ?", (int(item_id),)) as cur:
                    row = await cur.fetchone()
                    if row: return f"📦 Produs: {row[0]}"
        except: pass
    
    labels = {
        'menu_shop': "🛍 Deschide Magazin",
        'menu_profile': "👤 Profil",
        'menu_support': "💬 Suport",
        'menu_main': "🏠 Meniu Principal",
        'menu_start': "🏠 Meniu Principal",
        'buy_item_': "🛒 Start Achiziție",
        'verify_pay_': "✅ Verifică Plată",
        'cancel_order_': "❌ Anulează Comandă",
        'preorder_': "⏳ Precomandă"
    }
    for k, v in labels.items():
        if cb.startswith(k): return v
    return f"Buton: {cb[:30]}"

async def _log_and_cache_user(user, activity_text: str):
    try:
        await log_activity(user.id, user.username, activity_text)
    except: pass
    # Background photo fetch
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT profile_photo FROM users WHERE telegram_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
        if row and not row[0] and _bot_ref:
            photos = await _bot_ref.get_user_profile_photos(user.id, limit=1)
            if photos.total_count > 0:
                photo_file = await _bot_ref.get_file(photos.photos[0][-1].file_id)
                os.makedirs("assets/profiles", exist_ok=True)
                save_path = f"assets/profiles/{user.id}.jpg"
                await _bot_ref.download_file(photo_file.file_path, save_path)
                async with aiosqlite.connect(DB_PATH) as db:
                    await db.execute("UPDATE users SET profile_photo = ? WHERE telegram_id = ?", (save_path, user.id))
                    await db.commit()
    except: pass

_bot_ref = None

# --- BOT SETUP ---
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def start_bot():
    """Logic to start the Telegram Bot polling."""
    global _bot_ref
    _bot_ref = bot
    await init_db()
    await ensure_5_slots()
    
    # Inject bot into dashboard state for web interaction
    web_app.state.bot = bot
    
    dp.message.middleware(ActivityMiddleware())
    dp.callback_query.middleware(ActivityMiddleware())
    
    dp.include_router(admin_router)
    dp.include_router(user_router)

    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🚀 Telegram Bot starting...")
    await dp.start_polling(bot)

# --- WEB & BOT RUNNER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the bot in the background
    bot_task = asyncio.create_task(start_bot())
    
    # --- HEARTBEAT / KEEP-ALIVE ---
    async def keep_alive_heartbeat():
        import aiohttp
        while True:
            await asyncio.sleep(300) # Every 5 minutes
            url = settings.KEEP_ALIVE_URL
            if not url: continue
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        logging.debug(f"💓 Heartbeat sent to {url}: {resp.status}")
            except Exception as e:
                logging.debug(f"💔 Heartbeat failed: {e}")

    heartbeat_task = asyncio.create_task(keep_alive_heartbeat())
    
    yield
    # Cleanup
    bot_task.cancel()
    heartbeat_task.cancel()
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
