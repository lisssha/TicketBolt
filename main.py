from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
#все работает, осталось только разобраться с библиотекой. Но так как есть пример, то мейби должно быть с этим полегче
import psycopg2
from config import host, user, password, db_name


def init_db():
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS Ticket(
                id serial PRIMARY KEY,
                contact_information VARCHAR,
                complain_text VARCHAR NOT NULL);"""
            )
            # print("сработало")

    except Exception as _ex:
        print(f"ошибка при работе с бд: {_ex}")
    finally:
        if connection:
            connection.close()


init_db()


# обр нач кнопки стр
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["Написать жалобу"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f'Hello {update.effective_user.first_name},', reply_markup=reply_markup)


# обр кнопки "напис жалоб"
async def request_complain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # флаг юзера что он захотел пожаловаться (жалуются тока гады!!!)
    context.user_data['complain_mode'] = True
    await update.message.reply_text("Напишите нам, что вас не устроило или что хотели бы изменить. Нам важно ваше мнение!!ю ноу")


# здесь надо переписат  и думаю норм. значит отсанется только бд

# ответы на смс пользователя!!
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text == "Написать жалобу":
        await request_complain(update, context)

    elif context.user_data.get('complain_mode', False):
        if 'complain_text' not in context.user_data:
            # жалоба
            context.user_data['complain_text'] = update.message.text
            await update.message.reply_text("Подскажите ваши контактные данные")

        else:
            complain_user = update.message.text
            # вырезать жабу
            complain_text = context.user_data.pop('complain_text')
            # await update.message.reply_text(f"ваше имя: {complain_user}\nваша жалоба: {complain_text}")
            await update.message.reply_text("Спасибо за ваш отзыв! Жалобу рассмотрим в ближайшее время")
            context.user_data['complain_mode'] = False
            try:
                with psycopg2.connect(
                        host=host,
                        user=user,
                        password=password,
                        database=db_name
                ) as connection:
                    # connection.autocommit = True
                    with connection.cursor() as cursor:
                        # скл инъе
                        query = """INSERT INTO Ticket (contact_information, complain_text)VALUES (%s, %s)"""
                        cursor.execute(query, (complain_user, complain_text))
                        print("данные сохранены")
            except Exception as _ex:
                print(f"ошибка при работе с бд: {_ex}")


if __name__ == '__main__':
    app = ApplicationBuilder().token("7337155391:AAHdhBX98vtXU-deNw4QgbfvGopQS0yShC4").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
