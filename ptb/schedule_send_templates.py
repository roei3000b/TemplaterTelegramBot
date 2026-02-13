import asyncio
import json
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import boto3
from telegram.ext import ApplicationBuilder, CallbackQueryHandler

import template_manager
import templater.templater
import tempfile
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

logger = logging.getLogger(__name__)

application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
MANAGER = template_manager.TemplateManager()

def send_email_with_attachment(recipient, file_path):
    ses = boto3.client('ses')
    sender = os.getenv('SES_SENDER_EMAIL')
    if not sender:
        logger.error("SES_SENDER_EMAIL not configured, skipping email")
        return

    filename = Path(file_path).name
    msg = MIMEMultipart()
    msg['Subject'] = f'לו״ז שבת - {filename}'
    msg['From'] = sender
    msg['To'] = recipient

    msg.attach(MIMEText('מצורף לו״ז השבת שלך.', 'plain', 'utf-8'))

    with open(file_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    msg.attach(part)

    ses.send_raw_email(
        Source=sender,
        Destinations=[recipient],
        RawMessage={'Data': msg.as_string()}
    )


async def send_template(template_path, city, chat_id, email=None):
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

        if email:
            try:
                send_email_with_attachment(email, filled_path)
            except Exception:
                logger.exception("Failed to send email to %s", email)

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
