from dialog_bot_sdk import interactive_media
from dialog_bot_sdk.bot import DialogBot
from models import Event, User, Review


def cancel_handler(bot: DialogBot, params):
    try:
        bot.messaging.send_message(
            params[0].peer,
            "Отправляю вас в главное меню",
            get_default_layout()
        )

        set_state_by_uid(params[0].sender_uid, "START")
    except (AttributeError, KeyError):
        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Отправляю вас в главное меню",
            get_default_layout()
        )

        set_state_by_uid(params[0].uid, "START")


def get_default_layout():
    return [interactive_media.InteractiveMediaGroup(
        [
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("make_review", "Оставить отзыв")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("create_event", "Создать новое событие")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("list_events", "Мои события")
            )
        ]
    )]


def get_events_list(uid: int):
    events = {}

    for event in Event.select().where(Event.owner == uid).order_by(Event.name):
        events[str(event.get_id())] = f"{event.name}"

    return [interactive_media.InteractiveMediaGroup(
        [interactive_media.InteractiveMedia(
            "event_list",
            interactive_media.InteractiveMediaSelect(
                events,
                label="Список событий"
            )
        ),
            interactive_media.InteractiveMedia(
                "cancel",
                interactive_media.InteractiveMediaButton("cancel", "В главное меню")
            )
        ]
    )]


def set_state_by_uid(uid: int, state: str):
    user = User.select().where(User.uid == uid).get()
    user.state = state
    user.save()


def get_event_actions(event_id):
    return [interactive_media.InteractiveMediaGroup(
        [
            interactive_media.InteractiveMedia(
                "event_action",
                interactive_media.InteractiveMediaButton(f"delete_{event_id}", "Удалить событие")
            ),
            interactive_media.InteractiveMedia(
                "event_action",
                interactive_media.InteractiveMediaButton(f"export_{event_id}",
                                                         "Выгрузить отзывы о событии в табличном формате")
            ),
            interactive_media.InteractiveMedia(
                "cancel",
                interactive_media.InteractiveMediaButton("cancel", "Назад в главное меню")
            )
        ]
    )]
