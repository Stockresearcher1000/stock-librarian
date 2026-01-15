# main.py - Sentinax-FO Negative News Sentinel
# Updated: Changed Gemini model from gemini-1.5-flash → gemini-2.5-flash

import os
import time
import logging
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import google.generativeai as genai
from transformers import pipeline
from telegram import Bot
import asyncio

# -------------------------------
# CONFIGURATION
# -------------------------------

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Environment variables (set in GitHub Secrets)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validate required env vars
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in environment variables")
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logging.warning("Telegram credentials missing - alerts will be logged but not sent")

# Gemini setup - CHANGED MODEL HERE
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')   # ← Updated model name

# Sentiment pipeline (FinBERT)
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    device=-1  # CPU
)

# Stocks list (F&O stocks - example, replace with your full list)
STOCKS = [
    "360ONE", "ABB", "ABCAPITAL", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS",
    "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APLAPOLLO", "APOLLOHOSP", "ASHOKLEY",
    "ASIANPAINT", "ASTRAL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO",
    # ... add all ~200 stocks here ...
    "YESBANK", "ZEEL", "ZOMATO", "ZYDUSLIFE"
]

BATCH_SIZE = 5
SLEEP_BETWEEN_BATCHES = 10  # seconds
SLEEP_BETWEEN_STOCKS = 2   # seconds

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def get_gemini_summary(stock):
    """Get negative news summary using Gemini"""
    prompt = f"""
    Search recent news (last 24-48 hours) for {stock} (NSE: {stock}).
    Look specifically for negative events: fraud, penalty, probe, scam, lawsuit, regulatory action, default, insolvency, etc.
    If found, summarize in 2-3 sentences with source links if possible.
    If no negative news, return exactly: "No negative news found"
    """
    try:
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        logging.info(f"Gemini summary for {stock}: {text[:100]}...")
        return text
    except Exception as e:
        logging.error(f"Gemini error {stock}: {str(e)}")
        return "Gemini API failed"

def forum_agent(stock):
    """Scrape moneycontrol/forum or similar for negative mentions"""
    url = f"https://mmb.moneycontrol.com/forum-topics/stocks/{stock.lower()}/thread-message-1.html"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "Forum page not accessible"

        soup = BeautifulSoup(resp.text, features='lxml')  # explicit
        posts = soup.find_all('div', class_='post')
        negative_mentions = []
        for post in posts[:10]:  # last 10 posts
            text = post.get_text(strip=True).lower()
            if any(word in text for word in ['fraud', 'scam', 'penalty', 'probe', 'default', 'insolvency']):
                negative_mentions.append(text[:200])
        if negative_mentions:
            return "\n".join(negative_mentions)
        return "No negative forum mentions"
    except Exception as e:
        logging.error(f"Forum error {stock}: {str(e)}")
        return "Forum scrape failed"

def get_rss_negative(stock):
    """RSS search for negative keywords"""
    keywords = "fraud OR penalty OR probe OR scam OR lawsuit OR negative"
    query = f"{stock} {keywords}"
    url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, 'xml')
        items = soup.find_all('item')
        negatives = []
        for item in items[:5]:
            title = item.title.text.lower()
            if any(kw in title for kw in ['fraud', 'scam', 'penalty', 'probe']):
                negatives.append(item.title.text)
        if negatives:
            return "\n".join(negatives)
        return "No negative RSS hits"
    except Exception as e:
        logging.error(f"RSS error {stock}: {str(e)}")
        return "RSS failed"

def analyze_sentiment(text):
    """FinBERT sentiment on combined text"""
    if not text or len(text.strip()) < 20:
        return "neutral", 0.0

    # Truncate to avoid token limit (FinBERT max ~512 tokens)
    truncated = text[:2000]
    result = sentiment_pipeline(truncated)[0]
    label = result['label'].lower()
    score = result['score']

    if label == 'negative' and score > 0.75:
        return "negative", score
    return "neutral", score

async def send_telegram_alert(text):
    """Send alert to Telegram (async)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.info(f"Would send alert: {text[:100]}...")
        return

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        logging.info("Alert sent")
    except Exception as e:
        logging.error(f"Telegram send failed: {str(e)}")

# -------------------------------
# MAIN SCAN LOGIC
# -------------------------------

async def scan_batch(batch):
    alerts = []
    for stock in batch:
        logging.info(f"Processing {stock}")

        # Step 1: Gemini summary
        gemini_result = get_gemini_summary(stock)

        # Step 2: Forum mentions
        forum_result = forum_agent(stock)

        # Step 3: RSS negative
        rss_result = get_rss_negative(stock)

        # Combine
        combined = f"Gemini: {gemini_result}\nForum: {forum_result}\nRSS: {rss_result}"

        # Step 4: Sentiment
        sentiment_label, sentiment_score = analyze_sentiment(combined)

        if sentiment_label == "negative":
            alert_text = f"""
<b>NEGATIVE ALERT: {stock}</b>

Score: {sentiment_score:.2f}
Gemini: {gemini_result}
Forum: {forum_result[:300]}
RSS: {rss_result[:300]}
"""
            alerts.append((stock, alert_text))
            await send_telegram_alert(alert_text)

        time.sleep(SLEEP_BETWEEN_STOCKS)

    return alerts

def main():
    logging.info("Starting F&O Negative News Sentinel v1...")

    loop = asyncio.get_event_loop()

    while True:
        start_time = time.time()

        for i in range(0, len(STOCKS), BATCH_SIZE):
            batch = STOCKS[i:i + BATCH_SIZE]
            logging.info(f"Batch: {', '.join(batch)}")

            # Run async batch
            alerts = loop.run_until_complete(scan_batch(batch))

            if alerts:
                logging.info(f"Alerts: {[s[0] for s in alerts]}")

            time.sleep(SLEEP_BETWEEN_BATCHES)

        duration = time.time() - start_time
        logging.info(f"Scan done. Next in 30.0 min")
        time.sleep(1800)  # 30 minutes

if __name__ == "__main__":
    main()
