import time
import re
import threading
import sqlite3
import logging
import os
from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
import feedparser
from telegram import Bot
from transformers import pipeline

# ──────────────────────────────────────────────────────────────
# Load secrets from environment variables (GitHub Actions)
# ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in environment variables")
if not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_CHAT_ID is not set in environment variables")

HUGGINGFACE_MODEL = "ProsusAI/finbert"

SCAN_INTERVAL = 1800  # 30 minutes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLite for deduplication
DB_FILE = 'sentinel_alerts.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS seen_alerts (hash TEXT PRIMARY KEY)')
    conn.commit()
    return conn, c

conn, cursor = init_db()

def is_seen(h):
    cursor.execute("SELECT 1 FROM seen_alerts WHERE hash = ?", (h,))
    return cursor.fetchone() is not None

def mark_seen(h):
    cursor.execute("INSERT OR IGNORE INTO seen_alerts (hash) VALUES (?)", (h,))
    conn.commit()

# F&O stock list (update periodically if needed)
STOCKS = [
    "360ONE", "ABB", "ABCAPITAL", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ALKEM", "AMBER", "AMBUJACEM",
    "ANGELONE", "APLAPOLLO", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO",
    "BAJAJFINSV", "BAJAJHLDNG", "BAJFINANCE", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHARTIARTL",
    "BHEL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BPCL", "BRITANNIA", "BSE", "CAMS", "CANBK", "CDSL",
    "CGPOWER", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR", "CROMPTON", "CUMMINSIND", "DABUR",
    "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "ETERNAL", "EXIDEIND", "FEDERALBNK",
    "FORTIS", "GAIL", "GLENMARK", "GMRAIRPORT", "GODREJCP", "GODREJPROP", "GRASIM", "HAL", "HAVELLS", "HCLTECH",
    "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDPETRO", "HINDUNILVR", "HINDZINC", "HUDCO", "ICICIBANK",
    "ICICIGI", "ICICIPRULI", "IDEA", "IDFCFIRSTB", "IEX", "IIFL", "INDHOTEL", "INDIANB", "INDIGO", "INDUSINDBK",
    "INDUSTOWER", "INFY", "INOXWIND", "IOC", "IPCALAB", "IRCTC", "IREDA", "IRFC", "ITC", "JINDALSTEL",
    "JIOFIN", "JSWENERGY", "JSWSTEEL", "JUBLFOOD", "KALYANKJIL", "KAYNES", "KEI", "KFINTECH", "KOTAKBANK", "KPITTECH",
    "LAURUSLABS", "LICHSGFIN", "LICI", "LODHA", "LT", "LTF", "LTIM", "LUPIN", "M&M", "MANAPPURAM",
    "MANKIND", "MARICO", "MARUTI", "MAXHEALTH", "MAZDOCK", "MCX", "MFSL", "MGL", "MOTHERSON", "MPHASIS",
    "MRF", "MUTHOOTFIN", "NATIONALUM", "NAUKRI", "NBCC", "NESTLEIND", "NHPC", "NMDC", "NTPC", "NUVAMA",
    "NYKAA", "OBEROIRLTY", "OFSS", "OIL", "ONGC", "PAGEIND", "PATANJALI", "PAYTM", "PERSISTENT", "PETRONET",
    "PFC", "PGEL", "PHOENIXLTD", "PIDILITIND", "PIIND", "PNB", "PNBHOUSING", "POLICYBZR", "POLYCAB", "POWERGRID",
    "POWERINDIA", "PPLPHARMA", "PREMIERENE", "PRESTIGE", "RBLBANK", "RECLTD", "RELIANCE", "RVNL", "SAIL", "SAMMAANCAP",
    "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", "SRF", "SUNPHARMA",
    "SUNTV", "SUPREMEIND", "SUZLON", "SWIGGY", "SYNGENE", "TATACONSUM", "TATAELXSI", "TATAPOWER", "TATASTEEL", "TATATECH",
    "TCS", "TECHM", "TIINDIA", "TITAN", "TM PV", "TORNTPHARM", "TORNTPOWER", "TRENT", "TVSMOTOR", "ULTRACEMCO",
    "UNIONBANK", "UNITDSPR", "UNOMINDA", "UPL", "VBL", "VEDL", "VOLTAS", "WAAREEENER", "WIPRO", "YESBANK",
    "ZEEL", "ZOMATO", "ZYDUSLIFE"
]

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# ──────────────────────────────────────────────────────────────
# AGENTS
# ──────────────────────────────────────────────────────────────

class GeminiAgent:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def search(self, stock_group):
        stock_list_str = ", ".join(stock_group)
        prompt = f"""
You are an Omniscient Financial Forensic Auditor searching the whole internet.
Analyze these stocks for negative news/price crashes: {stock_list_str}.

TRIGGERS (global/Indian):
1. LEGAL/COURTS: Lawsuits, hearings, judgments (SEBI/SAT/Supreme Court, US SEC/EU, extract upcoming dates).
2. REGULATORY: Penalties, probes (ED/CBI/RBI/SEBI, international).
3. INSIDER/RUMORS: Resignations, audits, selling.
4. FORUMS/SOCIAL: Reddit, StockTwits, ValuePickr, X, Seeking Alpha for rumors/upcoming events.
5. UPCOMING: Forward-looking negatives (e.g., 'expected fine next month').

CRITERIA:
- Every potential negative mention (high-impact highlighted >5% fall, 95%+ confidence).
- English only; include links/sources.
- Extract dates.

FORMAT (per stock):
🚨 STOCK: [Name]
⚖️ CATALYST: [Details + link]
💥 IMPACT: [Expected fall]
📅 DATES: [Upcoming]
🧠 CONFIDENCE: [Level]
🌐 SOURCE: [e.g., Reuters/Reddit]
If none: NULL
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini error: {e}")
            return "NULL"

class SentimentAgent:
    def __init__(self):
        self.analyzer = pipeline("sentiment-analysis", model=HUGGINGFACE_MODEL)

    def analyze(self, text):
        if not text or text.upper() == "NULL":
            return False, 0.0
        result = self.analyzer(text)[0]
        is_neg = result['label'] == 'negative' and result['score'] > 0.7
        return is_neg, result['score']

class RSSNewsAgent:
    def search(self, stock):
        rss_urls = [
            f"https://news.google.com/rss/search?q={stock}+fraud+OR+penalty+OR+probe+OR+scam+OR+lawsuit+negative+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
            "https://www.moneycontrol.com/rss/MCtopnews.xml",
            "https://economictimes.indiatimes.com/rssfeedsdefault.cms"
        ]
        results = []
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    txt = (entry.title or '') + ' ' + (entry.get('description', '') or '')
                    if stock.lower() in txt.lower():
                        results.append(f"{entry.title} - {entry.link}")
            except Exception as e:
                logging.error(f"RSS error {stock}: {e}")
        return "\n".join(results) if results else "NULL"

class ForumAgent:
    def search(self, stock):
        queries = [
            f"https://www.reddit.com/search.rss?q={stock}+negative+OR+rumor+OR+scam+OR+fraud&sort=new",
            f"https://stocktwits.com/symbol/{stock}/rss" if stock else ""
        ]
        results = []
        for url in queries:
            if not url: continue
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, 'xml')
                items = soup.find_all('item')[:5]
                for item in items:
                    title = item.find('title').text if item.find('title') else ""
                    link = item.find('link').text if item.find('link') else ""
                    if any(k in title.lower() for k in ['fraud', 'scam', 'probe', 'negative']):
                        results.append(f"{title} - {link}")
            except Exception as e:
                logging.error(f"Forum error {stock}: {e}")
        return "\n".join(results) if results else "NULL"

class LawsuitAgent:
    def search(self, stock):
        q = f"{stock} lawsuit OR hearing OR date OR penalty OR SEBI OR ED OR CBI site:gov.in OR site:courtlistener.com OR site:supremecourt.gov.in after:2026-01-01"
        try:
            r = requests.get(f"https://www.google.com/search?q={requests.utils.quote(q)}", timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if 'http' in a['href']][:3]
            return "\n".join(links) if links else "NULL"
        except Exception as e:
            logging.error(f"Lawsuit error {stock}: {e}")
            return "NULL"

class DateExtractionAgent:
    def extract(self, text):
        text = text.lower()
        pats = [
            r'\b(\d{1,2}[-/ ]\w{3,9}[-/ ]\d{4})\b',
            r'\b(\w{3,9} \d{1,2},? \d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'next \w+ (hearing|trial|judgment|date)',
            r'expected by \d{4}-\d{2}-\d{2}'
        ]
        dates = []
        for p in pats:
            dates.extend(re.findall(p, text))
        future = [d for d in dates if '2026' in d or '2027' in d]
        return ', '.join(set(future)) if future else None

# ──────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ──────────────────────────────────────────────────────────────

def process_batch(stock_group):
    gemini = GeminiAgent()
    sentiment = SentimentAgent()
    rss = RSSNewsAgent()
    forum = ForumAgent()
    lawsuit = LawsuitAgent()
    dates = DateExtractionAgent()

    def gemini_t(r): r['gemini'] = gemini.search(stock_group)
    def rss_t(r, s): r['rss'] = rss.search(s)
    def forum_t(r, s): r['forum'] = forum.search(s)
    def lawsuit_t(r, s): r['lawsuit'] = lawsuit.search(s)

    reports = {}
    for stock in stock_group:
        res = {}
        ts = [
            threading.Thread(target=gemini_t, args=(res,)),
            threading.Thread(target=rss_t, args=(res, stock)),
            threading.Thread(target=forum_t, args=(res, stock)),
            threading.Thread(target=lawsuit_t, args=(res, stock))
        ]
        for t in ts: t.start()
        for t in ts: t.join()

        combined = "\n".join([res.get(k, '') for k in ['gemini','rss','forum','lawsuit'] if res.get(k)])
        if not combined.strip() or combined.strip().upper() == "NULL":
            continue

        is_neg, score = sentiment.analyze(combined)
        if is_neg:
            msg = f"🚨 Multi-Agent Alert for {stock}:\n{combined}\n🤖 Sentiment: Negative (Score: {score:.2f})"
            d = dates.extract(combined)
            if d: msg += f"\n🗓 Upcoming Dates: {d}"
            if score > 0.95: msg += "\n🔥 HIGH IMPACT DETECTED!"

            h = str(hash(msg))
            if not is_seen(h):
                send_alert(msg)
                mark_seen(h)
                reports[stock] = msg

    return reports

def send_alert(text):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        logging.info("Alert sent")
    except Exception as e:
        logging.error(f"Telegram error: {e}")

def main():
    logging.info("🔎 Starting F&O Negative News Sentinel v1...")
    while True:
        for group in chunks(STOCKS, 5):
            logging.info(f"Batch: {', '.join(group)}")
            reps = process_batch(group)
            if reps:
                logging.info(f"Alerts: {list(reps.keys())}")
            time.sleep(10)

        logging.info(f"Scan done. Next in {SCAN_INTERVAL/60} min")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
