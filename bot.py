import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    Application
)
from deep_translator import GoogleTranslator
from docx import Document  # Word fayllarini o'qish uchun kutubxona

# --- HEALTH-CHECK SERVER ---
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

# --- SOZLAMALAR ---
# Token hosting muhitidan olinadi (Xavfsiz usul)
TOKEN = os.environ.get("BOT_TOKEN", "8969508702:AAG1bUWvj-TnmdL_tMC_wb8iP6Iu7jfePZA")
ADMIN_ID = 6575497342
USERS_FILE = "users.json"

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
    keys = list(names.keys())
    for i in range(0, len(keys), 3):
        row = [
            InlineKeyboardButton(names[k], callback_data=k)
            for k in keys[i:i+3]
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

LANGUAGES_KEYBOARD = get_language_keyboard()

# --- KOMANDALAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text(
        "👋 Salom! Men **Tilchi bot**'man. 🤖\n\n"
        "✨ Menga istalgan matnni yoki **.txt / .docx (Word)** faylni yuboring, men uni tez va sifatli tarjima qilib beraman! 🌍",
        reply_markup=LANGUAGES_KEYBOARD,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ **Yordam markazi:**\n\n"
        "💬 Matn yuboring yoki `.txt` / `.docx` hujjat yuklang.\n"
        "🔘 Chiqqan tugmalardan kerakli tilni tanlang.",
        parse_mode="Markdown"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(f"📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar: **{len(users)}** ta", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Sizda bu komandadan foydalanish huquqi yo'q.")

# --- MATNNI QAYTA ISHLASH ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    text = update.message.text
    context.user_data['text'] = text
    context.user_data['file_path'] = None
    await update.message.reply_text(
        "🌐 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )

# --- HUJJATLARNI QAYTA ISHLASH (.txt va .docx) ---
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    doc_file = update.message.document
    file_name = doc_file.file_name

    # Faqat .txt va .docx formatlarini ruxsat beramiz
    if not (file_name.endswith('.txt') or file_name.endswith('.docx')):
        await update.message.reply_text(
            "❌ Kechirasiz, hozircha faqat **.txt** va **.docx** (Word) fayllarini qabul qilaman.",
            parse_mode="Markdown"
        )
        return

    # Faylni yuklab olish
    file = await context.bot.get_file(doc_file.file_id)
    os.makedirs("downloads", exist_ok=True)
    local_path = os.path.join("downloads", file_name)
    await file.download_to_drive(local_path)

    extracted_text = ""
    if file_name.endswith('.txt'):
        with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
            extracted_text = f.read()
    elif file_name.endswith('.docx'):
        doc = Document(local_path)
        extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    # Faylni o'chirib tashlaymiz (serverni to'ldirmaslik uchun)
    if os.path.exists(local_path):
        os.remove(local_path)

    if not extracted_text.strip():
        await update.message.reply_text("❌ Fayl ichida tarjima qilish uchun matn topilmadi.")
        return

    # Juda uzun matnlar uchun cheklov (Telegram xabar hajmi cheklangani uchun)
    if len(extracted_text) > 3000:
        extracted_text = extracted_text[:3000] + "\n\n...(Matn juda uzun bo'lgani uchun qisqartirildi)"

    context.user_data['text'] = extracted_text
    await update.message.reply_text(
        f"📄 **Fayl qabul qilindi:** `{file_name}`\n🌐 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD,
        parse_mode="Markdown"
    )

# --- MAXSUS TUGMALAR ---
async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✍️ Yangi so‘z, matn yoki hujjat yuboring:")

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌍 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )

# --- TARJIMA QILISH ---
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = context.user_data.get('text')
    if not text:
        await query.edit_message_text("❌ Matn topilmadi. Iltimos, yangi matn yoki fayl yuboring.")
        return

    target_code = query.data
    target_language = names.get(target_code)
    
    if not target_language:
        await query.edit_message_text("❌ Noma'lum til tanlandi.")
        return

    try:
        translated = GoogleTranslator(
            source="auto",
            target=target_code
        ).translate(text)

        keyboard = [
            [InlineKeyboardButton("🔄 Yana tarjima qilish", callback_data="again")],
            [InlineKeyboardButton("🌍 Tilni almashtirish", callback_data="change_language")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if target_code == "ar":
            rtl_mark = "\u200F"
            message_text = (
                f"{rtl_mark}🇸🇦 {names[target_code]} tiliga tarjima:\n\n"
                f"{rtl_mark}📝 *Asl matn:* {text[:500]}...\n\n"
                f"{rtl_mark}✅ *Tarjima:* {translated}"
            )
        else:
            message_text = (
                f"🌐 {names[target_code]} tiliga tarjima:\n\n"
                f"📝 *Asl matn:* {text[:500]}...\n\n"
                f"✅ *Tarjima:* {translated}"
            )

        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await query.edit_message_text("❌ Tarjima qilishda xatolik yuz berdi.")
        print("Xatolik:", e)

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Botni qayta ishga tushirish 🚀"),
        BotCommand("help", "Yordam va yo'riqnoma ℹ️"),
        BotCommand("stats", "Statistika 📊"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))

    # Hujjatlarni qabul qilish handler'i
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    # Oddiy matnlar uchun handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.add_handler(CallbackQueryHandler(again, pattern="^again$"))
    app.add_handler(CallbackQueryHandler(change_language, pattern="^change_language$"))
    app.add_handler(CallbackQueryHandler(translate, pattern="^(uz|en|ru|ko|tr|de|fr|ar|zh-CN)$"))

    print("🤖 Tilchi bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
