import os
import json
import threading
from io import BytesIO
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytesseract
from PIL import Image

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from deep_translator import GoogleTranslator
from docx import Document


# =========================================================
# HEALTH CHECK SERVER
# =========================================================

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        return


def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        SimpleHTTPRequestHandler
    )

    server.serve_forever()


threading.Thread(
    target=run_health_check_server,
    daemon=True
).start()


# =========================================================
# SOZLAMALAR
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 6575497342
USERS_FILE = "users.json"


# =========================================================
# TILLAR
# =========================================================

names = {
    "uz": "🇺🇿 O‘zbekcha",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ko": "🇰🇷 한국어",
    "tr": "🇹🇷 Türkçe",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "ar": "🇸🇦 العربية",
    "zh-CN": "🇨🇳 中文"
}


# =========================================================
# FOYDALANUVCHILAR
# =========================================================

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(users), f)


# =========================================================
# TIL TUGMALARI
# =========================================================

def get_language_keyboard():
    keyboard = []
    keys = list(names.keys())

    for i in range(0, len(keys), 3):
        row = [
            InlineKeyboardButton(
                names[k],
                callback_data=k
            )
            for k in keys[i:i + 3]
        ]
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


LANGUAGES_KEYBOARD = get_language_keyboard()


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    save_user(user_id)

    await update.message.reply_text(
        "👋 Salom! Men **Tilchi bot**'man. 🤖\n\n"
        "✨ Menga istalgan matnni, "
        "**.txt / .docx** faylni yoki "
        "📸 **rasmni** yuboring.\n\n"
        "🌍 Men rasm ichidagi matnni ham "
        "aniqlab, siz tanlagan tilga tarjima qilaman!",
        reply_markup=LANGUAGES_KEYBOARD,
        parse_mode="Markdown"
    )


# =========================================================
# HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "ℹ️ **Yordam markazi:**\n\n"
        "💬 Matn yuboring.\n"
        "📄 `.txt` yoki `.docx` fayl yuboring.\n"
        "📸 Rasm yuboring.\n\n"
        "🔘 Keyin kerakli tilni tanlang.\n\n"
        "🤖 Rasm yuborsangiz, men rasm ichidagi "
        "matnni avtomatik aniqlayman va tarjima qilaman.",
        parse_mode="Markdown"
    )


# =========================================================
# STATISTIKA
# =========================================================

async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(
            f"📊 **Bot statistikasi:**\n\n"
            f"👥 Jami foydalanuvchilar: "
            f"**{len(users)}** ta",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "⚠️ Sizda bu komandadan foydalanish huquqi yo‘q."
        )


# =========================================================
# ODDIY MATN
# =========================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    save_user(user_id)

    text = update.message.text
    if not text:
        return

    context.user_data["text"] = text
    context.user_data["content_type"] = "text"

    await update.message.reply_text(
        "🌐 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )


# =========================================================
# RASM OCR
# =========================================================

async def photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    save_user(user_id)

    await update.message.reply_text(
        "📸 Rasm qabul qilindi.\n"
        "🔍 Rasm ichidagi matn aniqlanmoqda..."
    )

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_data = await file.download_as_bytearray()
        image = Image.open(BytesIO(image_data))

        extracted_text = pytesseract.image_to_string(
            image,
            lang="eng+rus"
        )
        extracted_text = extracted_text.strip()

        if not extracted_text:
            await update.message.reply_text(
                "❌ Rasm ichidan matn topilmadi.\n\n"
                "📸 Iltimos, matni aniqroq ko‘rinadigan "
                "rasm yuboring."
            )
            return

        if len(extracted_text) > 3000:
            extracted_text = (
                extracted_text[:3000]
                + "\n\n..."
            )

        context.user_data["text"] = extracted_text
        context.user_data["content_type"] = "image"

        await update.message.reply_text(
            "✅ Rasm ichidagi matn aniqlandi!\n\n"
            "📝 **Topilgan matn:**\n\n"
            f"{extracted_text[:3500]}\n\n"
            "🌐 Endi qaysi tilga tarjima qilay?",
            reply_markup=LANGUAGES_KEYBOARD,
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Rasm OCR xatosi:", e)
        await update.message.reply_text(
            "❌ Rasmni o‘qishda xatolik yuz berdi.\n\n"
            "📸 Rasmni qaytadan yuborib ko‘ring."
        )


# =========================================================
# TXT + DOCX
# =========================================================

async def document_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    save_user(user_id)

    doc_file = update.message.document
    file_name = doc_file.file_name or "file"
    file_name_lower = file_name.lower()

    if not (
        file_name_lower.endswith(".txt")
        or file_name_lower.endswith(".docx")
    ):
        await update.message.reply_text(
            "❌ Kechirasiz, hozircha faqat "
            "**.txt** va **.docx** fayllarini "
            "qabul qilaman.",
            parse_mode="Markdown"
        )
        return

    try:
        file = await context.bot.get_file(doc_file.file_id)
        os.makedirs("downloads", exist_ok=True)
        local_path = os.path.join("downloads", file_name)

        await file.download_to_drive(local_path)
        extracted_text = ""

        if file_name_lower.endswith(".txt"):
            with open(
                local_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:
                extracted_text = f.read()

        elif file_name_lower.endswith(".docx"):
            doc = Document(local_path)
            extracted_text = "\n".join(
                p.text for p in doc.paragraphs if p.text.strip()
            )

        if os.path.exists(local_path):
            os.remove(local_path)

        if not extracted_text.strip():
            await update.message.reply_text(
                "❌ Fayl ichida tarjima qilish uchun matn topilmadi."
            )
            return

        if len(extracted_text) > 3000:
            extracted_text = (
                extracted_text[:3000]
                + "\n\n..."
            )

        context.user_data["text"] = extracted_text
        context.user_data["content_type"] = "document"

        await update.message.reply_text(
            f"📄 **Fayl qabul qilindi:** `{file_name}`\n\n"
            "🌐 Qaysi tilga tarjima qilay?",
            reply_markup=LANGUAGES_KEYBOARD,
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Fayl xatosi:", e)
        await update.message.reply_text(
            "❌ Faylni qayta ishlashda xatolik yuz berdi."
        )


# =========================================================
# YANA TARJIMA
# =========================================================

async def again(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    context.user_data.pop("text", None)
    context.user_data.pop("content_type", None)

    await query.edit_message_text(
        "✍️ Yangi so‘z, matn, hujjat yoki 📸 rasm yuboring."
    )


# =========================================================
# TILNI ALMASHTIRISH
# =========================================================

async def change_language(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🌍 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )


# =========================================================
# TARJIMA
# =========================================================

async def translate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    text = context.user_data.get("text")
    content_type = context.user_data.get("content_type", "text")

    if not text:
        await query.edit_message_text(
            "❌ Matn topilmadi.\n\n"
            "Iltimos, yangi matn, fayl yoki rasm yuboring."
        )
        return

    target_code = query.data

    if target_code not in names:
        await query.edit_message_text("❌ Noma'lum til tanlandi.")
        return

    try:
        translated = GoogleTranslator(
            source="auto",
            target=target_code
        ).translate(text)

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Yana tarjima qilish",
                    callback_data="again"
                )
            ],
            [
                InlineKeyboardButton(
                    "🌍 Tilni almashtirish",
                    callback_data="change_language"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if content_type == "image":
            source_title = "📸 Rasm ichidagi matn"
        elif content_type == "document":
            source_title = "📄 Fayldagi matn"
        else:
            source_title = "📝 Asl matn"

        if target_code == "ar":
            rtl = "\u200F"
            message_text = (
                f"{rtl}🇸🇦 {names[target_code]} tiliga tarjima:\n\n"
                f"{rtl}{source_title}:\n"
                f"{rtl}{text[:500]}\n\n"
                f"{rtl}✅ **Tarjima:**\n"
                f"{rtl}{translated}"
            )
        else:
            message_text = (
                f"🌐 **{names[target_code]} tiliga tarjima:**\n\n"
                f"{source_title}:\n"
                f"{text[:500]}\n\n"
                f"✅ **Tarjima:**\n"
                f"{translated}"
            )

        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Tarjima xatosi:", e)
        await query.edit_message_text(
            "❌ Tarjima qilishda xatolik yuz berdi.\n\n"
            "Iltimos, qaytadan urinib ko‘ring."
        )


# =========================================================
# BOT KOMANDALARI
# =========================================================

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Botni qayta ishga tushirish 🚀"),
        BotCommand("help", "Yordam va yo‘riqnoma ℹ️"),
        BotCommand("stats", "Statistika 📊")
    ]
    await application.bot.set_my_commands(commands)


# =========================================================
# MAIN
# =========================================================

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        print("Render Environment Variables ichiga BOT_TOKEN qo‘shing.")
        return

    app = (
        Application
        .builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    # START
    app.add_handler(CommandHandler("start", start))

    # HELP
    app.add_handler(CommandHandler("help", help_command))

    # STATS
    app.add_handler(CommandHandler("stats", stats))

    # RASM
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    # HUJJAT
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    # MATN
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # YANA
    app.add_handler(CallbackQueryHandler(again, pattern="^again$"))

    # TIL ALMASHTIRISH
    app.add_handler(CallbackQueryHandler(change_language, pattern="^change_language$"))

    # TIL TANLASH
    app.add_handler(CallbackQueryHandler(translate, pattern="^(uz|en|ru|ko|tr|de|fr|ar|zh-CN)$"))

    print("🤖 Tilchi bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
