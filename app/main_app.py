#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import asyncio
import logging
import os
from datetime import datetime

import config.db.database

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import command.commands
from utils.logger import log_app

log_app()


def start_bot(time):
    status = 1
    sql = "UPDATE bot_status SET is_run = %s, run_at = %s WHERE id = 1"
    val = (status, time)
    config.db.database.query_db(sql, val)


def stop_bot(time):
    status = 0
    sql = "UPDATE bot_status SET is_run = %s, stop_at = %s WHERE id = 1"
    val = (status, time)
    config.db.database.query_db(sql, val)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await command.commands.start(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def chat_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await command.commands.chat_from_user(update, context)


async def main_broadcast(context) -> None:
    await command.commands.job_query_broadcast(context)


async def admin_chat(context) -> None:
    await command.commands.job_query_admin_chat(context)


async def check_bot_status(context) -> None:
    await command.commands.job_check_bot_status(context)


# @retry(stop_max_attempt_number=3, wait_fixed=10000)
def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.getenv("TOKEN_BOT_TELEGRAM")).build()
    job_queue_admin_chat = application.job_queue
    job_queue_admin_chat.run_repeating(callback=admin_chat, interval=10, first=0)
    job_queue_broadcast = application.job_queue
    job_queue_broadcast.run_repeating(callback=main_broadcast, interval=10, first=0)
    job_queue_check_bot_status = application.job_queue
    job_queue_check_bot_status.run_repeating(callback=check_bot_status, interval=10, first=0)
    command_handlers = [CommandHandler("start", start),
                        CommandHandler("help", help_command),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, chat_from_user)]
    # on different commands - answer in Telegram
    # on non command i.e. message - echo the message on Telegram
    for handler in command_handlers:
        application.add_handler(handler)

    try:
        # Start the Application
        now = datetime.now()
        print(f"Running: {now}")
        start_bot(now)
        application.run_polling()
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
    except KeyboardInterrupt:
        now = datetime.now()
        print(f"Stop Keyboard Interrupt: {now}")
        stop_bot(now)
        raise Exception("Bot is stopped")
    except Exception as e:
        logging.error(e)
        now = datetime.now()
        print(f"Stop : {now} - {e}")
        stop_bot(now)
    finally:
        now = datetime.now()
        print(f"Stop Finally: {now}")
        stop_bot(now)
