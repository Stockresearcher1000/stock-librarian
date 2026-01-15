Pythonimport time
import re
import threading
import sqlite3
import logging
from google.generativeai import GenerativeModel
import google.generativeai as genai
from google.generativeai.types import GenerateContentConfig, Tool
import requests
from bs4 import BeautifulSoup
import feedparser
from telegram import Bot  # pip install python-telegram-bot
from transformers import pipeline  # pip install transformers torch

# Scan interval (seconds; 1800 = 30 min, 3600 = 1 hour)
SCAN_INTERVAL = 1800

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize SQLite for de-duping seen alerts
DB_FILE = 'sentinel_alerts.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS seen_alerts (hash TEXT PRIMARY KEY)')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

def is_seen(hash_str):
    cursor.execute("SELECT 1 FROM seen_alerts WHERE hash = ?", (hash_str,))
    return cursor.fetchone() is not None

def mark_seen(hash_str):
    cursor.execute("INSERT OR IGNORE INTO seen_alerts (hash) VALUES (?)", (hash_str,))
    conn.commit()

# Latest NSE F&O stock symbols (snapshot as of Jan 2026; ~202 symbols, sorted)
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
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Agent Classes for Collaboration (free, modular)
class GeminiAgent:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = GenerativeModel('gemini-1.5-flash')  # Fast model

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
            response = self.model.generate_content(
                prompt,
                generation_config=GenerateContentConfig(tools=[Tool(functions={'google_search': Tool.Function()})])
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
        is_negative = result['label'] == 'negative' and result['score'] > 0.7
        return is_negative, result['score']

class RSSNewsAgent:
    def search(self, stock):
        rss_urls = [
            f"https://news.google.com/rss/search?q={stock}+fraud+penalty+probe+scam+lawsuit+negative+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
            f"https://www.moneycontrol.com/rss/MCtopnews.xml",
            f"https://economictimes.indiatimes.com/rssfeedsdefault.cms"
        ]
        results = []
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    if stock.lower() in entry.title.lower() or stock.lower() in entry.get('description', '').lower():
                        results.append(f"{entry.title} - {entry.link}")
            except Exception as e:
                logging.error(f"RSS error for {stock}: {e}")
        return "\n".join(results) if results else "NULL"

class ForumAgent:
    def search(self, stock):
        forum_queries = [
            f"https://www.reddit.com/search.rss?q={stock}+negative+rumor+scam+fraud&sort=new",
            f"https://stocktwits.com/symbol/{stock}/rss" if stock else ""
        ]
        results = []
        for url in forum_queries:
            if not url: continue
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')[:5]
                for item in items:
                    title = item.find('title').text if item.find('title') else ""
                    link = item.find('link').text if item.find('link') else ""
                    if any(kw in title.lower() for kw in ['fraud', 'scam', 'probe', 'negative']):
                        results.append(f"{title} - {link}")
            except Exception as e:
                logging.error(f"Forum error for {stock}: {e}")
        return "\n".join(results) if results else "NULL"

class LawsuitAgent:
    def search(self, stock):
        query = f"{stock} lawsuit hearing date penalty SEBI ED CBI site:gov.in OR site:courtlistener.com OR site:supremecourt.gov.in after:2026-01-01"
        try:
            response = requests.get(f"https://www.google.com/search?q={requests.utils.quote(query)}", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if 'http' in a['href']][:3]
            return "\n".join(links) if links else "NULL"
        except Exception as e:
            logging.error(f"Lawsuit error for {stock}: {e}")
            return "NULL"

class DateExtractionAgent:
    def extract(self, text):
        text = text.lower()
        patterns = [
            r'\b(\d{1,2}[-/ ]\w{3,9}[-/ ]\d{4})\b',
            r'\b(\w{3,9} \d{1,2},? \d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'next \w+ (hearing|trial|judgment|date)',
            r'expected by \d{4}-\d{2}-\d{2}'
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))
        future_dates = [d for d in dates if int(d.split()[-1]) >= 2026]
        return ', '.join(set(future_dates)) if future_dates else None

def process_batch(stock_group):
    gemini_agent = GeminiAgent()
    sentiment_agent = SentimentAgent()
    rss_agent = RSSNewsAgent()
    forum_agent = ForumAgent()
    lawsuit_agent = LawsuitAgent()
    date_agent = DateExtractionAgent()

    def gemini_thread(result):
        result['gemini'] = gemini_agent.search(stock_group)

    def rss_thread(result, stock):
        result['rss'] = rss_agent.search(stock)

    def forum_thread(result, stock):
        result['forum'] = forum_agent.search(stock)

    def lawsuit_thread(result, stock):
        result['lawsuit'] = lawsuit_agent.search(stock)

    reports = {}
    for stock in stock_group:
        result = {}
        threads = [
            threading.Thread(target=gemini_thread, args=(result,)),
            threading.Thread(target=rss_thread, args=(result, stock)),
            threading.Thread(target=forum_thread, args=(result, stock)),
            threading.Thread(target=lawsuit_thread, args=(result, stock))
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        combined_text = "\n".join([result.get(k, '') for k in ['gemini', 'rss', 'forum', 'lawsuit']])
        if combined_text.strip().upper() == "NULL" or not combined_text.strip():
            continue

        is_negative, score = sentiment_agent.analyze(combined_text)
        if is_negative:
            report = f"🚨 Multi-Agent Alert for {stock}:\n{combined_text}\n🤖 Sentiment: Negative (Score: {score:.2f})"
            dates = date_agent.extract(combined_text)
            if dates:
                report += f"\n🗓 Upcoming Dates: {dates}"
            if score > 0.95:
                report += "\n🔥 HIGH IMPACT DETECTED!"

            report_hash = str(hash(report))
            if not is_seen(report_hash):
                send_telegram_alert(report)
                mark_seen(report_hash)
                reports[stock] = report

    return reports

def send_telegram_alert(report):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=report)
        logging.info("Alert sent successfully")
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

def main():
    logging.info("🔎 Starting F&O Negative News Sentinel v1...")
    while True:
        for stock_group in chunks(STOCKS, 5):
            logging.info(f"Processing batch: {', '.join(stock_group)}")
            reports = process_batch(stock_group)
            if reports:
                logging.info(f"Alerts generated for {list(reports.keys())}")
            time.sleep(10)

        logging.info(f"Full scan complete. Next in {SCAN_INTERVAL / 60} min...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
