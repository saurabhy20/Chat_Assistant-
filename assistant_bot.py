import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import openai

# ======================
# CONFIGURATION
# ======================
CONFIG = {
    "TELEGRAM_TOKEN": "7639863811:AAFpYst7CZ0i5xOQDjviV2PUbz7KnyPXjtQ",
    "OPENAI_API_KEY": "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",
    "ADMIN_USER_ID": 6009143798,
    "SYSTEM_PROMPT": "You are a Genius. Respond concisely and helpfully.",
    "MODEL": "gpt-4o",
    "MAX_HISTORY": 10,
    "TEMPERATURE": 0.7,
    "WELCOME_MESSAGE": "👋 Hello! I'm your SUZU☺️. How can I help you today?",
    "HELP_MESSAGE": (
        "🤖 <b>Mujhse Pange Na Lena</b>\n\n"
        "• Just chat with me normally samjhe\n"
        "• Bas Mujhe Ab Aur Kuchh Nahi Kahna\n"
        "• Use /help to see this message\n\n"
        "I remember the last {MAX_HISTORY} messages in our conversation."
    ),
    "RESPONDING_TO_OTHERS": True,
    "ERROR_NOTIFICATIONS": True
}

# ======================
# INITIALIZATION
# ======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
openai.api_key = CONFIG["OPENAI_API_KEY"]
conversations = {}

# ======================
# HELPER FUNCTIONS
# ======================
def get_conversation_history(chat_id):
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": CONFIG["SYSTEM_PROMPT"]}]
    return conversations[chat_id]

def update_conversation_history(chat_id, role, content):
    history = get_conversation_history(chat_id)
    history.append({"role": role, "content": content})
    if len(history) > CONFIG["MAX_HISTORY"] + 1:
        conversations[chat_id] = [history[0]] + history[-CONFIG["MAX_HISTORY"]:]

def clear_conversation_history(chat_id):
    conversations[chat_id] = [{"role": "system", "content": CONFIG["SYSTEM_PROMPT"]}]

async def generate_ai_response(history):
    try:
        response = await openai.ChatCompletion.acreate(
            model=CONFIG["MODEL"],
            messages=history,
            temperature=CONFIG["TEMPERATURE"]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "⚠️ Sorry, Mai Abhi Kuchh Soch Rahi Hu . Baad me baat krna."

# ======================
# TELEGRAM HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CONFIG["WELCOME_MESSAGE"])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = CONFIG["HELP_MESSAGE"].format(MAX_HISTORY=CONFIG["MAX_HISTORY"])
    await update.message.reply_text(help_msg, parse_mode="HTML")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_conversation_history(update.message.chat_id)
    await update.message.reply_text("🧹 Conversation history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id

    if not CONFIG["RESPONDING_TO_OTHERS"] and user_id != CONFIG["ADMIN_USER_ID"]:
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    update_conversation_history(chat_id, "user", message.text)
    history = get_conversation_history(chat_id)
    ai_response = await generate_ai_response(history)
    update_conversation_history(chat_id, "assistant", ai_response)
    await message.reply_text(ai_response)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if CONFIG["ERROR_NOTIFICATIONS"] and update and hasattr(update, "effective_chat"):
        error_text = (
            "⚠️ <b>Bot Error</b>\n\n"
            f"<code>{context.error}</code>\n\n"
            f"Chat ID: {update.effective_chat.id if update.effective_chat else 'N/A'}"
        )
        await context.bot.send_message(
            chat_id=CONFIG["ADMIN_USER_ID"],
            text=error_text,
            parse_mode="HTML"
        )

# ======================
# MAIN FUNCTION
# ======================
def main():
    application = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("AI Assistant Bot is running...")
    logger.info(f"Using model: {CONFIG['MODEL']}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
