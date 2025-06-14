import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import openai
import config

# API Keys
TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
OPENAI_API_KEY = config.OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

# Load sales prompt
with open("prompt.txt", "r", encoding="utf-8") as f:
    SALES_PROMPT = f.read()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# States
STATE_START = 0
STATE_WAITING_ACTIVITY = 1
STATE_WAITING_NAME = 2
STATE_WAITING_PHONE = 3

user_states = {}
user_data = {}

# Main Buttons
def get_main_buttons():
    keyboard = [
        [InlineKeyboardButton("💻 Créer mon site maintenant", callback_data="start_site")],
        [
            InlineKeyboardButton("📞 Être rappelé", callback_data="call_back"),
            InlineKeyboardButton("💬 Poser une question", callback_data="ask_question"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# OpenAI response
def ask_openai(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SALES_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logging.error(f"Erreur OpenAI: {e}")
        return "Je rencontre un petit souci technique. Essayons à nouveau 😊"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = STATE_START
    await update.message.reply_text(
        "Bienvenue 👋\nJe suis là pour vous accompagner dans la création de votre site web professionnel ou pour répondre à vos questions.\n\nCliquez sur l’un des boutons ci-dessous pour commencer 👇",
        reply_markup=get_main_buttons(),
    )

# Button interactions
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "start_site":
        user_states[user_id] = STATE_WAITING_ACTIVITY
        await query.edit_message_text("Parfait ! Quelle est votre activité ?")
    elif query.data == "call_back":
        user_states[user_id] = STATE_WAITING_PHONE
        await query.edit_message_text("Très bien. Donnez-moi votre numéro de téléphone.")
    elif query.data == "ask_question":
        user_states[user_id] = STATE_START
        await query.edit_message_text("Allez-y, posez-moi votre question. Je vous écoute 😊")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    state = user_states.get(user_id, STATE_START)

    if message.lower() in ["salut", "coucou", "bonjour", "hey"]:
        await update.message.reply_text(
            "Bonjour 👋 Je suis là pour vous accompagner dans la création de votre site web professionnel ou pour répondre à vos questions.\n\nCliquez sur l’un des boutons ci-dessous pour commencer 👇",
            reply_markup=get_main_buttons(),
        )
        return

    if any(word in message.lower() for word in ["prix", "coût", "combien"]):
        await update.message.reply_text(
            "💰 Le prix est simple :\n"
            "- 10 000 F CFA / mois la première année\n"
            "- Puis 40 000 F CFA / an via LWS\n\n"
            "Vous avez droit à 2 modifications gratuites par mois.\n"
            "C’est un pack complet avec site, design, email, SEO, nom de domaine, tout inclus.\n"
            "Et si vous arrêtez 2 mois de suite, l’hébergement sera suspendu."
        )
        return

    if state == STATE_WAITING_ACTIVITY:
        user_data[user_id] = {"activity": message}
        user_states[user_id] = STATE_WAITING_NAME
        await update.message.reply_text("Merci ! Quel est votre nom complet ?")
    elif state == STATE_WAITING_NAME:
        user_data[user_id]["name"] = message
        user_states[user_id] = STATE_WAITING_PHONE
        await update.message.reply_text("Parfait. Et votre numéro de téléphone ?")
    elif state == STATE_WAITING_PHONE:
        user_data[user_id]["phone"] = message
        data = user_data[user_id]
        await update.message.reply_text(
            f"Merci {data['name']} ! 🎉\n"
            f"Nous allons vous contacter très bientôt pour créer votre site de {data['activity']}.\n"
            "Préparez-vous à avoir un site professionnel, moderne, rapide, avec email, SEO et accompagnement personnalisé."
        )
        user_states[user_id] = STATE_START
    else:
        response = ask_openai(message)
        await update.message.reply_text(response, reply_markup=get_main_buttons())

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envoyez un message ou cliquez sur un bouton pour commencer.")

# Run bot
def main():
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        print("❌ Clés API manquantes. Vérifiez config.py.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot en ligne...")
    app.run_polling()

if __name__ == "__main__":
    main()
