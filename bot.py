from io import BytesIO
import logging
import os
from deep_translator import GoogleTranslator
from PIL import Image
import pytesseract
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Tokenni muhit o'zgaruvchisidan olish
TOKEN = os.getenv("BOT_TOKEN")


# /start buyrug'i uchun handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xush kelibsiz! Menga matnli rasm yoki istalgan matn yuboring, "
        "men uni o'zbek tiliga tarjima qilib beraman. 🚀"
    )


# Oddiy matn xabarlarini tarjima qilish
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        translated = GoogleTranslator(source="auto", target="uz").translate(
            text
        )
        await update.message.reply_text(f"🌐 Tarjimasi (O'zbekcha):\n{translated}")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Tarjimada xatolik yuz berdi: {str(e)}"
        )


# Rasmlarni (OCR) o'qib tarjima qilish
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        image = Image.open(BytesIO(photo_bytes))
        extracted_text = pytesseract.image_to_string(
            image, lang="eng+rus"
        ).strip()

        if not extracted_text:
            await update.message.reply_text(
                "❌ Rasmdan hech qanday matn aniqlanmadi."
            )
            return

        translated = GoogleTranslator(source="auto", target="uz").translate(
            extracted_text
        )

        response_text = (
            f"📝 Aniqlangan matn:\n`{extracted_text}`\n\n"
            f"🌐 Tarjimasi (O'zbekcha):\n{translated}"
        )
        await update.message.reply_text(response_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {str(e)}")


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

    app = Application.builder().token(TOKEN).build()

    # Handlerlarni ro'yxatdan o'tkazish
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
