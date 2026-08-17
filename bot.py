import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

# --- RENDER PORT HEALTH-CHECK SERVER ---
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

# --- STATISTIKA VA ADMIN SOZLAMALARI ---
ADMIN_ID = 6575497342
USERS_FILE = "users.json"

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

# --- BOT KOMANDALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    await update.message.reply_text(
        "Salom! Men TilQuestBot'man. Menga istalgan matningizni yuboring, men uni tarjima qilib beraman!"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(f"📊 **Bot statistikasi:**\n\nJami foydalanuvchilar soni: **{len(users)}** ta")
    else:
        await update.message.reply_text("Sizda bu komandadan foydalanish huquqi yo'q.")

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    text = update.message.text
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        await update.message.reply_text(translated)
    except Exception:
        await update.message.reply_text("Tarjima qilishda xatolik yuz berdi.")

# --- BOTNI ISHGA TUSHIRISH ---
def main():
    TOKEN = "8969508702:AAG1bUWvj-TnmdL_tMC_wb8iP6Iu7jfePZA"  # <--- Shu qo'shtirnoq ichiga o'zingizning haqiqiy tokeningizni yozing

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))

    print("Tilchi bot ishga tushdi!")
    app.run_polling()

if __name__ == '__main__':
    main()
