import os
import Filters
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler
import requests

# API Base URL
API_BASE_URL = " https://c892-218-111-149-235.ngrok-free.app"  # Replace with your Flask API's public URL

# Get Telegram Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

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

USER_RESPONSES = {}  # Store responses temporarily

# Start Command
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id, "Welcome! Please choose your desired role.")
    show_role_selection(update, context)

# Show Role Selection
def show_role_selection(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    roles = ["admin", "moderator", "user"]
    keyboard = [[InlineKeyboardButton(role.capitalize(), callback_data=f"role:{role}")] for role in roles]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id, "Select your role:", reply_markup=reply_markup)

# Handle Role Selection
def handle_role_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    chat_id = query.message.chat.id
    selected_role = query.data.split(":")[1]

    # Store selected role
    if chat_id not in USER_RESPONSES:
        USER_RESPONSES[chat_id] = {"role": selected_role}

    if selected_role == "user":
        # Directly register the user with the 'user' role
        register_user(chat_id, selected_role, update, context)
    else:
        # Ask the first question for the selected role
        ask_role_question(update, context, chat_id, selected_role, question_index=0)

# Ask Role-Specific Question
def ask_role_question(update: Update, context: CallbackContext, chat_id, role, question_index):
    question = ROLE_QUESTIONS[role][question_index]

    # Store current question index
    USER_RESPONSES[chat_id]["current_question"] = question_index

    context.bot.send_message(chat_id, question["text"])

# Handle User Answers
def handle_answer(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_response = update.message.text

    if chat_id not in USER_RESPONSES or "role" not in USER_RESPONSES[chat_id]:
        context.bot.send_message(chat_id, "Please restart by choosing a role using /start.")
        return

    role = USER_RESPONSES[chat_id]["role"]
    question_index = USER_RESPONSES[chat_id].get("current_question", 0)
    correct_answer = ROLE_QUESTIONS[role][question_index]["answer"]

    if user_response.strip().lower() == correct_answer.strip().lower():
        # Correct answer
        if question_index + 1 < len(ROLE_QUESTIONS[role]):
            # Ask the next question
            ask_role_question(update, context, chat_id, role, question_index + 1)
        else:
            # All questions answered correctly; register the user
            register_user(chat_id, role, update, context)
    else:
        # Incorrect answer
        context.bot.send_message(chat_id, "Incorrect answer. Please try again or choose a different role using /start.")

# Register User
def register_user(chat_id, role, update, context):
    username = update.effective_chat.username or "unknown_user"

    # Send user data to the Flask API
    response = requests.post(f"{API_BASE_URL}/users", json={"username": username, "chat_id": chat_id, "role": role})

    if response.status_code == 200:
        context.bot.send_message(chat_id, f"You have been successfully registered as a {role}!")
    else:
        context.bot.send_message(chat_id, f"An error occurred while registering your role: {response.json().get('error')}")

    # Clear temporary data
    USER_RESPONSES.pop(chat_id, None)

# Main Function
def main():
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role:"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
