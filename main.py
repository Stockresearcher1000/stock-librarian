import os
import requests
import time  # New: This allows the robot to wait
from google import genai

# Pulling secrets from GitHub
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Your list of stocks
STOCKS = ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "SBIN", "INFY"] 

client = genai.Client(api_key=GEMINI_KEY)

def check_stock(stock):
    try:
        # 1. Grab news
        url = f"https://news.google.com/rss/search?q={stock}+stock+news+last+24h"
        response = requests.get(url)
        
        # 2. Ask AI to analyze
        prompt = f"Analyze these headlines for {stock}. If there is major negative news (fraud, crash, heavy loss), reply 'ALERT: [Reason]'. Otherwise reply 'SKIP'. News: {response.text[:2000]}"
        
        response_ai = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        ai_msg = response_ai.text
        
        # 3. Send Telegram if needed
        if "ALERT" in ai_msg.upper():
            msg = f"🚨 {stock} ALERT: {ai_msg}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
            
    except Exception as e:
        print(f"Error checking {stock}: {e}")

# This part runs the scan
for s in STOCKS:
    print(f"Checking {s}...")
    check_stock(s)
    time.sleep(4)  # This tells the robot to wait 4 seconds before the next stock
