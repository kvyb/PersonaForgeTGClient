"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
# TODO Add "Typing" UI effect before response. See other Github for this.
import websockets
import logging
import os
import pyfiglet
import asyncio
import json
import time
import re

from telegram import __version__ as TG_VER
from telegram.constants import ParseMode

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
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global dict to store data in telegram session
CharData = {}

CHARCREATE, CHARNAME, YOUNAME, AIPERSONA, SCENARIO, BIO = range(6)

# TODO set character info here:
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user what to do next"""
    reply_keyboard = [["Create", "Other"]]
    await update.message.reply_text(
        "<strong>Overseer Loaded</strong>\n\n"
        "Send  /cancel  to <u><strong>Stop</strong></u> Persona creation\n\n"
        "Press the <strong>Create</strong> button to make a new AI Persona\n\n\n"
        "Note:\n"
        "   - Overseer will bind and retain the character until compute server restart.\n"
        "   - Persona names cannot be shared between personas.\n"
        "   - Overseer will remember your Personas by their names until compute server restart.\n"
        "   - You can reconnect to a Persona by 'creating' with the Persona name, leaving all Persona setup fields blank.\n"
        "   - <strong>This AI is unmoderated and can be explicit. By continuing, you confirm that you are 18+.</strong>\n",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Create a Char"
        ), parse_mode=ParseMode.HTML,
    )
    return CHARCREATE


async def charcreate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Char Create mode"""
    user = update.message.from_user
    logger.info("Char CREATE mode: %s: %s", user.first_name, update.message.text)

    UserID = user['id']
    CharData.update({UserID: []})

    if update.message.text == "Create":
        await update.message.reply_text(
            "<strong>Overseer:</strong> Persona Creation / <i>Start</i>\n\n"
            "Name your Persona.",
            reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML,
        )
    return CHARNAME


async def charname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI character name"""
    user = update.message.from_user

    UserID = user['id']
    CharData[UserID].append(update.message.text)

    logger.info("Character name is: %s: %s", update.message.text, CharData)
    
    await update.message.reply_text(
        "What should the persona call you?\nOr send /skip."
    )

    return YOUNAME


async def skip_charname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """AI Character name"""
    user = update.message.from_user

    UserID = user['id']
    CharData[UserID].append('')

    logger.info("User %s did not send a charname.", user.first_name)
    await update.message.reply_text(
        "Ok, if you don't want to enter this value, enter what the Persona should call you."
    )

    return YOUNAME


async def youname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Name for user"""
    # user = update.message.from_user
    user = update.message.from_user

    UserID = user['id']
    CharData[UserID].append(update.message.text)

    logger.info("The AI will call you: %s", update.message.text)
    await update.message.reply_text(
        "Describe, in one plain text message, what the Persona is like.\n\n"
        "Note:\n"
        "   - Include physical, behavioural, and mental characteristics.\n"
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
    CharData[UserID].append('')

    logger.info("User %s did not send a name for himself", user.first_name)
    await update.message.reply_text(
        "Describe, in one plain text message, what the Persona is like.\n\n"
        "Note:\n"
        "   - Include physical, behavioural, mental, characteristics\n"
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
    CharData[UserID].append(update.message.text)

    logger.info("The AI persona will be based on: %s", update.message.text)
    await update.message.reply_text(
        "<strong>Overseer:</strong> Persona and User Encounter / <i>Setup</i>\n\n"
        "Describe, in one plain text message, the circumstances and context of the first encounter "
        "between you and the Persona.\n"
        "Or send /skip",
        parse_mode=ParseMode.HTML
    )
    return SCENARIO

async def skip_aipersona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Persona data for the AI gen."""
    user = update.message.from_user

    UserID = user['id']
    CharData[UserID].append('')

    logger.info("User %s did not send a persona.", user.first_name)
    await update.message.reply_text(
        "<strong>Overseer:</strong> Persona and User Encounter / <i>Setup</i>\n\n"
        "Describe, in one plain text message, the circumstances and context of the first encounter"
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
    CharData[UserID].append(update.message.text)

    logger.info("The scenario is: %s . AND whole Dict: %s", update.message.text, CharData)
    await update.message.reply_text(
        "<strong>Overseer:</strong> The persona is ready.\nNow start your conversation.\n\n<strong>Talk to it like you would to a real human</strong>\n\n"
        "<strong>You may narrate actions, activites, or change of context during the conversation. Format the words with <i>italic</>.</strong>\n\n"
        "<strong>You can ask the Persona for actions by using the 'describe' or 'narrate' keyword. By asking, for example: 'Describe what you will do next'</strong>\n\n"
        "type /cancel to detach Persona and create new Persona with /start",
        parse_mode=ParseMode.HTML
    )
    return BIO

async def skip_scenario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Scenario"""
    user = update.message.from_user

    UserID = user['id']
    CharData[UserID].append('')
    
    logger.info("User %s did not send a scenario.", user.first_name)
    await update.message.reply_text(
        "<strong>Overseer:</strong> The persona is ready.\nNow start your conversation.\n\n<strong>Talk to it like you would to a real human</strong>\n\n"
        "<strong>You may narrate actions, activites, or change of context during the conversation. Format the words with <i>italic</>.</strong>\n\n"
        "<strong>You can ask the Persona for actions by using the 'describe' or 'narrate' keyword. By asking, for example: 'Describe what you will do next'</strong>\n\n"
        "type /cancel to detach Persona and create new Persona with /start",
        parse_mode=ParseMode.HTML
    )

    return BIO


# TODO - Implement character create via http api. Limit to 1 available character.

async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""

    user = update.message.from_user
    UserID = user['id']

    # TODO CHECK NUMBER OF CHARS PRESENT
    CharHash = "telegram"+"_111_"+str(UserID)+"_char"+CharData[UserID][0]
    CharProfile = CharData[UserID]

    logger.info("Bio of %s: %s", CharHash, CharProfile)

    async with websockets.connect('ws://34.118.23.184:7860/queue/join') as websocket:

        # TODO implement hashids bound to user id. id -> hashid -> hashid2
        
        response = await websocket.recv()
        if response:
            await websocket.send(json.dumps({
                'session_hash':CharHash,
                'fn_index':3
            }))
            time.sleep(3)
            response = await websocket.recv()

            print(response)
            response = await websocket.recv()
            print(response)
            if response:
                # DYNAMIC DATA FROM USER: None, None, message, None
                # THEN DATA FROM PERSONA: char name, your name, char persona, char greet, scenario, example chat 
                await websocket.send(json.dumps({
                    "fn_index":3,
                    "data":[None,None,update.message.text,None,CharProfile[0],CharProfile[1],CharProfile[2],"Hello",CharProfile[3],None],
                    "session_hash":CharHash
                }))
                response = await websocket.recv()
                print(response)
                print(type(response))
                if json.loads(response)['msg'] == 'process_starts':
                    
                    response = await websocket.recv()
                    
                    print("final: ",response)
                    
                    response = json.loads(response)
                
                    AIResponse = response["output"]["data"][3][-1][-1]
                    AIResponse = re.sub("^[^<\w]+", "", str(AIResponse), count=1)
 
                    
    await update.message.reply_text(AIResponse, parse_mode=ParseMode.HTML)
    
    return BIO


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Goodbye.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6250262905:AAG_pFYEEdjvM2fqrldHHEduA2wmnuopSko").build()

    # Add conversation handler with the states CHARCREATE, CHARNAME, YOUNAME, AIPERSONA and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHARCREATE: [MessageHandler(filters.Regex("^(Create|Other)$"), charcreate)],
            CHARNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, charname), CommandHandler("skip", skip_charname)],
            YOUNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, youname), CommandHandler("skip", skip_youname)],
            AIPERSONA: [MessageHandler(filters.TEXT & ~filters.COMMAND, aipersona), CommandHandler("skip", skip_aipersona)],
            SCENARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, scenario), CommandHandler("skip", skip_scenario)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    
    ascii_banner = pyfiglet.figlet_format("PersonaForge TG Client")
    print(ascii_banner)
    main()