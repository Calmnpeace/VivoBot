import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, CallbackContext, filters

# API Base URL for Flask API
API_BASE_URL = "https://c892-218-111-149-235.ngrok-free.app"  # Replace with your Flask API URL

# Get Telegram Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN1")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

# Role-Specific Questions
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

USER_RESPONSES = {}  # Temporarily stores user responses


# Start Command
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "Welcome! Please choose your desired role.")
    show_role_selection(update, context)


# Show Role Selection
async def show_role_selection(update: Update, context: CallbackContext):
    roles = ["admin", "moderator", "user"]
    keyboard = [[InlineKeyboardButton(role.capitalize(), callback_data=f"role:{role}")] for role in roles]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(update.effective_chat.id, "Select your role:", reply_markup=reply_markup)


# Handle Role Selection
async def handle_role_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    selected_role = query.data.split(":")[1]
    USER_RESPONSES[chat_id] = {"role": selected_role}

    if selected_role == "user":
        register_user(chat_id, selected_role, update, context)
    else:
        ask_role_question(update, context, chat_id, selected_role, question_index=0)


# Ask Role-Specific Questions
async def ask_role_question(update: Update, context: CallbackContext, chat_id, role, question_index):
    question = ROLE_QUESTIONS[role][question_index]
    USER_RESPONSES[chat_id]["current_question"] = question_index
    await context.bot.send_message(chat_id, question["text"])


# Handle User Answers
async def handle_answer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_response = update.message.text
    role_data = USER_RESPONSES.get(chat_id)

    if not role_data:
        await context.bot.send_message(chat_id, "Please restart by choosing a role using /start.")
        return

    role = role_data["role"]
    question_index = role_data.get("current_question", 0)
    correct_answer = ROLE_QUESTIONS[role][question_index]["answer"]

    if user_response.strip().lower() == correct_answer.strip().lower():
        if question_index + 1 < len(ROLE_QUESTIONS[role]):
            await ask_role_question(update, context, chat_id, role, question_index + 1)
        else:
            await register_user(chat_id, role, update, context)
    else:
        await context.bot.send_message(chat_id, "Incorrect answer. Please try again.")


# Register User in the Database
async def register_user(chat_id, role, update, context):
    username = update.effective_chat.username or "unknown_user"

    # Sending the user data to the Flask API
    response = requests.post(f"{API_BASE_URL}/users", json={"username": username, "chat_id": chat_id, "role": role})

    if response.status_code == 200:
        await context.bot.send_message(chat_id, f"You have been successfully registered as a {role}!")
    else:
        await context.bot.send_message(chat_id, f"Error: {response.json().get('error', 'Unknown error')}")

    USER_RESPONSES.pop(chat_id, None)


# Main Function to Start the Bot
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    application.run_polling()


if __name__ == "__main__":
    main()
