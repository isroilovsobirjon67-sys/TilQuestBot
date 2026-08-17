from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from deep_translator import GoogleTranslator

TOKEN = "8969508702:AAG1bUWvj-TnmdL_tMC_wb8iP6Iu7jfePZA"

# Tillarni tanlash klaviaturasi
LANGUAGES_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="uz"),
        InlineKeyboardButton("🇬🇧 English", callback_data="en"),
    ],
    [
        InlineKeyboardButton("🇷🇺 Русский", callback_data="ru"),
        InlineKeyboardButton("🇰🇷 한국어", callback_data="ko"),
    ],
    [
        InlineKeyboardButton("🇹🇷 Türkçe", callback_data="tr"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="de"),
    ],
    [
        InlineKeyboardButton("🇫🇷 Français", callback_data="fr"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="ar"),
    ],
    [
        InlineKeyboardButton("🇨🇳 中文", callback_data="zh-CN"),
    ]
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start buyrug'i uchun handler"""
    await update.message.reply_text(
        "👋 Salom! Men Tilchi botman!\n\n"
        "📝 Tarjima qilmoqchi bo‘lgan so‘z yoki matningizni yozib yuboring."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help buyrug'i uchun handler"""
    await update.message.reply_text(
        "ℹ️ *Yordam va Yo'riqnoma:*\n\n"
        "1. Botga istalgan matningizni yozib yuboring.\n"
        "2. Paydo bo'lgan tugmalardan tarjima qilmoqchi bo'lgan tilingizni tanlang.\n"
        "3-. Bot avtomatik ravishda kiritilgan matn tilini aniqlaydi.",
        parse_mode="Markdown"
    )


async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lang buyrug'i uchun handler"""
    text = context.user_data.get("text")
    if not text:
        await update.message.reply_text(
            "📝 Avval tarjima qilmoqchi bo'lgan matningizni yozib yuboring!"
        )
        return

    await update.message.reply_text(
        f"📝 Sizning matningiz:\n\n{text}\n\n"
        "🌍 Qaysi tilga tarjima qilmoqchisiz?",
        reply_markup=LANGUAGES_KEYBOARD
    )

    await update.message.reply_text(
        f"📝 Sizning matningiz:\n\n{text}\n\n"
        "🌍 Qaysi tilga tarjima qilmoqchisiz?",
        reply_markup=LANGUAGES_KEYBOARD
    )

    await update.message.reply_text(
        f"📝 Sizning matningiz:\n\n{text}\n\n"
        "🌍 Qaysi tilga tarjima qilmoqchisiz?",
        reply_markup=LANGUAGES_KEYBOARD
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnli xabarlarni qabul qilish"""
    text = update.message.text
    context.user_data["text"] = text

    await update.message.reply_text(
        f"📝 Siz yozdingiz:\n\n{text}\n\n"
        "🌍 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tarjima qilish jarayoni"""
    query = update.callback_query
    await query.answer()

    text = context.user_data.get("text")

    if not text:
        await query.edit_message_text(
            "❌ Tarjima qilinadigan matn topilmadi. Iltimos, qaytadan matn yuboring."
        )
        return

    languages = {
        "uz": "uz",
        "en": "en",
        "ru": "ru",
        "ko": "ko",
        "tr": "tr",
        "de": "de",
        "fr": "fr",
        "ar": "ar",
        "zh-CN": "zh-CN"
    }

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

    target_language = languages.get(query.data)
    if not target_language:
        await query.edit_message_text("❌ Noma'lum til tanlandi.")
        return

    try:
        translated = GoogleTranslator(
            source="auto",
            target=target_language
        ).translate(text)

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Yana tarjima",
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

        # Ikkita yulduzcha o'rniga bitta yulduzcha ishlatildi (*Asl matn:* va *Tarjima:*)
        await query.edit_message_text(
            f"🌍 {names[query.data]}\n\n"
            f"📝 *Asl matn:* {text}\n\n"
            f"✅ *Tarjima:* {translated}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await query.edit_message_text(
            "❌ Tarjima qilishda xatolik yuz berdi."
        )
        print("Xatolik:", e)


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi matn so'rash"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 Yangi so‘z yoki gapni yozing:"
    )


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tilni almashtirish tugmasi bosilganda"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🌍 Qaysi tilga tarjima qilay?",
        reply_markup=LANGUAGES_KEYBOARD
    )


async def post_init(application: Application):
    """Telegram menyusiga buyruqlarni joylash"""
    commands = [
        BotCommand("start", "Botni qayta ishga tushirish"),
        BotCommand("help", "Yordam va yo'riqnoma"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Buyruqlar (Commands)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Matnli xabarlar
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    # Callback handlers (Tugmalar uchun)
    app.add_handler(
        CallbackQueryHandler(
            translate,
            pattern="^(uz|en|ru|ko|tr|de|fr|ar|zh-CN)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            again,
            pattern="^again$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            change_language,
            pattern="^change_language$"
        )
    )

    print("🤖 Tilchi bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()