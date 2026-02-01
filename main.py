import logging
import requests
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = '7611956551:AAEUjO70_8fB_CoyD0Ff3D4oBclL7vU-6vY'
ADMIN_ID = 7859798194  # Sizning ID raqamingiz o'rnatildi

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- BAZA (XOTIRA) ---
db = sqlite3.connect("bot_settings.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
db.commit()

def get_setting(key, default):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else default

def set_setting(key, value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    db.commit()

# --- BYPASS TIZIMI ---
async def get_bypass(url):
    api_list = [
        f"https://api.deltaexecutor.dev/api/v1/bypass?url={url}",
        f"https://api.bypass.city/bypass?url={url}",
        f"https://fluxus-reborn-api.vercel.app/api/bypass?url={url}"
    ]
    for api in api_list:
        try:
            res = await asyncio.to_thread(requests.get, api, timeout=15)
            if res.status_code == 200:
                data = res.json()
                return data.get("result") or data.get("key") or data.get("data")
        except: continue
    return None

# --- ADMIN BUYRUQLARI ---
@dp.message_handler(commands=['setchannel'])
async def set_channel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        new_channel = message.get_args()
        if new_channel and new_channel.startswith("@"):
            set_setting("channel", new_channel)
            await message.reply(f"✅ Канал изменен на: {new_channel}")
        else:
            await message.reply("❌ Напишите: `/setchannel @uz_bypass`", parse_mode="Markdown")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    channel = get_setting("channel", "@sizning_kanalingiz")
    try:
        member = await bot.get_chat_member(channel, message.from_user.id)
        if member.status == 'left': raise Exception()
    except:
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Подписаться", url=f"https://t.me/{channel[1:]}"))
        kb.add(InlineKeyboardButton("🔄 Проверить", callback_data="check"))
        return await message.answer(f"⚠️ **Чтобы пользоваться ботом, подпишитесь на канал: {channel}**", reply_markup=kb, parse_mode="Markdown")
    
    await message.answer("👋 **Привет! Отправь ссылку для Bypass.**")

@dp.callback_query_handler(lambda c: c.data == 'check')
async def check_cb(c: types.CallbackQuery):
    channel = get_setting("channel", "@sizning_kanalingiz")
    try:
        member = await bot.get_chat_member(channel, c.from_user.id)
        if member.status != 'left':
            await c.message.edit_text("✅ **Спасибо! Теперь отправьте ссылку.**")
        else:
            await c.answer("❌ Вы не подписались!", show_alert=True)
    except:
        await c.answer("⚠️ Бот должен быть админом в канале!", show_alert=True)

@dp.message_handler()
async def main(message: types.Message):
    channel = get_setting("channel", "@sizning_kanalingiz")
    try:
        m = await bot.get_chat_member(channel, message.from_user.id)
        if m.status == 'left': return await start(message)
    except: pass

    if message.text.startswith("http"):
        wait = await message.reply("⏳ **Bypassing...**")
        res = await get_bypass(message.text)
        await wait.edit_text(f"✅ **Result:** `{res}`" if res else "❌ Error bypass.", parse_mode="Markdown")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
