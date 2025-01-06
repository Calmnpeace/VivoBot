import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FLASK_API_URL = "https://9bef-218-111-149-235.ngrok-free.app"  # Replace with your ngrok URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Please choose your role: /admin, /moderator, /user")

async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = update.message.text.lstrip("/")
    chat_id = update.message.chat_id

    # Update role via Flask API
    response = requests.post(f"{FLASK_API_URL}/set_role", json={"chat_id": chat_id, "role": role})
    if response.status_code == 200:
        await update.message.reply_text(f"Your role has been set to {role}.")
    else:
        await update.message.reply_text("Failed to set role. Please try again.")

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    # Fetch permissions via Flask API
    response = requests.get(f"{FLASK_API_URL}/permissions", params={"chat_id": chat_id})
    if response.status_code == 200:
        permissions = response.json()
        await update.message.reply_text(f"Your access: {permissions}")
    else:
        await update.message.reply_text("Failed to fetch permissions. Please try again.")

application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler(["admin", "moderator", "user"], set_role))
application.add_handler(CommandHandler("check_access", check_access))

if __name__ == "__main__":
    application.run_polling()
