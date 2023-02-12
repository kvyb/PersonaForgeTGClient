# TODO QOL Add "Typing" UI effect before response. See other Github for this.
# TODO DONE SET UP PAYMENT LIMITS.
# TODO DONE Set UP PAYING USER FLAIR
# TODO QOL Replace /cancel /start with proper handlers (see return)
# TODO DONE Make good descriptions
# TODO Add templates for everyone, of several characters to load.
# TODO DONE rewrite global storage to db
# TODO DONE fix regex to exclude the characters not just symbols
import websockets
import logging
import os
import pyfiglet
import asyncio
import json
import time
from datetime import datetime
import re

from telegram import __version__ as TG_VER
from dotenv import load_dotenv

import pymongo

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram.constants import ParseMode
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CallbackContext,
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    PreCheckoutQueryHandler,
    CallbackQueryHandler,
    PicklePersistence,
)
import telegram

# ============================
load_dotenv('.env')
BOT_KEY = os.getenv('TELEGRAM_TOKEN')
STRIPE_TOKEN = os.getenv('STRIPE_TOKEN')
FREE_CHAT_LIMIT = 40

# ============================
# === Enable logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Database init ===


cluster = pymongo.MongoClient("mongodb+srv://PersonaForge:w1ytzBnrDhO0hzjL@cluster0.tbx2bdw.mongodb.net/?retryWrites=true&w=majority")
db = cluster["Customers"]
collection = db["PersonaForge"]
# collection.insert_one({"_id":0, "user_name":"Kris"})
# Global dict to store data in telegram session

# === BOT ===
CHARCREATE, CHARLOAD, CHARNAME, YOUNAME, AIPERSONA, SCENARIO, CHAT, CHATFROMLOAD, DELETE = range(9)

# TODO set character info here:
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user what to do next"""
    # reply_keyboard = [["Creat Persona", "Load Persona", "Edit Persona", "Delete Persona"]]
    keyboard = [
        [
            # InlineKeyboardButton("About", callback_data="About"),
            InlineKeyboardButton("Load", callback_data="Load"),
        ],
        [
            InlineKeyboardButton("Delete", callback_data="Delete"),
            InlineKeyboardButton("Create", callback_data="Create")
        ],
    ]

    user = update.message.from_user
    UserID = user['id']
    document = collection.find_one({"_id": UserID})

    if document is not None and "PaidDate" in document:
        await update.message.reply_text(
            "<strong>✅ You have Full Access.</strong>\n\n"
            "<strong><u>PersonaForge GTP-6-JB:</u> </strong>\n\nTrained on 6 Billion parameters, 402 Billion data points, 1TB of data, and 383K epochs, this is an extremely robust implementation of the conversational AI model.\n\n"
            "<strong>This model can take the persona of any person or character you wish and communicate as a person.</strong>\n\n"
            "At any point, send /cancel to <u><strong>Stop</strong></u> and after send /start to <u><strong>Return</strong></u> to this menu.\n\n"
            "Press the <strong>Create</strong> button to make a new AI Persona. 👩👨\n\n\n"
            "Note:\n\n"
            "   - It takes the Persona 8 seconds to reply to a message, on average.\n"
            "   - <strong>This AI is unmoderated and can be explicit. By continuing, you confirm that you are 18+.</strong>\n"
            "   - <strong>Conversation data between the AI and users is not stored.</strong>\n",
            parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "<strong>PersonaForge GTP-6-JB: </strong>\n\nTrained on 6 Billion parameters, 402 Billion data points, 1TB of data, and 383K epochs, this is an extremely robust implementation of the conversational AI model.\n\n"
            "This model can take the persona of any person or character you wish and communicate as a person.\n\n"
            "At any point, send /cancel to <u><strong>Stop</strong></u> and after send /start to <u><strong>Return</strong></u> to this menu.\n\n"
            "Press the <strong>Create</strong> button to make a new AI Persona. 👩👨\n\n\n"
            "Note:\n\n"
            "   - It takes the Persona 8 seconds to reply to a message, on average.\n"
            "   - Running this AI is computationally expensive. You may send up to 50 messages for free. Consider purchasing the full access to support this project.\n"
            "   - <strong>This AI is unmoderated and can be explicit. By continuing, you confirm that you are 18+.</strong>\n"
            "   - <strong>Conversation data between the AI and users is not stored.</strong>\n",
            parse_mode=ParseMode.HTML, reply_markup = InlineKeyboardMarkup(keyboard)
        )
    return CHARCREATE

async def charcreate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    
    await query.answer()

    """Char Create mode"""
    user = query.from_user
    logger.info("Char CREATE mode: %s: %s", user.first_name, query.from_user)
    ChatID = update.callback_query.from_user.id
    UserID = user['id']

    if collection.find_one({"_id": UserID}) is None:
        collection.insert_one({"_id": UserID})
    else:
        pass

    if query.data == "Create":
        await query.edit_message_text(
            "<strong>Overseer:</strong> Persona Creation / <i>Start</i>\n\n"
            "<strong>Note that if any fields are skipped, the Persona will not be saved for later.</strong>\n\n"
            "Name your Persona:", parse_mode=ParseMode.HTML,
        )
        return CHARNAME
    elif query.data == "Load":
        
        document = collection.find_one({"_id": UserID})
        
        if document is not None:
            reply_keyboard = []
            # REMOVE THESE OR IT WONT ITERATE WITH FINALISED PERSONAS.
            # TODO: REVIEW THE BELOW COS THERE CAN BE AN EXCEPTION IF USER TRIES TO LOAD WITHOUT A COMPLETE CHAR (WONT HAPPEN REALLY)
            document.pop("_id")
            if document["SelectedPersona"]:
                document.pop("SelectedPersona", None)
            if document["ChatCount"]:
                document.pop("ChatCount", None)
            if "PaidDate" in document and document["PaidDate"]:
                document.pop("PaidDate", None)

            # CHECK THAT PERSONAS HAVE ALL REQUIRED PROPERTIES BEFORE SHOWING THEM IN SELECTION:
            required_keys = {"CallsUser", "Scenario", "Encounter", "CharHash"}

            for key in list(document.keys()):
                value = document[key]
                keys = [item.keys() for item in value]
                keys = set().union(*keys)
                if not required_keys.issubset(keys):
                    del document[key]
            
            keys = list(document.keys())
            # 
            for i in range(0, len(keys), 4):
                reply_keyboard.append(keys[i:i+4])

            await context.bot.send_message(text="<strong>Overseer:</strong> Select Your existing Personas:\nOr type /cancel\n", chat_id=ChatID, reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, input_field_placeholder="Select Persona to load."
                ), parse_mode=ParseMode.HTML,
            )
        else:
            print("Document not found.")
        return CHARLOAD
    
    elif query.data == "Delete":
        document = collection.find_one({"_id": UserID})
        
        if "_id" in document.keys():
            print(document)
            reply_keyboard = []
            document.pop("_id")
            if document["SelectedPersona"]:
                document.pop("SelectedPersona", None)
            if document["ChatCount"]:
                document.pop("ChatCount", None)
            if "PaidDate" in document and document["PaidDate"]:
                document.pop("PaidDate", None)

            # COMPOSE KEYBOARD WITH PERSONA NAMES

            reply_keyboard.append(list(document.keys()))

            await context.bot.send_message(text="Personas in Storage:\nRestart the Bot to return to menu. /cancel\n", chat_id=ChatID, reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, input_field_placeholder="Select Persona to Delete."
                ), parse_mode=ParseMode.HTML,
            )
        else:
            reply_keyboard_cancel = [["/cancel"]]
            await context.bot.send_message(text="Nothing to delete. Restart the Bot to return to menu. /cancel", chat_id=UserID, reply_markup=ReplyKeyboardMarkup(
                reply_keyboard_cancel, input_field_placeholder="Restart the Bot"
                ), parse_mode=ParseMode.HTML)
        return DELETE
    
    # elif query.data == "About":
    #     return

# === CREATE BLOCK START ===

async def charname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI character name"""
    user = update.message.from_user

    UserID = user['id']
    ChatID = update.message.from_user.id
    collection.update_one({"_id": UserID}, {"$set": {"SelectedPersona": update.message.text}})
    
    if update.message.text in collection.find_one({"_id": UserID}):
        reply_keyboard = [["/cancel"]]
        await context.bot.send_message(text="You already have a Persona with this name. /cancel and /start to return to menu", chat_id=ChatID, reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, input_field_placeholder="type /cancel and /start to return to menu"
                ), parse_mode=ParseMode.HTML)
        return
    else:

        collection.update_one({"_id": UserID}, {"$set": {update.message.text: []}}, upsert=True)
        print(collection.find_one({"_id": UserID}))
        
        await update.message.reply_text(
            "What should the Persona call you?\nOr send /skip."
        )

        return YOUNAME

async def youname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Name for user"""
    # user = update.message.from_user
    user = update.message.from_user
    UserID = user['id']
    
    # GET SELECTED PERSONA DATA
    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]

    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"CallsUser": update.message.text})}}, upsert=True)


    logger.info("The AI will call you: %s", update.message.text)
    await update.message.reply_text(
        "Describe, in one plain text message, what the Persona is like.\n\n"
        "Note:\n"
        "   - Include physical, behavioural, and mental characteristics, interests etc.\n"
        "   - You can also add contextual information about what the Persona did in the past, present or future.\n"
        "   - Must be in less than 500 words.\n"
        "Or send /skip",
        parse_mode=ParseMode.HTML
    )

    return AIPERSONA


async def skip_youname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Name for user"""
    user = update.message.from_user

    UserID = user['id']
    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]

    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"CallsUser": None})}}, upsert=True)


    logger.info("User %s did not send a name for himself", user.first_name)
    await update.message.reply_text(
        "<strong>Describe, in one plain text message, what the Persona is like.</strong>\n\n"
        "Note:\n"
        "   - Include physical, behavioural, and mental characteristics, interests etc.\n"
        "   - You can also add contextual information about what the Persona did in the past, present or future.\n"
        "   - Must be in less than 500 words.\n"
        "Or send /skip",
        parse_mode=ParseMode.HTML
    )

    return AIPERSONA

async def aipersona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Persona data for the AI gen."""
    # user = update.message.from_user
    user = update.message.from_user

    UserID = user['id']

    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]

    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"Scenario": update.message.text})}}, upsert=True)

    logger.info("The AI persona will be based on: %s", update.message.text)
    await update.message.reply_text(
        "<strong>Persona and User Encounter Setup</strong>\n\n"
        "Describe, in one plain text message, the circumstances and context of the first encounter "
        "between you and the Persona.\n"
        "Or send /skip",
        parse_mode=ParseMode.HTML
    )
    return SCENARIO

async def skip_aipersona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user

    UserID = user['id']

    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]

    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"Scenario": None})}}, upsert=True)

    logger.info("User %s did not send a persona.", user.first_name)
    await update.message.reply_text(
        "<strong>Persona and User Encounter Setup</strong>\n\n"
        "Describe, in one plain text message, the circumstances and context of the first encounter "
        "between you and the Persona.\n"
        "Or send /skip",
        parse_mode=ParseMode.HTML
    )

    return SCENARIO

async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Scenario"""
    # user = update.message.from_user
    user = update.message.from_user

    UserID = user['id']

    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]

    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"Encounter": update.message.text})}}, upsert=True)

    await update.message.reply_text(
        "<strong>The persona is ready.</strong>\nNow start your conversation.\n\n<strong>Talk to it like you would to a real human!</strong>\n\n"
        "<strong>You may narrate, or ask the persona to narrate: actions, activites, change of context, during the conversation.</strong>\n\n"
        "<strong>You can ask the Persona for actions by using the 'describe' or 'narrate' keyword. By asking, for example: 'Describe what will you do next?'</strong>\n\n"
        "type /cancel to detach from Persona, and press /start to return to main menu.",
        parse_mode=ParseMode.HTML
    )
    return CHAT

async def skip_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Scenario"""
    user = update.message.from_user

    UserID = user['id']

    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]
    
    collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"Encounter": None})}}, upsert=True)
    
    logger.info("User %s did not send a scenario.", user.first_name)
    await update.message.reply_text(
        "<strong>The persona is ready.</strong>\nNow start your conversation.\n\n<strong>Talk to it like you would to a real human!</strong>\n\n"
        "<strong>You may narrate, or ask the persona to narrate: actions, activites, change of context, during the conversation.</strong>\n\n"
        "<strong>You can ask the Persona for actions by using the 'describe' or 'narrate' keyword. By asking, for example: 'Describe what will you do next?'</strong>\n\n"
        "type /cancel to detach from Persona, and press /start to return to main menu.",
        parse_mode=ParseMode.HTML
    )

    return CHAT

# === CREATE BLOCK ENDS ===
# === DELETE BLOCK STARTS ===
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    UserID = user['id']
    ToDelete = str(update.message.text)

    if update.message.text in collection.find_one({"_id": UserID}):
        collection.update_one({"_id": UserID}, {"$unset": {ToDelete: ""}})
        
        reply = ToDelete + " has been Deleted."

        await update.message.reply_text(
            reply, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove()
        )
        reply_keyboard_cancel = [["/cancel"]]
        await context.bot.send_message(text="Restart the Bot to return to menu. /cancel", chat_id=UserID, reply_markup=ReplyKeyboardMarkup(
                reply_keyboard_cancel, input_field_placeholder="Restart the Bot"
                ), parse_mode=ParseMode.HTML)
# === DELETE BLOCK ENDS ===
# === LOAD BLOCK START ===

# TODO CHARLOADING - For each item in collection, display button. If button pressed, mark Collection key:value with current selection. Query in loadBio later.
async def charload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    user = update.message.from_user
    UserID = user['id']
    CharName = update.message.text
    collection.update_one({"_id": UserID}, {"$set": {"SelectedPersona": update.message.text}})
    print(CharName)
    reply = "<strong>"+ CharName + " is ready.</strong>\nNow start your conversation.\n\n<strong>Talk to it like you would to a real human!</strong>\n\n<strong>You may narrate, or ask the persona to narrate: actions, activites, change of context, during the conversation.</strong>\n\n<strong>You can ask the Persona for actions by using the 'describe' or 'narrate' keyword. By asking, for example: 'Describe what will you do next?'</strong>\n\ntype /cancel to detach from Persona, and press /start to return to main menu."

    logger.info("User %s loading Personas. LIST OF PERSONAS:")

    await update.message.reply_text(
        reply, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove()
    )

    return CHATFROMLOAD

# WRITE CHATFROMLOAD
async def chatfromload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    UserID = user['id']
    # FETCH COLLECTION FOR TG USER ID
    document = collection.find_one({"_id": UserID})
    # GET SELECTED PERSONA DATA

    SelectedPersona = document["SelectedPersona"]
    CharDataDict = document[SelectedPersona]
    CharProfile = []
    CharProfile.append(SelectedPersona)
    for item in CharDataDict:
        CharProfile.extend(item.values())


    if not "ChatCount" in document:
        print("CHATCOUNT:::", document)
        collection.update_one({"_id": UserID}, {"$inc": {"ChatCount": 1}}, upsert=True)
    elif document["ChatCount"] < FREE_CHAT_LIMIT or "PaidDate" in document:
        collection.update_one({"_id": UserID}, {"$inc": {"ChatCount": 1}}, upsert=True)
    else:
        buy_keyboard = [["/buy"]]
        await update.effective_message.reply_html(
            "Chat limit reached. /buy to get unlimited access.\n", reply_markup=ReplyKeyboardMarkup(
                buy_keyboard, input_field_placeholder="/buy"))
        return 
    
    logger.info("\nTALKING WITH PERSONA PROFILE :: %s", CharProfile)

    async with websockets.connect('ws://34.116.221.94:7860/queue/join') as websocket:

        # TODO implement hashids bound to user id. id -> hashid -> hashid2
        
        response = await websocket.recv()
        if response:
            await websocket.send(json.dumps({
                'session_hash':CharProfile[4],
                'fn_index':3
            }))
            time.sleep(3)
            response = await websocket.recv()
            response = await websocket.recv()

            if response:
                # DYNAMIC DATA FROM USER: None, None, message, None
                # THEN DATA FROM PERSONA: char name, your name, char persona, char greet, scenario, example chat 

                await websocket.send(json.dumps({
                    "fn_index":3,
                    "data":[None,None,update.message.text,None,CharProfile[0],CharProfile[1],CharProfile[2],"Hello",CharProfile[3],None],
                    "session_hash":CharProfile[4]
                }))
                response = await websocket.recv()

                if json.loads(response)['msg'] == 'process_starts':
                    
                    response = await websocket.recv()
                    
                    response = json.loads(response)
                    
                    AIResponseRaw = response["output"]["data"][3][-1][-1]

                    regex = r"^[^<]+"
                    AIResponse = re.sub(regex, "", AIResponseRaw, re.MULTILINE)
       
    await update.message.reply_text(AIResponse, parse_mode=ParseMode.HTML)
    
    return CHATFROMLOAD
# 
# === LOAD BLOCK ENDS ===
# TODO THE BELOW NEEDS A REFACTOR PRETTY BAD

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""

    user = update.message.from_user
    UserID = user['id']

    document = collection.find_one({"_id": UserID})
    CharName = document["SelectedPersona"]
    CharDataDict = document[CharName]
    CharProfile = []
    CharProfile.append(CharName)
    for item in CharDataDict:
        CharProfile.extend(item.values())
    
    print("CHARPROFILE::", CharProfile)

    # TODO CHECK NUMBER OF CHARS PRESENT
    # logger.info("CHARDATA: %s \n\n\nUser CHARDATA: %s", CharData, CharData[UserID])
    CharHash = "telegram"+"_111_"+str(UserID)+"_char"+CharName



    # === CHECK NUMBER OF AI CHAT RUNS ===
    document = collection.find_one({"_id": UserID})

    if not "ChatCount" in document:
        collection.update_one({"_id": UserID}, {"$inc": {"ChatCount": 1}}, upsert=True)
    elif document["ChatCount"] < FREE_CHAT_LIMIT or "PaidDate" in document:
        collection.update_one({"_id": UserID}, {"$inc": {"ChatCount": 1}}, upsert=True)
    else:
        buy_keyboard = [["/buy"]]
        await update.effective_message.reply_html(
            "Chat limit reached. /buy to get unlimited access and support the project.\n", reply_markup=ReplyKeyboardMarkup(
                buy_keyboard, input_field_placeholder="/buy"))
        return 

    # PaidDate
    # === SET ACTIVE SELECTED PERSONA FOR USER ===
    # collection.update_one({"_id": UserID}, {"$set": {"SelectedPersona": CharName}})
    if document is not None:
        array = document.get(CharName)
        if array is not None:
            if any(x.get("CharHash") == CharHash for x in array):
                print("CHARHASH already present for Persona")
            else:
                collection.update_one({"_id": UserID}, {"$push": {CharName: dict({"CharHash": CharHash})}}, upsert=True)
        else:
            print("Array not found.")
    else:
        print("Document not found.")
    # document = collection.find_one({"_id": UserID})
    # print("DOCUMENT:", document)
    # if document is not None and len(document[CharName]) < 4:
    #     collection.update_one({"_id": UserID}, {"$push": {CharName: {"$each": {"CharHash": CharHash}}}})
    # else:
    #     pass
    
    logger.info("Bio of %s: %s", CharHash, CharProfile)

    async with websockets.connect('ws://34.116.221.94:7860/queue/join') as websocket:

        # TODO implement hashids bound to user id. id -> hashid -> hashid2
        
        response = await websocket.recv()
        if response:
            await websocket.send(json.dumps({
                'session_hash':CharHash,
                'fn_index':3
            }))
            time.sleep(3)
            response = await websocket.recv()
            response = await websocket.recv()

            if response:
                # DYNAMIC DATA FROM USER: None, None, message, None
                # THEN DATA FROM PERSONA: char name, your name, char persona, char greet, scenario, example chat 
                
                await websocket.send(json.dumps({
                    "fn_index":3,
                    "data":[None,None,update.message.text,None,CharProfile[0],CharProfile[1],CharProfile[2],"Hello",CharProfile[3],None],
                    "session_hash":CharHash
                }))
                response = await websocket.recv()

                if json.loads(response)['msg'] == 'process_starts':
                    
                    response = await websocket.recv()
                    
                    print("final: ",response)
                    
                    response = json.loads(response)
                    
                    AIResponseRaw = response["output"]["data"][3][-1][-1]
                    regex = r"^[^<]+"
                    AIResponse = re.sub(regex, "", AIResponseRaw, re.MULTILINE)

    await update.message.reply_text(AIResponse, parse_mode=ParseMode.HTML)
    
    return CHAT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Stopped. To start Persona Bot again /start", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# === PAYMENTS ===
async def start_without_shipping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an invoice without shipping-payment."""
    chat_id = update.message.chat_id
    title = "Pay for Persona Forge AI - Full Access"
    description = "Full Access Usage of Persona Forge AI."
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    currency = "USD"
    # price in dollars
    price = 5
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Persona Forge AI", (price*100)-1)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    await context.bot.send_invoice(
        chat_id, title, description, payload, STRIPE_TOKEN, currency, prices
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != "Custom-Payload":
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)

# finally, after contacting the payment provider...
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("AFTER PAYMENT:::", update.message.from_user)
    UserID = update.message.from_user['id']
    document = collection.find_one({"_id": UserID})
    if not "PaidDate" in document:

        time = datetime.now()
        collection.update_one({"_id": UserID}, {"$set": {"PaidDate": time}}, upsert=True)

    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    await update.message.reply_text("Thank you for your payment and support! 😍\n\n Limits lifted!")

# === PAYMENTS END ===

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    persistence = PicklePersistence(filepath="PersonaForgeBot")
    application = Application.builder().token(BOT_KEY).persistence(persistence).build()

    # Add conversation handler with the states CHARCREATE, CHARNAME, YOUNAME, AIPERSONA and CHAT
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHARCREATE: [CallbackQueryHandler(charcreate)],
            CHARLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, charload)],
            CHARNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, charname)],
            YOUNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, youname), CommandHandler("skip", skip_youname)],
            AIPERSONA: [MessageHandler(filters.TEXT & ~filters.COMMAND, aipersona), CommandHandler("skip", skip_aipersona)],
            SCENARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, scenario), CommandHandler("skip", skip_scenario)],
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat)],
            CHATFROMLOAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, chatfromload)],
            DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="conversation_handler",
        persistent=True,
    )

    application.add_handler(conv_handler)

    # === PAYMENT HANDLERS ===
    application.add_handler(CommandHandler("buy", start_without_shipping_callback))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))


    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    
    ascii_banner = pyfiglet.figlet_format("PersonaForge TG Client")
    print(ascii_banner)
    main()