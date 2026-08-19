import io
import logging
import os
import pytesseract
from PIL import Image
from docx import Document
from deep_translator import GoogleTranslator
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Qo'llab-quvvatlanadigan 9 ta til ro'yxati
LANGUAGES = {
    "uz": "🇺🇿 O'zbek",
    "en": "🇬🇧 Ingliz",
    "ru": "🇷🇺 Rus",
    "tr": "🇹🇷 Turk",
    "de": "🇩🇪 Nemis",
    "fr": "🇫🇷 Fransuz",
    "es": "🇪🇸 Ispan",
    "zh-CN": "🇨🇳 Xitoy",
    "ar": "🇸🇦 Arab",
}


def get_language_keyboard() -> InlineKeyboardMarkup:
    """9 ta til tugmalaridan iborat chiroyli va qulay interfeys yaratadi."""
    keyboard = []
    keys = list(LANGUAGES.keys())

    # Tugmalarni 2 tadan qator qilib joylashtirish
    for i in range(0, len(keys), 2):
        row = [
            InlineKeyboardButton(LANGUAGES[keys[i]], callback_data=f"setlang_{keys[i]}")
        ]
        if i + 1 < len(keys):
            row.append(
                InlineKeyboardButton(LANGUAGES[keys[i + 1]], callback_data=f"setlang_{keys[i + 1]}")
            )
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start buyrug'i uchun javob va til tanlash interfeysi."""
    context.user_data.setdefault("target_lang", "uz")
    current_lang_name = LANGUAGES.get(context.user_data["target_lang"], "O'zbek")

    text = (
        "👋 **Assalomu alaykum! Tilchi OCR va Tarjimon botiga xush kelibsiz!**\n\n"
        "✨ **Bot imkoniyatlari:**\n"
        "• Matnlarni 9 xil tilga tez va aniq tarjima qilish\n"
        "• Rasmlardagi matnlarni o'qish (OCR) va tarjima qilish\n"
        "• `.txt` va `.docx` hujjatlarini to'liq tarjima qilish\n\n"
        f"📌 **Hozirgi tanlangan tarjima tili:** {current_lang_name}\n\n"
        "👇 **Iltimos, matn yoki hujjatni qaysi tilga tarjima qilmoqchiligingizni tanlang:**"
    )

    await update.message.reply_text(
        text,
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown"
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi tugma orqali tilni o'zgartirganda ishlaydi."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_")[1]
    context.user_data["target_lang"] = lang_code
    lang_name = LANGUAGES.get(lang_code, "Noma'lum")

    text = (
        f"✅ **Tarjima tili munosib ravishda o'zgartirildi:** {lang_name}\n\n"
        "Endi menga matn, rasm yoki `.txt` / `.docx` hujjat yuborishingiz mumkin!"
    )

    await query.edit_message_text(
        text,
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Matnli xabarlarni tarjima qilish va interfeysni ko'rsatish."""
    user_text = update.message.text
    target_lang = context.user_data.get("target_lang", "uz")

    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(user_text)
        current_lang_name = LANGUAGES.get(target_lang, "O'zbek")

        response = (
            f"🔤 **Tarjima ({current_lang_name}):**\n\n"
            f"{translated}\n\n"
            "───────────────\n"
            "🌐 **Boshqa tilga tarjima qilish uchun quyidan tilni tanlang:**"
        )

        await update.message.reply_text(
            response,
            reply_markup=get_language_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Matn tarjimasida xatolik: {e}")
        await update.message.reply_text("❌ Matnni tarjima qilishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Rasmdagi matnni ajratib olish (OCR) va tarjima qilish."""
    target_lang = context.user_data.get("target_lang", "uz")
    status_message = await update.message.reply_text("⏳ Rasm qayta ishlanmoqda va matn o'qilmoqda...")

    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        image = Image.open(io.BytesIO(photo_bytes))
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            await status_message.edit_text("⚠️ Rasmdan hech qanday matn topilmadi.")
            return

        translated = GoogleTranslator(source="auto", target=target_lang).translate(extracted_text)
        current_lang_name = LANGUAGES.get(target_lang, "O'zbek")

        response = (
            f"🔍 **Rasmdan ajratib olingan matn:**\n`{extracted_text.strip()}`\n\n"
            f"🔤 **Tarjima ({current_lang_name}):**\n{translated}\n\n"
            "───────────────\n"
            "🌐 **Boshqa tilga tarjima qilish uchun tilni tanlang:**"
        )

        await status_message.edit_text(
            response,
            reply_markup=get_language_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"OCR tarjimasida xatolik: {e}")
        await status_message.edit_text("❌ Rasmni qayta ishlashda xatolik yuz berdi.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """.txt va .docx fayllarini tarjima qilish."""
    document = update.message.document
    file_name = document.file_name.lower()
    target_lang = context.user_data.get("target_lang", "uz")

    if not (file_name.endswith(".txt") or file_name.endswith(".docx")):
        await update.message.reply_text("⚠️ Iltimos, faqat `.txt` yoki `.docx` formatidagi hujjat yuboring.")
        return

    status_message = await update.message.reply_text("⏳ Hujjat o'qilmoqda va tarjima qilinmoqda...")

    try:
        doc_file = await document.get_file()
        file_bytes = await doc_file.download_as_bytearray()

        extracted_text = ""
        if file_name.endswith(".txt"):
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
        elif file_name.endswith(".docx"):
            doc = Document(io.BytesIO(file_bytes))
            extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text])

        if not extracted_text.strip():
            await status_message.edit_text("⚠️ Hujjat ichida hech qanday matn topilmadi.")
            return

        lines = extracted_text.split("\n")
        translated_lines = []

        for line in lines:
            if line.strip():
                translated_line = GoogleTranslator(source="auto", target=target_lang).translate(line)
                translated_lines.append(translated_line)
            else:
                translated_lines.append("")

        translated_text = "\n".join(translated_lines)
        current_lang_name = LANGUAGES.get(target_lang, "O'zbek")

        result_bytes = io.BytesIO(translated_text.encode("utf-8"))
        result_bytes.name = f"translated_{document.file_name}"

        await update.message.reply_document(
            document=result_bytes,
            caption=(
                f"✅ **Hujjat tarjima qilindi!**\n"
                f"🌐 **Tarjima qilingan til:** {current_lang_name}\n\n"
                "Quyidagi tugmalar orqali tilni o'zgartirishingiz mumkin:"
            ),
            reply_markup=get_language_keyboard(),
            parse_mode="Markdown"
        )
        await status_message.delete()

    except Exception as e:
        logger.error(f"Hujjat tarjimasida xatolik: {e}")
        await status_message.edit_text("❌ Hujjatni tarjima qilishda xatolik yuz berdi.")


async def start_dummy_server() -> None:
    """Render port ogohlantirishini oldini olish uchun soxta veb-server."""
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


def main() -> None:
    """Botni ishga tushirish funksiyasi."""
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable topilmadi!")
        return

    app = Application.builder().token(token).build()

    # Soxta veb-serverni parallel ishga tushirish
    app.post_init = lambda application: start_dummy_server()

    # Handlerlar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^setlang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot muvaffaqiyatli ishga tushdi.")
    app.run_polling()


if __name__ == "__main__":
    main()
