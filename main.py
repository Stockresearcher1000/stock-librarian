import asyncio
from telegram import Bot

# Replace these with your REAL values
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"

async def send_notification():
    # 1. Use an 'async with' block to handle initialization & shutdown automatically
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        async with bot:  # This line is CRITICAL for v20+ 
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
