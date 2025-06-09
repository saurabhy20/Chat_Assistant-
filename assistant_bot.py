import json
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
# CONFIGURATION (JSON)
# ======================
CONFIG = {
    "TELEGRAM_TOKEN": "7639863811:AAHQYHiKTJgjf6CHOg-8nLj9WUVATi8P6yo",
    "OPENAI_API_KEY": "sk-...XZQA",
    "ADMIN_USER_ID": 6009143798,  # Your Telegram user ID
    "SYSTEM_PROMPT": "You are a Genius. Respond concisely and helpfully.",
    "MODEL": "gpt-4-turbo",
    "MAX_HISTORY": 10,  # Number of messages to remember
    "TEMPERATURE": 0.7,
    "WELCOME_MESSAGE": "👋 Hello! I'm your SUZU☺️. How can I help you today?",
    "HELP_MESSAGE": (
        "🤖 <b>Mujhse Pange Na Lena</b>\n\n"
        "• Just chat with me normally samjhe\n"
        "• Bas Mujhe Ab Aur Kuchh Nahi Kahna\n"
        "• Use /help to see this message\n\n"
        "I remember the you last {MAX_HISTORY} messages in our conversation."
    ),
    "RESPONDING_TO_OTHERS": True,  # Whether to respond to non-admin users
    "ERROR_NOTIFICATIONS": True
}

# ======================
# INITIALIZATION
# ======================
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set up OpenAI
openai.api_key = CONFIG["OPENAI_API_KEY"]

# Conversation history storage
conversations = {}

# ======================
# HELPER FUNCTIONS
# ======================
def get_conversation_history(chat_id):
    """Retrieve conversation history for a chat"""
    if chat_id not in conversations:
        conversations[chat_id] = [
            {"role": "system", "content": CONFIG["SYSTEM_PROMPT"]}
        ]
    return conversations[chat_id]

def update_conversation_history(chat_id, role, content):
    """Update conversation history for a chat"""
    history = get_conversation_history(chat_id)
    history.append({"role": role, "content": content})
    
    # Trim history to maintain max length
    if len(history) > CONFIG["MAX_HISTORY"] + 1:  # +1 for system prompt
        conversations[chat_id] = [history[0]] + history[-CONFIG["MAX_HISTORY"]:]

def clear_conversation_history(chat_id):
    """Reset conversation history for a chat"""
    conversations[chat_id] = [
        {"role": "system", "content": CONFIG["SYSTEM_PROMPT"]}
    ]

async def generate_ai_response(history):
    """Generate AI response using OpenAI API"""
    try:
        response = await openai.AsyncOpenAI().chat.completions.create(
            model=CONFIG["MODEL"],
            messages=history,
            temperature=CONFIG["TEMPERATURE"]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "⚠️ Sorry, Mai Abhi Kuchh Soch Rahi Hu . Baad me baat krna."

# ======================
# TELEGRAM HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    await update.message.reply_text(CONFIG["WELCOME_MESSAGE"])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message when /help is issued."""
    help_msg = CONFIG["HELP_MESSAGE"].format(MAX_HISTORY=CONFIG["MAX_HISTORY"])
    await update.message.reply_text(help_msg, parse_mode="HTML")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history when /clear is issued."""
    clear_conversation_history(update.message.chat_id)
    await update.message.reply_text("🧹 Conversation history cleared!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate AI responses."""
    message = update.message
    chat_id = message.chat_id
    user_id = message.from_user.id
    
    # Ignore messages from other users if configured
    if not CONFIG["RESPONDING_TO_OTHERS"] and user_id != CONFIG["ADMIN_USER_ID"]:
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Update conversation history
    update_conversation_history(chat_id, "user", message.text)
    
    # Generate AI response
    history = get_conversation_history(chat_id)
    ai_response = await generate_ai_response(history)
    
    # Update history and send response
    update_conversation_history(chat_id, "assistant", ai_response)
    await message.reply_text(ai_response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and optionally send notification to admin."""
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    
    if CONFIG["ERROR_NOTIFICATIONS"]:
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
    """Start the bot."""
    # Create Application
    application = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # Message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("AI Assistant Bot is running...")
    logger.info(f"Using model: {CONFIG['MODEL']}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
