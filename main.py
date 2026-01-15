import asyncio
import os
import time
from telegram import Bot
from groq import Groq
from google import genai

# Load Environment Variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)
tg_bot = Bot(token=TELEGRAM_TOKEN)

# List of 200+ F&O Stocks (Example list - add all yours here)
STOCKS = ["AXISBANK", "SBIN", "RELIANCE", "ADANIENT", "TATASTEEL", "INFY", "TCS", "ICICIBANK"] 
BATCH_SIZE = 20

async def analyze_with_ai(prompt):
    """Tries Groq first, then Gemini if Groq fails."""
    try:
        # 1st Attempt: Groq (Llama 3.3)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"⚠️ Groq failed or limit hit: {e}. Switching to Gemini...")
        try:
            # 2nd Attempt: Gemini Fallback
            response = genai_client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt
            )
            return response.text
        except Exception as e2:
            return f"❌ Both APIs failed: {e2}"

async def main():
    for i in range(0, len(STOCKS), BATCH_SIZE):
        batch = STOCKS[i : i + BATCH_SIZE]
        prompt = f"Analyze these stocks for LATEST negative news or upcoming bearish events: {', '.join(batch)}. Report only those with high risk."
        
        print(f"🔍 Scanning batch {i//BATCH_SIZE + 1}...")
        result = await analyze_with_ai(prompt)
        
        if result and "No negative news" not in result:
            async with tg_bot:
                await tg_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🚨 *Bearish Alert* 🚨\n\n{result}", parse_mode="Markdown")
        
        time.sleep(10) # Safety pause between batches

if __name__ == "__main__":
    asyncio.run(main())
