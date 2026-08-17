import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from deep_translator import GoogleTranslator

# --- HEALTH-CHECK SERVER (Render uxlab qolmasligi uchun) ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# --- BOT SOZLAMALARI VA STATISTIKA ---
ADMIN_ID = 6575497342
USERS_FILE = "users.json"

LANGUAGES = {
    "en": "🇬🇧 Ingliz",
    "ru": "🇷🇺 Rus",
    "uz": "🇺🇿 O'zbek",
    "tr": "🇹🇷 Turk",
    "de": "🇩🇪 Nemis",
    "fr": "🇫🇷 Fransuz",
    "es": "🇪🇸 Ispan",
    "ar": "🇦🇪 Arab",
    "zh-CN": "🇨🇳 Xitoy"
}

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)

def get_language_keyboard():
    keyboard = []
    keys = list(LANGUAGES.keys())
    for i in range(0, len(keys), 3):
        row = [
            InlineKeyboardButton(LANGUAGES[k], callback_data=f"lang_{k}")
            for k in keys[i:i+3]
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# --- KOMANDALAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text(
        "Salom! Men Tilchi bot'man.\n\nMenga xabar yuboring va men uni siz tanlagan tilga tarjima qilib beraman!"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(f"📊 Bot statistikasi:\n\nJami foydalanuvchilar soni: {len(users)} ta")
    else:
        await update.message.reply_text("Sizda bu komandadan foydalanish huquqi yo'q.")

# --- MATNNI QAYTA ISHLASH ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    context.user_data['pending_text'] = update.message.text
    await update.message.reply_text(
        "Qaysi tilga tarjima qilmoqchisiz? Tilni tanlang:",
        reply_markup=get_language_keyboard()
    )

# --- TUGMALAR BAZASI VA TARJIMA ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "reselect_lang":
        text_to_translate = context.user_data.get('pending_text')
        if not text_to_translate:
            await query.edit_message_text("Matn topilmadi. Iltimos, yangi matn yuboring.")
            return
        await query.edit_message_text(
            f"Asl matn:\n{text_to_translate}\n\nQaysi tilga tarjima qilmoqchisiz?",
            reply_markup=get_language_keyboard()
        )
        return

    target_lang = query.data.replace("lang_", "")
    text_to_translate = context.user_data.get('pending_text')

    if not text_to_translate:
        await query.edit_message_text("Matn topilmadi. Iltimos, matnni qayta yuboring.")
        return

    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text_to_translate)
        lang_name = LANGUAGES.get(target_lang, target_lang)
        
        reselect_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Boshqa tilga tarjima qilish", callback_data="reselect_lang")]
        ])
        
        await query.edit_message_text(
            f"Asl matn:\n{text_to_translate}\n\n"
            f"Tarjima ({lang_name}):\n{translated}",
            reply_markup=reselect_keyboard
        )
    except Exception:
        await query.edit_message_text("Tarjima qilishda xatolik yuz berdi.")

# --- BOTNI ISHGA TUSHIRISH ---
def main():
    TOKEN = "8969508702:AAG1bUWvj-TnmdL_tMC_wb8iP6Iu7jfePZA"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Tilchi bot ishga tushdi!")
    app.run_polling()

if __name__ == '__main__':
    main()
