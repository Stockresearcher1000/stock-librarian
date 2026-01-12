import os
import requests
import google.generativeai as genai

# These pull your secret passwords from the GitHub "Safe"
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# List of stocks to scan
STOCKS = ["RELIANCE", "TCS", "HDFCBANK", "INFY"] 

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def check_stock(stock):
    # 1. This grabs news from the internet
    url = f"https://news.google.com/rss/search?q={stock}+stock+news+last+24h"
    response = requests.get(url)
    
    # 2. This asks the AI to read the news
    prompt = f"Analyze these headlines for {stock}. If there is major negative news, reply 'ALERT: [Reason]'. Otherwise reply 'SKIP'. News: {response.text[:2000]}"
    ai_msg = model.generate_content(prompt).text
    
    # 3. If the AI finds something bad, it sends you a Telegram
    if "ALERT" in ai_msg.upper():
        msg = f"🚨 {stock} ALERT: {ai_msg}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})

# This runs the check for every stock in your list
for s in STOCKS:
    print(f"Checking {s}...")
    check_stock(s)
