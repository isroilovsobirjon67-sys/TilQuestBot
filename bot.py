import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator
import speech_recognition as sr
from pydub import AudioSegment

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
        "Salom! Men TilQuestBot'man.\n\nMenga matn yoki **ovozli xabar** yuboring, men uni matnga o'girib, ingliz tiliga tarjima qilib beraman!"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(f"📊 **Bot statistikasi:**\n\nJami foydalanuvchilar soni: **{len(users)}** ta")
    else:
        await update.message.reply_text("Sizda bu komandadan foydalanish huquqi yo'q.")

# --- MATNNI TARJIMA QILISH ---
async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    text = update.message.text
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        await update.message.reply_text(f"🔤 **Tarjima (EN):**\n{translated}")
    except Exception:
        await update.message.reply_text("Tarjima qilishda xatolik yuz berdi.")

# --- OVOZLI XABARNI TANIASH VA TARJIMA QILISH ---
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    
    msg = await update.message.reply_text("🎙 Ovozli xabar qayta ishlanmoqda...")
    
    ogg_path = f"voice_{user_id}.ogg"
    wav_path = f"voice_{user_id}.wav"

    try:
        # Telegram'dan ovozli faylni yuklab olish
        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_drive(ogg_path)

        # OGG formatni WAV formatiga o'tkazish
        sound = AudioSegment.from_file(ogg_path)
        sound.export(wav_path, format="wav")

        # Ovozni matnga aylantirish (SpeechRecognition)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # O'zbek yoki Rus/Ingliz tillarini avto aniqlash
            text = recognizer.recognize_google(audio_data, language="uz-UZ")

        # Matnni ingliz tiliga tarjima qilish
        translated = GoogleTranslator(source='auto', target='en').translate(text)

        await msg.edit_text(
            f"🗣 **Ovozdan olingan matn:**\n{text}\n\n"
            f"🔤 **Inglizcha tarjimasi:**\n{translated}"
        )

    except sr.UnknownValueError:
        await msg.edit_text("Ovozni aniqlab bo'lmadi. Iltimos, aniqroq gapirib qayta yuboring.")
    except Exception as e:
        await msg.edit_text("Ovozli xabarni qayta ishlashda xatolik yuz berdi.")
    
    finally:
        # Vaqtinchalik fayllarni o'chirish
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

# --- BOTNI ISHGA TUSHIRISH ---
def main():
    TOKEN = "8969508702:AAG1bUWvj-TnmdL_tMC_wb8iP6Iu7jfePZA"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("Tilchi bot ishga tushdi!")
    app.run_polling()

if __name__ == '__main__':
    main()
