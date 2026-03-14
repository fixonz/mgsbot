from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from utils.keyboards import main_menu
from database import add_user, DB_PATH, get_available_address, create_sale
from config import DEPOSIT_TIMEOUT_MINUTES, ADMIN_IDS
import os
from utils.tatum import check_ltc_transaction
from utils.ltc_price import get_ltc_ron_price, ron_to_ltc
import aiosqlite
import logging
import asyncio

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        "🏙 <b>Seiful Digital Premium</b>\n\n"
        "Bun venit în cel mai securizat magazin digital. "
        "Plăți LTC verificate cu livrare instantanee.\n\n"
        "🛒 <b>Alege o categorie de mai jos pentru a începe.</b>"
    )
    
    kb = main_menu()
    if message.from_user.id in ADMIN_IDS:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🛠 Panou Admin", callback_data="admin_main")])
    
    banner_path = "assets/2creier.jpg"
    if os.path.exists(banner_path):
        photo = FSInputFile(banner_path)

        await message.answer_photo(photo, caption=welcome_text, reply_markup=kb)
    else:
        await message.answer(welcome_text, reply_markup=kb)


@router.callback_query(F.data == "menu_profile")
async def cb_menu_profile(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT items.name, sales.amount_paid, sales.created_at, sales.id, items.price_ron
            FROM sales 
            JOIN items ON sales.item_id = items.id 
            WHERE sales.user_id = ? AND sales.status = 'paid'
            ORDER BY sales.created_at DESC
            LIMIT 5
        """, (callback.from_user.id,)) as cursor:
            orders = await cursor.fetchall()
            
    user = callback.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username = f" (@{user.username})" if user.username else ""
    
    text = (
        f"� <b>Profil Utilizator</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Nume:</b> {full_name}{username}\n\n"
        f"📦 <b>Istoric Comenzi (Ultimele 5):</b>\n"
    )
    
    kb_buttons = []
    if not orders:
        text += "<i>Momentan nu ai nicio comandă finalizată.</i>"
    else:
        for o in orders:
            text += f"🔹 #{o[3]} | <b>{o[0]}</b>\nPreț: {int(o[4])} RON ({o[1]} LTC) | {o[2]}\n\n"
            kb_buttons.append([InlineKeyboardButton(text=f"👁 Vezi #{o[3]} ({o[0]})", callback_data=f"view_secret_{o[3]}")])
        
    kb_buttons.append([InlineKeyboardButton(text="🔙 Înapoi", callback_data="menu_start")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    
    img_path = "assets/welcome_banner.png"
    
    if os.path.exists(img_path):
        from aiogram.types import InputMediaPhoto
        photo = FSInputFile(img_path)
        if callback.message.photo:
            try:
                await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=text), reply_markup=kb)
            except Exception:
                await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.answer_photo(photo, caption=text, reply_markup=kb)
            await callback.message.delete()
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()




@router.callback_query(F.data.startswith("view_secret_"))
async def cb_view_order_secret(callback: CallbackQuery):
    sale_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT items.name, item_images.image_url, sales.user_id, users.telegram_id
            FROM sales
            JOIN items ON sales.item_id = items.id
            JOIN item_images ON sales.image_id = item_images.id
            JOIN users ON sales.user_id = users.id
            WHERE sales.id = ? AND sales.status = 'paid'
        """, (sale_id,)) as cursor:
            data = await cursor.fetchone()
            
    if not data or data[3] != callback.from_user.id:
        await callback.answer("Comandă neautorizată sau inexistentă.", show_alert=True)
        return
        
    name, img_url, _, _ = data
    msg_text = f"📦 <b>Conținut Comandă #{sale_id}</b>\nProdus: <b>{name}</b>"
    
    if img_url.startswith("http") or len(img_url) > 40:
        await callback.bot.send_photo(callback.from_user.id, photo=img_url, caption=msg_text)
    else:
        await callback.bot.send_message(callback.from_user.id, f"{msg_text}\n\nConținut:\n<code>{img_url}</code>")
        
    await callback.answer("Ți-am retrimis mesajul cu stocul!", show_alert=True)


@router.callback_query(F.data == "menu_support")
async def cb_menu_support(callback: CallbackQuery):
    text = (
        "💬 <b>Centru de Suport</b>\n\n"
        "Ai nevoie de ajutor cu o comandă sau ai întrebări despre produse?\n\n"
        "👤 Contact Admin: @creierosuz\n"
        "🕒 Program: NON-STOP (24/7)\n\n"
        "Te rugăm să incluzi ID-ul comenzii dacă ai o problemă cu o plată."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Înapoi", callback_data="menu_start")]])
    
    img_path = "assets/support.png"
    if os.path.exists(img_path):
        from aiogram.types import InputMediaPhoto
        photo = FSInputFile(img_path)
        if callback.message.photo:
            try:
                await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=text), reply_markup=kb)
            except Exception:
                await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.answer_photo(photo, caption=text, reply_markup=kb)
            await callback.message.delete()
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()




@router.callback_query(F.data == "menu_shop")
async def cb_menu_shop(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM categories LIMIT 9") as cursor:
            cats = await cursor.fetchall()
            
    if not cats:
        await callback.message.edit_text("Momentan nu există categorii disponibile.")
        await callback.answer()
        return

    # Create 3x3 grid for categories
    kb_rows = []
    current_row = []
    for cat in cats:
        current_row.append(InlineKeyboardButton(text=cat[1], callback_data=f"shop_cat_{cat[0]}"))
        if len(current_row) == 3:
            kb_rows.append(current_row)
            current_row = []
    if current_row:
        kb_rows.append(current_row)
    
    kb_rows.append([InlineKeyboardButton(text="🔙 Înapoi", callback_data="menu_start")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    
    label = "💎 <b>Alege o Categorie:</b>"
    img_path = "assets/shop.png"
    if os.path.exists(img_path):
        from aiogram.types import InputMediaPhoto
        photo = FSInputFile(img_path)
        if callback.message.photo:
            try:
                await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=label), reply_markup=kb)
            except Exception:
                await callback.message.edit_caption(caption=label, reply_markup=kb)
        else:
            await callback.message.answer_photo(photo, caption=label, reply_markup=kb)
            await callback.message.delete()
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(label, reply_markup=kb)
        else:
            await callback.message.edit_text(label, reply_markup=kb)
    await callback.answer()



@router.callback_query(F.data == "menu_start")
async def cb_menu_start(callback: CallbackQuery):
    welcome_text = "🏙 <b>Seiful Digital Premium</b>\n\n🛒 Alege o categorie sau folosește meniul de mai jos."
    kb = main_menu()
    if callback.from_user.id in ADMIN_IDS:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🛠 Panou Admin", callback_data="admin_main")])
        
    img_path = "assets/2creier.jpg"

    if callback.message.photo and os.path.exists(img_path):
        from aiogram.types import InputMediaPhoto
        await callback.message.edit_media(
            media=InputMediaPhoto(media=FSInputFile(img_path), caption=welcome_text),
            reply_markup=kb
        )
    else:
        if os.path.exists(img_path):
            await callback.message.answer_photo(FSInputFile(img_path), caption=welcome_text, reply_markup=kb)
            await callback.message.delete()
        else:
            await callback.message.edit_text(welcome_text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("shop_cat_"))
async def cb_shop_cat(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    if len(data_parts) < 3 or not data_parts[2].isdigit():
        return # Safety skip for malformed or non-numeric IDs
    cat_id = int(data_parts[2])

    
    async with aiosqlite.connect(DB_PATH) as db:
        # Fetch category info first
        async with db.execute("SELECT name, display_image, description FROM categories WHERE id = ?", (cat_id,)) as cursor:
            cat_info = await cursor.fetchone()
            
        if not cat_info:
            await callback.answer("Categoria nu a fost găsită.", show_alert=True)
            return
            
        cat_name, cat_img, cat_desc = cat_info

        # Fetch items
        async with db.execute("""
            SELECT items.id, items.name, items.price_ron, items.price_ltc, COUNT(item_images.id) as stock
            FROM items 
            LEFT JOIN item_images ON items.id = item_images.item_id AND item_images.is_sold = 0
            WHERE items.category_id = ?
            GROUP BY items.id
            ORDER BY items.price_ron ASC
        """, (cat_id,)) as cursor:
            items = await cursor.fetchall()
            
    if not items:
        # Show description even if no items
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Înapoi la Categorii", callback_data="menu_shop")]])
        text = f"📂 Categorie: <b>{cat_name}</b>\n\n<i>{cat_desc or ''}</i>\n\n⚠️ Momentan nu există produse în această categorie."
    else:
        kb_rows = []
        for item in items:
            stock_count = item[4]
            if stock_count > 0:
                btn_text = f"{item[1]}"
                btn_style = "success"
            else:
                btn_text = f"{item[1]}"
                btn_style = "danger"
            kb_rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"shop_item_{item[0]}", style=btn_style)])

            
        kb_rows.append([InlineKeyboardButton(text="🔙 Înapoi la Categorii", callback_data="menu_shop")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
        text = f"📂 Categorie: <b>{cat_name}</b>\n\n<i>{cat_desc or ''}</i>\n\n<i>Alege pachetul dorit:</i>"

    
    if cat_img:
        from aiogram.types import InputMediaPhoto
        # Check if it's a local file or a URL
        is_local = not cat_img.startswith("http")
        photo = FSInputFile(cat_img) if is_local else cat_img

        if callback.message.photo:
            try:
                await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=text), reply_markup=kb)
            except Exception:
                # If editing fails (e.g. same media), just update caption
                await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.answer_photo(photo, caption=text, reply_markup=kb)
            await callback.message.delete()
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


import aiogram

@router.callback_query(F.data.startswith("shop_item_"))
async def cb_shop_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT items.name, items.description, items.price_ron, items.price_ltc, 
                   COUNT(item_images.id), items.display_image, categories.display_image
            FROM items 
            JOIN categories ON items.category_id = categories.id
            LEFT JOIN item_images ON items.id = item_images.item_id AND item_images.is_sold = 0
            WHERE items.id = ?
            GROUP BY items.id
        """, (item_id,)) as cursor:
            item = await cursor.fetchone()
            
    if not item:
        await callback.answer("Produsul nu a fost găsit", show_alert=True)
        return

    name, desc, p_ron, p_ltc, stock, item_img, cat_img = item
    display_img = item_img if item_img else cat_img
    
    # Live LTC price
    ltc_rate = await get_ltc_ron_price()
    live_ltc = ron_to_ltc(p_ron, ltc_rate)
    
    text = (
        f"📦 <b>{name}</b>\n\n"
        f"{desc}\n\n"
        f"💰 Preț: <b>{int(p_ron)} RON</b>\n"
        f"⚡️ Echivalent: <code>{live_ltc}</code> LTC\n"
        f"📊 Stoc disponibil: <b>{stock} buc</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if stock > 0:
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔥 Cumpără Acum", callback_data=f"buy_item_{item_id}", style="success")])
    else:
        kb.inline_keyboard.append([InlineKeyboardButton(text="⏳ Precomandă", callback_data=f"preorder_{item_id}", style="danger")])

        
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Înapoi", callback_data="nav_back_categories")])


    if display_img:
        from aiogram.types import InputMediaPhoto
        is_local = not display_img.startswith("http")
        photo = FSInputFile(display_img) if is_local else display_img

        if callback.message.photo:
            try:
                await callback.message.edit_media(media=InputMediaPhoto(media=photo, caption=text), reply_markup=kb)
            except Exception:
                await callback.message.edit_caption(caption=text, reply_markup=kb)
        else:
            await callback.message.answer_photo(photo, caption=text, reply_markup=kb)
            await callback.message.delete()
    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=kb)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "nav_back_categories")
async def cb_nav_back_categories(callback: CallbackQuery):
    await cb_menu_shop(callback)

@router.callback_query(F.data.startswith("preorder_"))
async def cb_preorder(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    user_tg_id = callback.from_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check for 24h spam
        from datetime import datetime, timedelta
        limit_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        
        async with db.execute("""
            SELECT created_at FROM preorders 
            WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?) 
            AND created_at > ?
            ORDER BY created_at DESC LIMIT 1
        """, (user_tg_id, limit_time)) as cursor:
            last_preorder = await cursor.fetchone()
            
        if last_preorder:
            await callback.answer("⏳ Poți face o singură precomandă la 24 de ore pentru a evita spam-ul. Revino mâine!", show_alert=True)
            return

        async with db.execute("SELECT name FROM items WHERE id = ?", (item_id,)) as cursor:
            item = await cursor.fetchone()
            
    if not item:
        await callback.answer("Produsul nu a fost găsit", show_alert=True)
        return
        
    item_name = item[0]
    user = callback.from_user
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "N/A"
    
    # Notify Admins
    admin_text = (
        "💎 <b>CERERE NOUĂ PRECOMANDĂ</b>\n\n"
        f"🛍 Produs: <b>{item_name}</b>\n"
        f"👤 Client: {full_name} ({username})\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"
        "<i>Dorești să onorezi această precomandă?</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Aprobă", callback_data=f"pre_yes_{user.id}_{item_id}", style="success"),
            InlineKeyboardButton(text="❌ Refuză", callback_data=f"pre_no_{user.id}_{item_id}", style="danger")
        ]
    ])
    
    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(admin_id, admin_text, reply_markup=kb)
        except:
            pass

    # Save to prevent spam
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO preorders (user_id, item_id) VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?)",
            (user_tg_id, item_id)
        )
        await db.commit()
            
    await callback.message.answer(
        "💎 <b>Precomandă Trimisă!</b>\n\n"
        "Cererea ta a fost trimisă către admin. Vei primi un mesaj imediat ce este procesată.",
        show_alert=True
    )
    await callback.answer()



@router.callback_query(F.data.startswith("buy_item_"))
async def cb_buy_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[2])
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, price_ron FROM items WHERE id = ?", (item_id,)) as cursor:
            item = await cursor.fetchone()
            
    if not item:
        await callback.answer("Produsul nu a fost găsit", show_alert=True)
        return
        
    name, p_ron = item
    
    # Live LTC conversion
    ltc_rate = await get_ltc_ron_price()
    price = ron_to_ltc(p_ron, ltc_rate)
    
    address, old_sale_to_clear = await get_available_address(DEPOSIT_TIMEOUT_MINUTES)
    
    if not address:
        await callback.answer(
            "⚠️ Canal ocupat! Așteaptă 2-5 min și încearcă din nou.", 
            show_alert=True
        )
        return

    sale_id = await create_sale(callback.from_user.id, item_id, price, address, DEPOSIT_TIMEOUT_MINUTES)
    
    # Notify Admins about PENDING sale
    for admin_id in ADMIN_IDS:
        try:
            admin_pending_msg = (
                f"📝 <b>INTENȚIE CUMPĂRARE</b>\n\n"
                f"🛍 Produs: {name}\n"
                f"💵 Sumă: <code>{price}</code> LTC (~{int(p_ron)} RON)\n"
                f"👤 Client: @{callback.from_user.username or 'N/A'} (ID: <code>{callback.from_user.id}</code>)\n"
                f"📍 Adresă: <code>{address}</code>\n"
                f"🆔 Comandă: #{sale_id}"
            )
            await callback.bot.send_message(admin_id, admin_pending_msg)
        except: pass

    price_plus_buffer = round(price + 0.0015, 4)
    text = (
        f"💳 <b>Finalizare Comandă: {name}</b>\n\n"
        f"Depune suma în LTC în {DEPOSIT_TIMEOUT_MINUTES} minute.\n\n"
        f"💰 <b>Sumă RON:</b> <code>{int(p_ron)}</code> RON\n"
        f"💰 <b>Suma MINIMĂ:</b> <code>{price}</code> LTC\n"
        f"📍 <b>Adresă LTC:</b> <code>{address}</code>\n\n"
        f"⚠️ <b>IMPORTANT:</b> Trimite suma MINIMĂ sau <b>puțin în plus</b> (Ex: <code>{price_plus_buffer}</code> LTC) pentru a asigura confirmarea automată.\n"
        f"Dacă trimiți chiar și cu 0.0001 mai puțin, plata NU va fi detectată!\n\n"
        f"📊 <i>Livrarea se face automat după 3 confirmări în rețea.</i>\n"
        f"📈 <i>Curs LTC: 1 LTC = {int(ltc_rate)} RON (actualizat la fiecare oră)</i>"
    )



    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Am Depus", callback_data=f"verify_{sale_id}")],
        [InlineKeyboardButton(text="❌ Anulare", callback_data="menu_shop")]
    ])
    
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=kb)
    else:
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("verify_"))
async def cb_verify_payment(callback: CallbackQuery):
    sale_id = int(callback.data.split("_")[1])
    # ... logic remains same ...
    label = "⏳ Verificăm blockchain-ul LTC... Acest proces durează 1-5 minute."
    if callback.message.photo:
        await callback.message.edit_caption(caption=label, reply_markup=None)
    else:
        await callback.message.edit_text(label, reply_markup=None)
    await callback.answer()

    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT items.name, sales.amount_expected, sales.address_used, sales.created_at, sales.user_id, items.id
            FROM sales 
            JOIN items ON sales.item_id = items.id 
            WHERE sales.id = ?
        """, (sale_id,)) as cursor:
            sale_data = await cursor.fetchone()
            
    if not sale_data:
        await callback.message.edit_text("Comanda nu a fost găsită.")
        return
        
    item_name, price, address, created_at, db_user_id, item_id = sale_data
    from datetime import datetime
    ts = int(datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').timestamp())

    async def update_status(text, kb=None):
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption=text, reply_markup=kb)
            else:
                await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            pass

    # Initial check
    found_tx, confs, tx_hash = await check_ltc_transaction(address, price, ts)
    
    if found_tx:
        # User requested 5, 2, 1 sequence
        waits = [300, 120, 60]
        for w in waits:
            if confs >= 3: break
            
            await update_status(f"🔄 <b>Tranzacție detectată!</b> (TX: <code>{tx_hash[:6]}...</code>)\n\nConfirmări: <code>{confs}/3</code>\n\nUrmătoarea verificare în {w//60} minute...")
            await asyncio.sleep(w)
            found_tx, new_confs, tx_hash = await check_ltc_transaction(address, price, ts)
            if new_confs != confs:
                confs = new_confs
                await callback.message.answer(f"📈 <b>Confirmări actualizate:</b> <code>{confs}/3</code>")

        # Final loop
        retries = 5
        while confs < 3 and found_tx and retries > 0:
            if retries < 5: await asyncio.sleep(60)
            found_tx, new_confs, tx_hash = await check_ltc_transaction(address, price, ts)
            if new_confs != confs:
                confs = new_confs
                await update_status(f"🔄 <b>Confirmări: {confs}/3</b>\n\nAșteptăm livrarea...")
            retries -= 1

    if found_tx and confs >= 3:
        async with aiosqlite.connect(DB_PATH) as db:
            # CHECK IF TX_HASH ALREADY USED
            async with db.execute("SELECT id FROM sales WHERE tx_hash = ?", (tx_hash,)) as cursor:
                if await cursor.fetchone():
                    await update_status("❌ Această tranzacție a fost deja procesată.")
                    return

            async with db.execute("SELECT id, image_url FROM item_images WHERE item_id = ? AND is_sold = 0 LIMIT 1", (item_id,)) as cursor:
                image_row = await cursor.fetchone()
            
            if not image_row:
                await update_status("⚠️ Stoc epuizat. Contactați @creierosuz pentru refund sau alt pachet.")
                return
            
            img_db_id, img_url = image_row
            await db.execute("UPDATE item_images SET is_sold = 1 WHERE id = ?", (img_db_id,))
            await db.execute("UPDATE sales SET status = 'paid', amount_paid = ?, image_id = ?, tx_hash = ? WHERE id = ?", (price, img_db_id, tx_hash, sale_id))
            await db.execute("UPDATE addresses SET in_use_by_sale_id = NULL, locked_until = NULL WHERE crypto_address = ?", (address,))
            await db.commit()
            
            # Final Delivery
            msg_text = f"🎉 <b>LIVRARE REUȘITĂ!</b>\n\nProdus: <b>{item_name}</b>\nSecretul tău:"
            if img_url.startswith("http") or len(img_url) > 40:
                await callback.bot.send_photo(callback.from_user.id, photo=img_url, caption=msg_text)
            else:
                await callback.bot.send_message(callback.from_user.id, f"{msg_text}\n\n<code>{img_url}</code>")
            
            await update_status(f"✅ PLATA CONFIRMATĂ!\nProdusul a fost trimis mai jos.")

            # Notify Admin
            for admin_id in ADMIN_IDS:
                try:
                    admin_msg = (
                        f"💰 <b>VÂNZARE FINALIZATĂ (ID: #{sale_id})</b>\n\n"
                        f"🛍 Produs: {item_name}\n"
                        f"💵 Sumă: <code>{price}</code> LTC\n"
                        f"👤 Client: @{callback.from_user.username or 'N/A'} (ID: <code>{callback.from_user.id}</code>)\n"
                        f"🔗 TXID: <code>{tx_hash}</code>\n\n"
                        f"✅ <b>Status: LIVRAT AUTOMAT</b>"
                    )
                    await callback.bot.send_message(admin_id, admin_msg)
                except: pass

    else:
        if found_tx:
            fail_text = f"⏳ <b>Detectat!</b>\n\nConfirmări actuale: <code>{confs}/3</code>\n\nTe rugăm să reîncerci peste 1-2 minute."
        else:
            fail_text = "❌ Plata nu a fost detectată. Asigură-te că ai trimis suma corectă."
            
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Reîmprospătează Status", callback_data=f"verify_{sale_id}")],
            [InlineKeyboardButton(text="🔙 Magazin", callback_data="menu_shop")]
        ])
        await update_status(fail_text, kb)



