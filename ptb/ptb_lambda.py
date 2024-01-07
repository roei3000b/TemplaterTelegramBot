import json
import asyncio
from pathlib import Path

from telegram import Update, BotCommand, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import os
import templater.templater
import templater.exceptions
import template_manager

LOCATION, SENDING_TEMPLATE, DONE, CHOOSING = range(4)
application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="ברוך הבא לטמפלייטר!"
                                                                          "\r\n"
                                                                        "שלח לי בבקשה קובץ Word או PowerPoint"
                                                                        " ואני אמלא אותו עבורך :)"
                                                                        "\r\n"
                                                                        "מוזמן לעיין בהוראות השימוש")

    await update.message.reply_document(document=open("הוראות שימוש בטמפלייטר.docx", "rb"))
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="https://youtu.be/kro65ztPqKQ?si=2Y-VfLmjpxT0wlY0")


async def template_fill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uploaded_file = await update.message.document.get_file()
    template_path = await uploaded_file.download_to_drive(custom_path=Path("/tmp") / Path(uploaded_file.file_path).name)
    context.user_data["template_path"] = template_path
    if not template_path.name.endswith(".docx") and not template_path.name.endswith(".pptx"):
        await update.message.reply_text("קובץ לא נתמך, שלח קובץ Word(docx) או PowerPoint(pptx) ")
        return ConversationHandler.END
    await update.message.reply_text("מעולה :) שלח בבקשה את שם העיר עבורה תרצה את הלו״ז.\r\n"
                                    "שים לב שהזמנים נלקחים מאתר ישיבה!")
    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        city = update.message.text
        context.user_data["city"] = city
        try:
            filled_path = templater.templater.fill_template(city,
                                                            context.user_data["template_path"],
                                                                 "/tmp",
                                                                                )
        except templater.templater.UnsupportedFileType as e:
            await update.message.reply_text("קובץ לא נתמך: " + str(e))
            return LOCATION
        await update.message.reply_document(document=open(filled_path, "rb"))
        keyboard = [['כן', 'לא']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("האם תרצה לקבל את הלו״ז בכל יום שישי באופן אוטומטי?",
                                        reply_markup=reply_markup)
        return CHOOSING
    except templater.exceptions.NoSuchCity:
        await update.message.reply_text("עיר לא קיימת במאגר! בחר עיר אחרת")
        return LOCATION

async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.lower()
    if user_choice == "לא":
        return DONE
    manager = template_manager.TemplateManager()
    manager.save(context.user_data["template_path"], context.user_data["city"], update.effective_chat.id)
    return DONE


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    return ConversationHandler.END


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))


async def main(event, context):
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    await application.bot.set_my_commands([BotCommand("start","התחל")])
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Document.ALL, template_fill)],
        states={
            LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, location),
            ],
            DONE: [
                MessageHandler(filters.Regex("^Done$"), done)
            ],
            CHOOSING: [
                MessageHandler(filters.Regex("^כן$"), choosing),
                MessageHandler(filters.Regex("^לא$"), done)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )

    application.add_handler(conv_handler)
    template_handler = MessageHandler(filters.Document.ALL, template_fill)
    application.add_handler(template_handler)

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



