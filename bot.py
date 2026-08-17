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


if name == "main":
    main()
