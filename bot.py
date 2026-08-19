import os
import logging
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Telegram Bot Token va Port
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Web Server (UptimeRobot va Render salomatligini ushlab turish uchun)
async def handle_health_check(request):
    return web.Response(text="Bot is live and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}!\n\n"
        "Botga xush kelibsiz! Rasmdagi matnlarni ajratish (OCR) yoki tarjima qilish uchun rasmni yuboring."
    )

# Asosiy ishga tushirish funksiyasi
async def post_init(application: Application):
    await start_web_server()

def main():
    if not TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi!")
        return

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Handlers (Komanda va xabarlarni tutib olish)
    app.add_handler(CommandHandler("start", start))
    
    # Botni ishga tushirish
    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
