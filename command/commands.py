import logging

import pytz
from telegram import Update, ForceReply

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import config.db.database


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_user = update.message.chat.id
    first_name = update.message.chat.first_name
    last_name = update.message.chat.last_name
    username = update.message.chat.username
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = update.message.date.replace(tzinfo=pytz.utc).astimezone(tz_jakarta)
    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")

    # menyimpan foto profil pengguna
    photo = None
    photos = await context.bot.getUserProfilePhotos(id_user)
    print(photos)
    if photos.total_count > 0:
        photo = photos.photos[0][-1].file_id

    # Insert data user ke dalam tabel user
    sql = "INSERT INTO users_telegram (id_user, photo, username, first_name, last_name, created_at) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (id_user, photo, username, first_name, last_name, created_at)
    id_user_query = config.db.database.query_all(f"SELECT id_user FROM users_telegram WHERE id_user = {id_user}")
    logging.info(f"user_id={id_user}, first_name={first_name}, last_name={last_name}, username={username}")
    if len(id_user_query) > 0 and id_user == id_user_query[0][0]:
        pesan1 = rf'Halo {update.effective_user.mention_html()} ! Anda Sudah Terdaftar di Database Kami'
        chat_bot_save(id_user, pesan1, created_at)
        pesan2 = rf'Silahkan Gunakan Command /help untuk melihat daftar command yang tersedia'
        chat_bot_save(id_user, pesan2, created_at)
        return [await update.message.reply_html(pesan1),
                await update.message.reply_text(pesan2)]
    config.db.database.query_db(sql, val)
    chat_user_save(id_user, update.message.text, created_at)

    user = update.effective_user

    pesan1 = rf'Halo {update.effective_user.mention_html()} ! Selamat Datang di Bot Banjir Lamongan'
    chat_bot_save(id_user, pesan1, created_at)
    pesan2 = rf'Silahkan Gunakan Command /help untuk melihat daftar command yang tersedia'
    chat_bot_save(id_user, pesan2, created_at)
    return [await update.message.reply_html(pesan1),
            await update.message.reply_text(pesan2)]


async def job_query_broadcast(context):
    # query data user yang sudah terdaftar
    sql_user = "SELECT id_user FROM users_telegram"
    id_user_query = config.db.database.query_all(sql_user)
    # query data broadcast
    sql_broadcast = "SELECT id, message, is_send, created_at FROM message_broadcast WHERE is_send = 0"
    broadcast_query = config.db.database.query_all(sql_broadcast)
    # print(broadcast_query)
    # kirim pesan broadcast ke setiap user
    for id_user in id_user_query:
        for broadcast in broadcast_query:
            id_broadcast = broadcast[0]
            message = broadcast[1]
            print(broadcast)
            is_send = broadcast[2]
            print(is_send)
            created_at = broadcast[3]
            if is_send == 0:
                try:
                    await context.bot.send_message(chat_id=id_user[0], text=message)
                    chat_bot_save(id_user[0], message, created_at)
                    # update status is_send
                    sql_update = "UPDATE message_broadcast SET is_send = 1 WHERE id = %s"
                    val = (id_broadcast,)
                    config.db.database.query_db(sql_update, val)
                    logging.info(
                        f"Broadcast Message id_broadcast={id_broadcast}, id_user={id_user[0]}, message={message}")
                except Exception as e:
                    logging.error(
                        f"Broadcast Message id_broadcast={id_broadcast}, id_user={id_user[0]}, message={message}")
                    continue


async def job_query_admin_chat(context):
    # query chat admin
    sql_chat = "SELECT id, id_admin, id_user, message, is_send, created_at FROM chat_admins WHERE is_send = 0"
    chat_query = config.db.database.query_all(sql_chat)
    # kirim pesan ke id_user
    for chat in chat_query:
        id_chat = chat[0]
        id_admin = chat[1]
        id_user = chat[2]
        message = chat[3]
        is_send = chat[4]
        created_at = chat[5]
        if is_send == 0:
            try:
                await context.bot.send_message(chat_id=id_user, text=message)
                # update status is_send
                sql_update = "UPDATE chat_admins SET is_send = 1 WHERE id = %s"
                val = (id_chat,)
                config.db.database.query_db(sql_update, val)
                logging.info(
                    f"Bot Chat Message id_chat={id_chat}, id_user={id_user}, message={message}")
            except Exception as e:
                logging.error(
                    f"Bot Chat Message id_chat={id_chat}, id_user={id_user}, message={message}")
                continue


async def job_check_bot_status(context):
    sql = "SELECT is_run from bot_status where id = 1"
    query = config.db.database.query_all(sql)
    is_run = query[0][0]
    if is_run == 0:
        context.job.schedule_removal()
        logging.info("Bot Stopped")
        raise SystemExit


async def chat_from_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    id_user = update.message.chat.id
    message = update.message.text
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = update.message.date.replace(tzinfo=pytz.utc).astimezone(tz_jakarta)
    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
    chat_user_save(id_user, message, created_at)


def chat_bot_save(id_user, message, created_at):
    id_admin = 1234
    is_send = 1

    sql = "INSERT INTO chat_admins (id_admin, id_user, message, is_send, created_at) VALUES (%s, %s, %s, %s, %s)"
    val = (id_admin, id_user, message, is_send, created_at)
    config.db.database.query_db(sql, val)
    logging.info(f"Chat From bot_id={id_user}, message={message}, created_at={created_at}")


def chat_user_save(id_user, message, created_at):
    sql = "INSERT INTO chat_user_telegram (id_user, message, created_at) VALUES (%s, %s, %s)"
    val = (id_user, message, created_at)
    config.db.database.query_db(sql, val)
    logging.info(f"Chat From user_id={id_user}, message={message}, created_at={created_at}")
