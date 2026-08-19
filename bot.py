import os
import logging
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Web Server
async def handle_health_check(request):
    return web.Response(text="Bot is live and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}!\n\n"
        "Botga xush kelibsiz! Rasmdagi matnlarni ajratish (OCR) va tarjima qilish uchun rasmni yuboring."
    )

# Rasmga ishlov berish
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ Rasm qabul qilindi. Matn o'qilmoqda...")
    photo_path = "temp_image.jpg"
    
    try:
        # Rasm faylini olish (Photo yoki Document bo'lishidan qat'i nazar)
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            file_id = update.message.document.file_id
        else:
            await status_msg.edit_text("Iltimos, faqat rasm formatidagi fayl yuboring.")
            return

        photo_file = await context.bot.get_file(file_id)
        await photo_file.download_to_drive(photo_path)

        # PyTesseract OCR
        image = Image.open(photo_path)
        extracted_text = pytesseract.image_to_string(image, lang='eng+rus') # eng va rus tillari

        if os.path.exists(photo_path):
            os.remove(photo_path)

        if not extracted_text.strip():
            await status_msg.edit_text("❌ Rasmda hech qanday matn topilmadi.")
            return

        # Tarjima
        translated_text = GoogleTranslator(source='auto', target='uz').translate(extracted_text.strip())

        response_message = (
            f"📝 **Aniqlangan matn:**\n`{extracted_text.strip()}`\n\n"
            f"🌐 **Tarjimasi (O'zbekcha):**\n`{translated_text}`"
        )
        await status_msg.edit_text(response_message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        if os.path.exists(photo_path):
            os.remove(photo_path)
        await status_msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")

async def post_init(application: Application):
    await start_web_server()

def main():
    if not TOKEN:
        print("XATOLIK: BOT_TOKEN topilmadi!")
        return

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    # Har qanday rasm yoki rasm-faylni ushlab olish handler'i
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
    
    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
