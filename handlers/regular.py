from dialog_bot_sdk.bot import DialogBot
from dialog_bot_sdk import interactive_media, internal
from models import User, Event, Review
from handlers import utils
from openpyxl import Workbook
from pathlib import Path

REVIEW_CACHE = {}
EVENT_CACHE = {}
EVENT_LIST_MESSAGE_CACHE = {}


def unknown_message_handler(bot: DialogBot, params):
    try:
        peer = bot.users.get_user_peer_by_id(params[0].uid)
    except AttributeError:
        peer = params[0].peer

    bot.messaging.send_message(
        peer,
        "Я не понимаю, что ты хочешь сделать. Можешь написать /menu для возврата в главное меню"
    )


def error_handler(bot: DialogBot, params):
    try:
        peer = bot.users.get_user_peer_by_id(params[0].uid)
    except AttributeError:
        peer = params[0].peer

    bot.messaging.send_message(
        peer,
        "Кажется, что то сломалось. Возвращаемся в главное меню"
    )

    utils.cancel_handler(bot, params)


def new_user_handler(bot: DialogBot, params):
    bot.messaging.send_message(
        params[0].peer,
        "Привет. Этот бот поможет тебе оставить или собрать отзыв о мероприятии"
    )

    user = User.create(
        uid=params[0].sender_uid
    )

    utils.cancel_handler(bot, params)


def main_menu_handler(bot: DialogBot, params):
    if params[0].value == "create_event":
        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Отлично, всегда рад новым мероприятиям. Как называть событие?"
        )

        utils.set_state_by_uid(params[0].uid, "NEW_EVENT")

    elif params[0].value == "make_review":
        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Отлично, всегда рад новым отзывам. На какое мероприятие оставляем отзыв?"
        )

        utils.set_state_by_uid(params[0].uid, "NEW_REVIEW")

    elif params[0].value == "list_events":
        if Event.select().where(Event.owner == params[0].uid).exists():
            bot.messaging.send_message(
                bot.users.get_user_peer_by_id(params[0].uid),
                "Список мероприятий, которыми вы управляете. Для управления мероприятием выберите его в списке",
                utils.get_events_list(params[0].uid)
            )

        else:
            bot.messaging.send_message(
                bot.users.get_user_peer_by_id(params[0].uid),
                "У вас нет мероприятий"
            )


def new_review_handler(bot: DialogBot, params):
    if params[0].sender_uid not in REVIEW_CACHE:
        event_name = params[0].message.textMessage.text

        if not Event.select().where(Event.name == event_name).exists():
            bot.messaging.send_message(
                params[0].peer,
                "Такого события не существует."
                " Попробуйте другое название или напишите /cancel для возврата в главное меню"
            )
            return

        event_id = Event.select().where(Event.name == event_name).get().get_id()
        REVIEW_CACHE[params[0].sender_uid] = {
            "writer_uid": params[0].sender_uid,
            "event_id": event_id
        }

        bot.messaging.send_message(
            params[0].peer,
            "Оцените событие от 0 до 10"
        )

    elif "rating" not in REVIEW_CACHE[params[0].sender_uid]:
        try:
            rating = int(params[0].message.textMessage.text)
        except ValueError:
            bot.messaging.send_message(
                params[0].peer,
                "Пожалуйста, отправьте число от 0 до 10 или напишите /cancel для возврата в главное меню"
            )
            return

        if rating < 0 or rating > 10:
            bot.messaging.send_message(
                params[0].peer,
                "Пожалуйста, отправьте число от 0 до 10 или напишите /cancel для возврата в главное меню"
            )
            return

        REVIEW_CACHE[params[0].sender_uid]["rating"] = rating

        bot.messaging.send_message(
            params[0].peer,
            "Отлично! Теперь напишите отзыв о событии в одном сообщении, или отправьте красивый эмодзи"
        )

    elif "text" not in REVIEW_CACHE[params[0].sender_uid]:
        text = params[0].message.textMessage.text

        REVIEW_CACHE[params[0].sender_uid]["text"] = text

        bot.messaging.send_message(
            params[0].peer,
            "Осталось только подписаться. Если подпишитесь псведонимом, я сохраню анонимность"
        )

    elif "writer_name" not in REVIEW_CACHE[params[0].sender_uid]:
        writer_name = params[0].message.textMessage.text

        REVIEW_CACHE[params[0].sender_uid]["writer_name"] = writer_name

        bot.messaging.send_message(
            params[0].peer,
            "Прекрасно, отзыв записан. Спасибо :)"
        )

        review = Review.create(
            **REVIEW_CACHE[params[0].sender_uid]
        )
        review.save()

        del REVIEW_CACHE[params[0].sender_uid]

        utils.cancel_handler(bot, params)


def new_event_handler(bot: DialogBot, params):
    if params[0].sender_uid not in EVENT_CACHE:
        event_name = params[0].message.textMessage.text

        if Event.select().where(Event.name == event_name).exists():
            bot.messaging.send_message(
                params[0].peer,
                "Событие с таким названием уже сущестует."
                " Попробуйте другое название или напишите /cancel для возврата в главное меню"
            )
            return

        EVENT_CACHE[params[0].sender_uid] = {
            "name": event_name,
            "owner": params[0].sender_uid
        }

        bot.messaging.send_message(
            params[0].peer,
            "Укажите краткий комментарий к событию, в одном сообщении"
        )

    elif "details" not in EVENT_CACHE[params[0].sender_uid]:
        event_details = params[0].message.textMessage.text
        EVENT_CACHE[params[0].sender_uid]["details"] = event_details

        event = Event.create(
            **EVENT_CACHE[params[0].sender_uid]
        )
        event.save()

        del EVENT_CACHE[params[0].sender_uid]

        bot.messaging.send_message(
            params[0].peer,
            "Событие успешно создано. Что бы начать собирать отзывы, просто отправьте бота и "
            "название события участникам"
        )

        utils.cancel_handler(bot, params)


def event_list_handler(bot: DialogBot, params):
    event_id = int(params[0].value)
    EVENT_LIST_MESSAGE_CACHE[params[0].uid] = params[0]
    event = Event.select().where(Event.id == event_id).get()
    reviews_count = Review.select().where(Review.event_id == event_id).count()

    bot.messaging.send_message(
        bot.users.get_user_peer_by_id(params[0].uid),
        f"Событие '{event.name}':"
        f"\n {reviews_count} отзыв(ов)"
        f"\n {event.details}"
    )

    bot.messaging.send_message(
        bot.users.get_user_peer_by_id(params[0].uid),
        "Опции",
        utils.get_event_actions(event_id)
    )


def event_action_handler(bot: DialogBot, params):
    task, event_id = params[0].value.split("_")
    event_id = int(event_id)
    event = Event.select().where(Event.id == event_id).get()

    if task == "delete":
        event.delete_instance()

        for review in Review.select().where(Review.event_id == event_id):
            review.delete_instance()

        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Событие успешно удалено"
        )

        bot.messaging.delete(
            EVENT_LIST_MESSAGE_CACHE[params[0].uid]
        )

        bot.messaging.delete(
            params[0]
        )

        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Список мероприятий, которыми вы управляете. Для управления мероприятием выберите его в списке",
            utils.get_events_list(params[0].uid)
        )

    elif task == "export":
        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Ваша таблица:"
        )

        wb = Workbook()
        ws = wb.active

        ws.append(["Оценка", "Комменатрий", "Подпись", "Время написания"])

        for review in Review.select().where(Review.event_id == event_id):
            ws.append(
                [review.rating, review.text, review.writer_name, f"{review.write_time.strftime('%d:%m:%y %H:%M')}"]
            )

        wb.save(f"sheets/{event.name}.xlsx")

        bot.messaging.send_file(
            bot.users.get_user_peer_by_id(params[0].uid),
            f"sheets/{event.name}.xlsx"
        )

        object = Path(f"sheets/{event.name}.xlsx")
        object.unlink()
