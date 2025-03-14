import time
from typing import Dict, List, Optional
from telegram import Message, ReplyKeyboardRemove, Update, ForceReply
from telegram.ext import Application, ConversationHandler, CommandHandler, ContextTypes, MessageHandler, filters
import json

from MQTT_Bridge.MQTT_Subscriber import MQTT_Subscriber
chats = {}

class CustomStringListFilter(filters.MessageFilter):
    __slots__ = ("_list",)

    def __init__(self, _list: list):
        self._list = _list
        for i in range(len(_list)):
            _list[i] = _list[i].upper()
        super().__init__(name=f"CustomStringListFilter({self._list})", data_filter=True)

    def filter(self, message: Message):
        if message.text:
            for element in self._list:
                if message.text.upper() == element:
                    return {"matches": [element]}
        return {}


# Set up the bot using the API token obtained from BotFather
#bot = telegram.Bot(token='6243331827:AAFlZgbqd6EGnRZE-d99zM9PQjI0-i2wcXk')

CITY, STREET, NUMBER = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    if chat_id in chats.keys() and all(map(lambda x: x is not None and isinstance(x, str), chats.get(chat_id))):
        message = rf"Bentornato {user.mention_html()}! Il tuo indirizzo è già memorizzato."
        await update.message.reply_html(message)
        return ConversationHandler.END
    else:
        chats[chat_id] = [None, None, None]
        message = f"Ciao {user.mention_html()}!\nInserisci il nome della tua città per continuare."
        await update.message.reply_html(message)
        return CITY
    
async def change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    message = f"Reimpostiamo l'indirizzo.\nInserisci il nome della tua città per continuare."
    await update.message.reply_html(message)
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_chat.id)
    chats[chat_id][0] = update.message.text
    message = f"Ok, quindi vivi a {update.message.text}. In quale via?"
    await update.message.reply_html(message)
    return STREET

async def street(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_chat.id)
    chats[chat_id][1] = update.message.text.upper()
    message = f"Ah, in {update.message.text}... e il numero civico è?"
    await update.message.reply_html(message,
        reply_markup=ReplyKeyboardRemove()
    )
    return NUMBER


async def number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = str(update.effective_chat.id)
    chats[chat_id][2] = update.message.text
    message = ("Bene, ti notificherò quando sarà ora"
               " di portare fuori i bidoni!\n"
               "Se dovessi cambiare il tuo indirizzo,"
                " scrivimi /change e ti aiuterò.")
    await update.message.reply_html(message,
        reply_markup=ReplyKeyboardRemove()
    )
    with open("chats.json", "w") as f:
        json.dump(chats, f)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    #logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Ciao! Imposteremo il tuo indirizzo un'altra volta.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main(cities_list, street_list) -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6243331827:AAFlZgbqd6EGnRZE-d99zM9PQjI0-i2wcXk").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("change", change)],
        states={
            CITY: [MessageHandler(CustomStringListFilter(cities_list), city)],
            STREET: [MessageHandler(CustomStringListFilter(street_list), street)],
            NUMBER: [MessageHandler(filters.Regex("^([0-9]*)$"), number)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    # Build available city list
    channel = MQTT_Subscriber('pattumi')
    while channel.garbage_median() == {}:
        time.sleep(10)
    
    median = channel.garbage_median()
    city_list = [_city for _city in median.keys()]

    street_list = []
    for _city in city_list:
        street_list += [_street for _street in median[_city].keys()]

    try:
        with open("chats.json") as f:
            chats = json.load(f)
            print(chats)
    except:
        pass
    print("Bot ready!")
    main(city_list, street_list)
    print(chats)
    with open("chats.json", "w") as f:
        json.dump(chats, f)
