import os
import asyncio
from groq import Groq
from telegram import Bot

# 1. Setup - Ensure these are in your GitHub Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. Test List
TEST_STOCKS = ["GODFRYPHLP", "ITC", "RELIANCE", "SBIN", "ADANIENT", "ZOMATO", "TATASTEEL", "INFY", "HDFCBANK", "AXISBANK"]

async def test_notification():
    client = Groq(api_key=GROQ_API_KEY)
    bot = Bot(token=TELEGRAM_TOKEN)
    
    prompt = f"Identify any negative news from Jan 13-15, 2026, for these stocks: {', '.join(TEST_STOCKS)}. Focus on why markets are falling."
    
    print("🤖 AI is analyzing test stocks...")
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    
    report = chat_completion.choices[0].message.content
    
    print("📤 Sending to Telegram...")
    async with bot:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=f"🧪 *SENTINAX TEST NOTIFICATION*\n\n{report}",
            parse_mode="Markdown"
        )
    print("✅ Done! Check your Telegram.")

if __name__ == "__main__":
    asyncio.run(test_notification())
