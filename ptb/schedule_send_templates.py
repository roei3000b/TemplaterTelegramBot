import asyncio
import json
import os

from telegram.ext import ApplicationBuilder, CallbackQueryHandler

import template_manager
import templater.templater
import tempfile
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
MANAGER = template_manager.TemplateManager()

async def send_template(template_path, city, chat_id):
    with tempfile.TemporaryDirectory() as tmpdirname:
        chat_id = str(chat_id)
        downloaded_template_path = tmpdirname + "/" + Path(template_path).name
        MANAGER.s3.download_file(MANAGER.bucket_name, template_path, downloaded_template_path)
        filled_path = templater.templater.fill_template(city, downloaded_template_path, tmpdirname)
        keyboard = [
            [
                InlineKeyboardButton("הפסק עדכונים עבור לו״ז זה", callback_data=template_path)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await application.bot.send_document(chat_id=chat_id, document=open(filled_path, "rb"), reply_markup=reply_markup)

async def send_all_templates():
    for template in MANAGER.list_templates():
        await send_template(**template)

async def button(update, context):
    print("Hey!!")
    query = update.callback_query
    template_path = query.data
    await query.edit_message_text(text=template_path)
    MANAGER.delete(template_path)
    await query.edit_message_text(text="בוצע")

async def main(event, context):
    await send_all_templates()
    return {
        'statusCode': 200,
        'body': 'Success'
    }


def lambda_handler(event, context):
    return asyncio.get_event_loop().run_until_complete(main(event, context))
