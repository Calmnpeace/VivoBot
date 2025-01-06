import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# API Base URL
API_BASE_URL = "http://localhost:5000"  # Replace with your Flask API's URL (e.g., the URL of your local server)

# Telegram Bot Token from Environment Variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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

USER_RESPONSES = {}

# Start Command
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, "Welcome! Please choose your desired role.")
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

    if chat_id not in USER_RESPONSES:
        USER_RESPONSES[chat_id] = {"role": selected_role}

    if selected_role == "user":
        register_user(chat_id, selected_role, update, context)
    else:
        ask_role_question(update, context, chat_id, selected_role, question_index=0)

# Ask Role-Specific Question
def ask_role_question(update: Update, context: CallbackContext, chat_id, role, question_index):
    question = ROLE_QUESTIONS[role][question_index]
    USER_RESPONSES[chat_id]["current_question"] = question_index
    context.bot.send_message(chat_id, question["text"])

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
        if question_index + 1 < len(ROLE_QUESTIONS[role]):
            ask_role_question(update, context, chat_id, role, question_index + 1)
        else:
            register_user(chat_id, role, update, context)
    else:
        await context.bot.send_message(chat_id, "Incorrect answer. Please try again or choose a different role using /start.")

# Register User in the API
def register_user(chat_id, role, update, context):
    username = update.effective_chat.username or "unknown_user"

    response = requests.post(f"{API_BASE_URL}/users", json={"username": username, "chat_id": chat_id, "role": role})

    if response.status_code == 200:
        context.bot.send_message(chat_id, f"You have been successfully registered as a {role}!")
    else:
        context.bot.send_message(chat_id, f"An error occurred while registering your role: {response.json().get('error')}")

    USER_RESPONSES.pop(chat_id, None)

# Main Function
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    application.run_polling()

if __name__ == "__main__":
    main()
