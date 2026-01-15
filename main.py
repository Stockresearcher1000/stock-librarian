import asyncio
import os
from telegram import Bot

# FETCH from the environment (these must match the names in your .yml file)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

async def send_notification():
    # SAFETY CHECK: Ensure the secrets were actually loaded
    if not TELEGRAM_BOT_TOKEN or "YOUR_BOT" in TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN is missing or still a placeholder!")
        return
    if not TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_CHAT_ID is missing!")
        return

    try:
        # Initialize the bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        async with bot:  # Automatically handles initialize() and shutdown()
            message = (
                "🔔 *Quick Update from Stock Bot*\n\n"
                "Scanned 2 stocks:\n"
                "• AMBER: No negative news found\n"
                "• ADANIENT: No negative news found\n\n"
                "All clear for now! 😊"
            )

            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="Markdown"
            )

        print("✅ Message sent successfully! Check your Telegram now.")

    except Exception as e:
        print(f"❌ Failed to send message: {e}")

if __name__ == "__main__":
    asyncio.run(send_notification())
