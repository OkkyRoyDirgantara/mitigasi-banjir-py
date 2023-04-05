import logging
import os
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ApplicationBuilder, \
    CallbackContext

from dotenv import load_dotenv

import log_app.log
from command import command

load_dotenv()
token_bot_telegram = os.getenv("TOKEN_BOT_TELEGRAM", "")


def run_telegram_bot():
    application = ApplicationBuilder().token(token_bot_telegram).build()
    log_app.log.logger().info("Telegram bot is running")
    application.add_handler(command.command_app())
    application.run_polling()