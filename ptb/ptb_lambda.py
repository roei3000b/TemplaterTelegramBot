import json
import asyncio
from pathlib import Path

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import os
import templater.word_templater
import templater.exceptions

LOCATION, SENDING_TEMPLATE = range(2)
application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="ברוך הבא לטמפלייטר!"
                                                                          "\r\n"
                                                                        "שלח לי בבקשה קובץ וורד בפורמט docx"
                                                                        " ואני אמלא אותו עבורך :)"
                                                                        "\r\n"
                                                                        "מוזמן לעיין בהוראות השימוש")

    await update.message.reply_document(document=open("הוראות שימוש בטמפלייטר.docx", "rb"))


async def docx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uploaded_file = await update.message.document.get_file()
    template_path = await uploaded_file.download_to_drive(custom_path=Path("/tmp") / Path(uploaded_file.file_path).name)
    context.user_data["template_path"] = template_path
    await update.message.reply_text("מעולה :) שלח בבקשה את שם העיר עבורה תרצה את הלו״ז.\r\n"
                                    "שים לב שהזמנים נלקחים מאתר ישיבה!")
    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        city = update.message.text
        filled_path = templater.word_templater.fill_template(context.user_data["template_path"],
                                                             "/tmp",
                                                             city)
        # TODO: figure out how to convert word to pdf for sending by bot
        await update.message.reply_document(document=open(filled_path, "rb"))
        context.user_data.clear()
        return ConversationHandler.END
    except templater.exceptions.NoSuchCity:
        await update.message.reply_text("עיר לא קיימת במאגר! בחר עיר אחרת")
        return LOCATION

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    return ConversationHandler.END


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))


async def main(event, context):
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.bot.set_my_commands([BotCommand("start","התחל")])
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Document.DOCX, docx)],
        states={
            LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, location),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)
    docx_handler = MessageHandler(filters.Document.DOCX | filters.Document.DOC, docx)
    application.add_handler(docx_handler)

    try:
        await application.initialize()
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

        return {
            'statusCode': 200,
            'body': 'Success'
        }

    except Exception as exc:
        return {
            'statusCode': 500,
            'body': 'Failure'
        }



