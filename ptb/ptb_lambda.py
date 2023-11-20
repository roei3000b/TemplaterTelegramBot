import json
import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
import templater.word_templater

application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm roei!")


async def docx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uploaded_file = await update.message.document.get_file()
    c = await uploaded_file.download_to_drive(custom_path=Path("/tmp")/Path(uploaded_file.file_path).name)
    filled_path = templater.word_templater.fill_template(c, "/tmp")
    # TODO: figure out how to convert word to pdf for sending by bot
    await context.bot.send_document(chat_id=update.effective_chat.id, document=open(filled_path, "rb"))

def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))


async def main(event, context):
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

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



