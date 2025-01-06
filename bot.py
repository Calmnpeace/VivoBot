import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Telegram Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

API_BASE_URL = "https://c892-218-111-149-235.ngrok-free.app"  # Replace with your Flask API URL for user registration

USER_RESPONSES = {}

# Role-Specific Questions (same as before)
ROLE_QUESTIONS = {
    "admin": [
        {"text": "What is the database administrator's name?", "answer": "admin_name"},
        {"text": "What is the admin access key?", "answer": "admin_key"},
    ],
    "moderator": [
        {"text": "What is the moderator's passphrase?", "answer": "mod_pass"},
        {"text": "How many users are currently registered in the database?", "answer": "100"},
    ],
}

# Start Command
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await update.message.reply_text("Welcome! Please choose your desired role.")
    show_role_selection(update, context)

# Show Role Selection
def show_role_selection(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    roles = ["admin", "moderator", "user"]
    keyboard = [[InlineKeyboardButton(role.capitalize(), callback_data=f"role:{role}")] for role in roles]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, "Select your role:", reply_markup=reply_markup)

# Handle Role Selection
async def handle_role_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    selected_role = query.data.split(":")[1]

    # Store selected role
    if chat_id not in USER_RESPONSES:
        USER_RESPONSES[chat_id] = {"role": selected_role}

    if selected_role == "user":
        # Directly register the user with the 'user' role
        await register_user(chat_id, selected_role, update, context)
    else:
        # Ask the first question for the selected role
        await ask_role_question(update, context, chat_id, selected_role, question_index=0)

# Ask Role-Specific Question
async def ask_role_question(update: Update, context: CallbackContext, chat_id, role, question_index):
    question = ROLE_QUESTIONS[role][question_index]

    # Store current question index
    USER_RESPONSES[chat_id]["current_question"] = question_index

    await context.bot.send_message(chat_id, question["text"])

# Handle User Answers
async def handle_answer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_response = update.message.text

    if chat_id not in USER_RESPONSES or "role" not in USER_RESPONSES[chat_id]:
        await context.bot.send_message(chat_id, "Please restart by choosing a role using /start.")
        return

    role = USER_RESPONSES[chat_id]["role"]
    question_index = USER_RESPONSES[chat_id].get("current_question", 0)
    correct_answer = ROLE_QUESTIONS[role][question_index]["answer"]

    if user_response.strip().lower() == correct_answer.strip().lower():
        # Correct answer
        if question_index + 1 < len(ROLE_QUESTIONS[role]):
            # Ask the next question
            await ask_role_question(update, context, chat_id, role, question_index + 1)
        else:
            # All questions answered correctly; register the user
            await register_user(chat_id, role, update, context)
    else:
        # Incorrect answer
        await context.bot.send_message(chat_id, "Incorrect answer. Please try again or choose a different role using /start.")

# Register User
async def register_user(chat_id, role, update, context):
    username = update.effective_chat.username or "unknown_user"

    # Send user data to the Flask API
    response = requests.post(f"{API_BASE_URL}/users", json={"username": username, "chat_id": chat_id, "role": role})

    if response.status_code == 200:
        await context.bot.send_message(chat_id, f"You have been successfully registered as a {role}!")
    else:
        await context.bot.send_message(chat_id, f"An error occurred while registering your role: {response.json().get('error')}")

    # Clear temporary data
    USER_RESPONSES.pop(chat_id, None)

# Webhook setup
async def set_webhook(application: Application):
    webhook_url = f"{API_BASE_URL}/your-webhook-path"
    await application.bot.set_webhook(webhook_url)

# Main Function
def main():
    application = Application.builder().token(TOKEN).build()

    # Set webhook
    application.bot.set_webhook(f"{API_BASE_URL}/your-webhook-path")

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    # Run the webhook listener (without polling)
    application.run_webhook(listen="0.0.0.0", port=5000, url_path="/your-webhook-path")

if __name__ == "__main__":
    main()
