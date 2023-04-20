import logging
from datetime import datetime, timedelta

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
    val = (id_user, photo, username, first_name, last_name, get_string_time())
    id_user_query = config.db.database.query_all(f"SELECT id_user FROM users_telegram WHERE id_user = {id_user}")
    logging.info(f"user_id={id_user}, first_name={first_name}, last_name={last_name}, username={username}")
    if len(id_user_query) > 0 and id_user == id_user_query[0][0]:
        chat_user_save(id_user, update.message.text, get_string_time())
        pesan1 = rf'Halo {update.effective_user.mention_html()} ! Anda Sudah Terdaftar di Database Kami'
        pesan2 = rf'Silahkan Gunakan Command /help untuk melihat daftar command yang tersedia'
        return [await update.message.reply_html(pesan1),
                chat_bot_save(id_user, pesan1, get_string_time()),
                await update.message.reply_html(pesan2),
                chat_bot_save(id_user, pesan2, get_string_time())]

    config.db.database.query_db(sql, val)
    chat_user_save(id_user, update.message.text, get_string_time())

    user = update.effective_user

    pesan1 = rf'Halo {update.effective_user.mention_html()} ! Selamat Datang di Bot Banjir Lamongan'
    pesan2 = rf'Silahkan Gunakan Command /help untuk melihat daftar command yang tersedia'
    return [await update.message.reply_html(pesan1),
            chat_bot_save(id_user, pesan1, get_string_time()),
            await update.message.reply_html(pesan2),
            chat_bot_save(id_user, pesan2, get_string_time())]


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
            if is_send == 0:
                try:
                    await context.bot.send_message(chat_id=id_user[0], text=message)
                    chat_bot_save(id_user[0], message, get_string_time())
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
    chat_user_save(id_user, message, get_string_time())


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


def get_string_time():
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = datetime.now().replace(tzinfo=pytz.utc).astimezone(tz_jakarta)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


async def cek_cuaca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    id_user = update.message.chat.id
    message = update.message.text
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = update.message.date.replace(tzinfo=pytz.utc).astimezone(tz_jakarta)
    created_at = dt.strftime("%Y-%m-%d %H:%M:%S")

    sql = f'SELECT h0, h6, h12, h18, updated_at FROM weathers where datetime = {dt.strftime("%Y%m%d")}'
    sql_query = config.db.database.query_all(sql)
    if sql_query == []:
        pesan = f'Belum ada data cuaca untuk tanggal {dt.strftime("%d-%m-%Y")}'
        chat_user_save(id_user, message, get_string_time())
        return [await update.message.reply_html(pesan),
                chat_bot_save(id_user, pesan, get_string_time())]
    else:
        kodecuaca = {"0": "Cerah",
                     "1": "Cerah Berawan",
                     "2": "Cerah Berawan",
                     "3": "Berawan",
                     "4": "Berawan Tebal",
                     "5": "Udara Kabur",
                     "10": "Asap",
                     "45": "Kabut",
                     "60": "Hujan Ringan",
                     "61": "Hujan Sedang",
                     "63": "Hujan Lebat",
                     "80": "Hujan Lokal",
                     "95": "Hujan Petir",
                     "97": "Hujan Petir"}

        pesan = (f'Cuaca di Lamongan hari ini\n\n'
                 f'Pukul 00:00 - 06:00 : {kodecuaca[str(sql_query[0][0])]} \n'
                 f'Pukul 06:00 - 12:00 : {kodecuaca[str(sql_query[0][1])]} \n'
                 f'Pukul 12:00 - 18:00 : {kodecuaca[str(sql_query[0][2])]} \n'
                 f'Pukul 18:00 - 24:00 : {kodecuaca[str(sql_query[0][3])]} \n'
                 f'\n'
                 f'Data Diperbarui : {sql_query[0][4]} \n'
                 f'\n'
                 f'Sumber : BMKG \n')
        chat_user_save(id_user, message, get_string_time())
        return [await update.message.reply_html(pesan),
                chat_bot_save(id_user, pesan, get_string_time())]


async def job_cuaca_broadcast(context):
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    dt = datetime.now(tz_jakarta) + timedelta(hours=1)
    sql_cuaca = f'SELECT h0, h6, h12, h18, updated_at FROM weathers where datetime = {dt.strftime("%Y%m%d")}'
    sql_query_cuaca = config.db.database.query_all(sql_cuaca)

    sql_user = f'SELECT id_user FROM users_telegram'
    sql_query_user = config.db.database.query_all(sql_user)

    if sql_query_cuaca == []:
        pesan = f'Belum ada data cuaca untuk tanggal {dt.strftime("%d-%m-%Y")}'
        for i in sql_query_user:
            try:
                await context.bot.send_message(chat_id=i[0], text=pesan)
                chat_bot_save(i[0], pesan, get_string_time())
            except Exception as e:
                logging.error(f"Error Broadcast Cuaca id_user={i[0]}")
                continue
    else:
        kodecuaca = {"0": "Cerah",
                     "1": "Cerah Berawan",
                     "2": "Cerah Berawan",
                     "3": "Berawan",
                     "4": "Berawan Tebal",
                     "5": "Udara Kabur",
                     "10": "Asap",
                     "45": "Kabut",
                     "60": "Hujan Ringan",
                     "61": "Hujan Sedang",
                     "63": "Hujan Lebat",
                     "80": "Hujan Lokal",
                     "95": "Hujan Petir",
                     "97": "Hujan Petir"}

        if dt.hour >= 0 and dt.hour < 6:
            pesan = (f'Cuaca di Lamongan pukul {dt.strftime("%H:%M:%S")} \n\n'
                     f'Pukul 00:00 - 06:00 : {kodecuaca[str(sql_query_cuaca[0][0])]} \n'
                     f'\n'
                     f'Data Diperbarui : {sql_query_cuaca[0][4]} \n'
                     f'\n'
                     f'Sumber : BMKG \n')
            for i in sql_query_user:
                try:
                    await context.bot.send_message(chat_id=i[0], text=pesan)
                    chat_bot_save(i[0], pesan, get_string_time())
                except Exception as e:
                    logging.error(f"Error Broadcast Cuaca id_user={i[0]}")
                    continue

        elif dt.hour >= 6 and dt.hour < 12:
            pesan = (f'Cuaca di Lamongan pukul {dt.strftime("%H:%M:%S")} \n\n'
                     f'Pukul 06:00 - 12:00 : {kodecuaca[str(sql_query_cuaca[0][1])]} \n'
                     f'\n'
                     f'Data Diperbarui : {sql_query_cuaca[0][4]} \n'
                     f'\n'
                     f'Sumber : BMKG \n')
            for i in sql_query_user:
                try:
                    await context.bot.send_message(chat_id=i[0], text=pesan)
                    chat_bot_save(i[0], pesan, get_string_time())
                except Exception as e:
                    logging.error(f"Error Broadcast Cuaca id_user={i[0]}")
                    continue
        elif dt.hour >= 12 and dt.hour < 18:
            pesan = (f'Cuaca di Lamongan pukul {dt.strftime("%H:%M:%S")} \n\n'
                     f'Pukul 12:00 - 18:00 : {kodecuaca[str(sql_query_cuaca[0][2])]} \n'
                     f'\n'
                     f'Data Diperbarui : {sql_query_cuaca[0][4]} \n'
                     f'\n'
                     f'Sumber : BMKG \n')
            for i in sql_query_user:
                try:
                    await context.bot.send_message(chat_id=i[0], text=pesan)
                    chat_bot_save(i[0], pesan, get_string_time())
                except Exception as e:
                    logging.error(f"Error Broadcast Cuaca id_user={i[0]}")
                    continue
        elif dt.hour >= 18 and dt.hour < 24:
            pesan = (f'Cuaca di Lamongan pukul {dt.strftime("%H:%M:%S")} \n\n'
                     f'Pukul 18:00 - 24:00 : {kodecuaca[str(sql_query_cuaca[0][3])]} \n'
                     f'\n'
                     f'Data Diperbarui : {sql_query_cuaca[0][4]} \n'
                     f'\n'
                     f'Sumber : BMKG \n')
            for i in sql_query_user:
                try:
                    await context.bot.send_message(chat_id=i[0], text=pesan)
                    chat_bot_save(i[0], pesan, get_string_time())
                except Exception as e:
                    logging.error(f"Error Broadcast Cuaca id_user={i[0]}")
                    continue
