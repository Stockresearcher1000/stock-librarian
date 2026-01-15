# telegram_test.py
# Quick test to send a message to your Telegram

from telegram import Bot
import asyncio

# Replace these with your REAL values (same as in GitHub secrets)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"          # ← Paste your token
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"            # ← Paste your chat ID (number)

async def send_notification():
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        message = (
            "🔔 Quick Update from Stock Bot\n\n"
            "Scanned 2 stocks:\n"
            "- AMBER: No negative news found\n"
            "- ADANIENT: No negative news found\n\n"
            "All clear for now! 😊"
        )

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="Markdown"
        )

        print("✅ Message sent successfully! Check your Telegram now.")

    except Exception as e:
        print("❌ Failed to send message:")
        print(e)

# Run the async function
asyncio.run(send_notification())
