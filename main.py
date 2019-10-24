from dialog_bot_sdk.bot import DialogBot
from models import Review, User, Event
from handlers import utils
from handlers.regular import *
import grpc
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
ENDPOINT = os.environ.get("ENDPOINT") or "hackathon-mob.transmit.im"


def on_click(*params):
    try:
        if params[0].id == "main_menu":
            main_menu_handler(bot, params)

        elif params[0].id == "event_list":
            event_list_handler(bot, params)

        elif params[0].id == "cancel":
            utils.cancel_handler(bot, params)

        elif params[0].id == "event_action":
            event_action_handler(bot, params)
    except:
        utils.cancel_handler(bot, params)


def on_msg(*params):
    try:
        if not User.select().where(User.uid == params[0].sender_uid).exists():
            new_user_handler(bot, params)
            return

        state = User.select().where(User.uid == params[0].sender_uid).get().state

        if params[0].message.textMessage.text == "/cancel" or params[0].message.textMessage.text == "/menu":
            utils.cancel_handler(bot, params)

        elif state == "NEW_REVIEW":
            new_review_handler(bot, params)

        elif state == "NEW_EVENT":
            new_event_handler(bot, params)

        else:
            unknown_message_handler(bot, params)


    except:
        error_handler(bot, params)


if __name__ == '__main__':
    bot = DialogBot.get_secure_bot(
        ENDPOINT,  # bot endpoint from environment
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        BOT_TOKEN  # bot token from environment
    )

    bot.messaging.on_message(on_msg, on_click)
