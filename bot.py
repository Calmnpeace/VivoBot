import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FLASK_API_URL = "https://9bef-218-111-149-235.ngrok-free.app/api"

application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text("Welcome! Please choose your role: /admin, /moderator, /user")

async def admin_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard options"""
    chat_id = update.message.chat_id

    # Check if user is an admin via Flask API
    response = requests.get(f"{FLASK_API_URL}/permissions", params={"chat_id": chat_id})
    if response.status_code != 200 or "admin" not in response.json().get("role", ""):
        await update.message.reply_text("You are not authorized to access admin tasks.")
        return

    await update.message.reply_text(
        "Admin Tasks:\n"
        "1. /view_users - View all users\n"
        "2. /update_role <user_id> <new_role> - Update user role\n"
        "3. /delete_user <user_id> - Delete a user"
    )

async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all registered users"""
    chat_id = update.message.chat_id

    response = requests.get(f"{FLASK_API_URL}/users", json={"chat_id": chat_id})
    if response.status_code == 200:
        users = response.json()
        users_info = "\n".join([f"ID: {u['id']}, Username: {u['username']}, Role: {u['role']}" for u in users])
        await update.message.reply_text(f"Registered Users:\n{users_info}")
    else:
        await update.message.reply_text("Failed to retrieve users. Ensure you have admin access.")

async def update_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update a user's role"""
    chat_id = update.message.chat_id
    try:
        target_user_id, new_role = context.args
    except ValueError:
        await update.message.reply_text("Usage: /update_role <user_id> <new_role>")
        return

    response = requests.post(
        f"{FLASK_API_URL}/update_user_role",
        json={"chat_id": chat_id, "user_id": target_user_id, "role": new_role}
    )
    if response.status_code == 200:
        await update.message.reply_text("User role updated successfully.")
    else:
        await update.message.reply_text("Failed to update role. Ensure you have admin access.")

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a user"""
    chat_id = update.message.chat_id
    try:
        target_user_id = context.args[0]
    except IndexError:
        await update.message.reply_text("Usage: /delete_user <user_id>")
        return

    response = requests.delete(
        f"{FLASK_API_URL}/delete_user",
        json={"chat_id": chat_id, "user_id": target_user_id}
    )
    if response.status_code == 200:
        await update.message.reply_text("User deleted successfully.")
    else:
        await update.message.reply_text("Failed to delete user. Ensure you have admin access.")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("admin", admin_tasks))
application.add_handler(CommandHandler("view_users", view_users))
application.add_handler(CommandHandler("update_role", update_role))
application.add_handler(CommandHandler("delete_user", delete_user))

if __name__ == "__main__":
    application.run_polling()
