"""
Daily Facts Bot — Telegram Bot
Sends short, interesting "did you know" facts on request or subscription.

Run locally:
    export BOT_TOKEN="your-token-from-botfather"
    python bot.py

Deployed on Railway, BOT_TOKEN is read from an environment variable you set
in the Railway dashboard (Variables tab) — never hard-code it in this file.
"""

import json
import logging
import os
import random
from datetime import time as dtime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"

# ---------------------------------------------------------------------------
# CONTENT LIBRARY — add new entries any time, no other code needs to change
# ---------------------------------------------------------------------------

FACTS = [
    "Honey never spoils — edible honey has been found in Egyptian tombs over 3,000 years old.",
    "Octopuses have three hearts, and two of them stop beating when the octopus swims.",
    "A day on Venus is longer than a year on Venus — it rotates slower than it orbits the sun.",
    "Bananas are berries, but strawberries aren't, botanically speaking.",
    "The Eiffel Tower grows about 15 cm taller in summer as the metal expands with heat.",
    "Sharks existed before trees — sharks are about 400 million years old, trees around 350 million.",
    "A single bolt of lightning contains enough energy to toast about 100,000 slices of bread.",
    "The shortest war in recorded history lasted about 38 minutes, between Britain and Zanzibar in 1896.",
    "Wombat droppings are cube-shaped, which stops them from rolling away and helps mark territory.",
    "There are more possible iterations of a chess game than atoms in the observable universe.",
    "The inventor of the Pringles can is partially buried in one, per his request.",
    "Sea otters hold hands while sleeping so they don't drift apart in the water.",
    "Hot water can freeze faster than cold water under certain conditions — a real, studied effect called the Mpemba effect.",
    "Scotland's national animal is the unicorn.",
    "The total weight of ants on Earth is estimated to roughly equal the total weight of all humans.",
]

WELCOME_MESSAGE = (
    "👋 Welcome!\n\n"
    "This bot sends you a short, interesting fact — one at a time, nothing else.\n\n"
    "Commands:\n"
    "/fact — get a random fact\n"
    "/subscribe — get a daily fact automatically\n"
    "/unsubscribe — stop daily facts\n"
    "/help — show this message again"
)

# ---------------------------------------------------------------------------
# SUBSCRIBER STORAGE
# ---------------------------------------------------------------------------


def load_subscribers() -> set:
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)


subscribers = load_subscribers()

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pick = random.choice(FACTS)
    await update.message.reply_text(f"💡 Did you know?\n\n{pick}")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        await update.message.reply_text("You're already subscribed to daily facts.")
        return
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text(
        "✅ Subscribed! You'll get one fact a day. Use /unsubscribe to stop anytime."
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        await update.message.reply_text("You're not currently subscribed.")
        return
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text("You've been unsubscribed from daily facts.")


async def send_daily_fact(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs once a day, sends one random fact to every subscriber."""
    if not subscribers:
        return
    pick = random.choice(FACTS)
    text = f"💡 Did you know?\n\n{pick}"
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it locally with `export BOT_TOKEN=...` or in Railway's Variables tab."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("fact", fact))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Daily fact at 09:00 UTC — adjust the hour to suit your audience's timezone.
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_fact, time=dtime(hour=9, minute=0))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
