import os  
import asyncio
from datetime import datetime, timedelta
import finnhub
from groq import Groq
import telebot

# --- 1. CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- 2. THE 2026 HIGH-RISK EARNINGS CALENDAR ---
# Hardcoded for reliability (Based on Jan 2026 Exchange Filings)
EARNINGS_CALENDAR = {
    "2026-01-16": ["RELIANCE", "WIPRO", "TECHM", "CENTRALBK"],
    "2026-01-17": ["HDFCBANK", "ICICIBANK", "RBLBANK"],
    "2026-01-20": ["SRF", "UNITEDBNK", "PERSISTENT"],
    "2026-01-21": ["TATACOMM", "HINDPETRO"],
    "2026-01-22": ["INDIGO", "ZEEL", "COFORGE", "MPHASIS"], # <--- IndiGo Jan 22
    "2026-01-26": ["AXISBANK"],
}

# --- 3. COMPLETE NSE F&O STOCK UNIVERSE ---
STOCKS = {
    "AARTIIND": "Aarti Industries", "ABB": "ABB India", "ABBOTINDIA": "Abbott India",
    "ABCAPITAL": "Aditya Birla Cap", "ABFRL": "Aditya Birla Fashion", "ACC": "ACC Ltd",
    "ADANIENSOL": "Adani Energy", "ADANIENT": "Adani Ent", "ADANIGREEN": "Adani Green",
    "ADANIPORTS": "Adani Ports", "ALKEM": "Alkem Lab", "AMBER": "Amber Ent",
    "AMBUJACEM": "Ambuja Cement", "ANGELONE": "Angel One", "APLAPOLLO": "APL Apollo",
    "APOLLOHOSP": "Apollo Hosp", "APOLLOTYRE": "Apollo Tyre", "ASHOKLEY": "Ashok Leyland",
    "ASIANPAINT": "Asian Paints", "ASTRAL": "Astral Ltd", "ATUL": "Atul Ltd",
    "AUBANK": "AU Small Finance", "AUROPHARMA": "Aurobindo Pharma", "AXISBANK": "Axis Bank",
    "BAJAJ-AUTO": "Bajaj Auto", "BAJFINANCE": "Bajaj Finance", "BAJAJFINSV": "Bajaj Finserv",
    "BALKRISIND": "Balkrishna Ind", "BALRAMCHIN": "Balrampur Chini", "BANDHANBNK": "Bandhan Bank",
    "BANKBARODA": "Bank of Baroda", "BANKINDIA": "Bank of India", "BATAINDIA": "Bata India",
    "BEL": "Bharat Elec", "BERGEPAINT": "Berger Paints", "BHARATFORG": "Bharat Forge",
    "BHEL": "BHEL", "BPCL": "BPCL", "BHARTIARTL": "Bharti Airtel", "BIOCON": "Biocon",
    "BOSCHLTD": "Bosch", "BRITANNIA": "Britannia", "BSOFT": "Birlasoft", "CANBK": "Canara Bank",
    "CHOLAFIN": "Cholamandalam", "CIPLA": "Cipla", "COALINDIA": "Coal India",
    "COFORGE": "Coforge", "COLPAL": "Colgate", "CONCOR": "CONCOR", "CUMMINSIND": "Cummins",
    "DABUR": "Dabur", "DALBHARAT": "Dalmia Bharat", "DEEPAKNTR": "Deepak Nitrite",
    "DIVISLAB": "Divis Lab", "DIXON": "Dixon Tech", "DLF": "DLF", "DRREDDY": "Dr Reddys",
    "EICHERMOT": "Eicher Motors", "ESCORTS": "Escorts Kubota", "FEDERALBNK": "Federal Bank",
    "GAIL": "GAIL", "GLENMARK": "Glenmark", "GMRINFRA": "GMR Airports", "GRASIM": "Grasim",
    "HAL": "HAL", "HAVELLS": "Havells", "HCLTECH": "HCL Tech", "HDFCBANK": "HDFC Bank",
    "HDFCLIFE": "HDFC Life", "HEROMOTOCO": "Hero MotoCorp", "HINDALCO": "Hindalco",
    "HINDPETRO": "HPCL", "HINDUNILVR": "HUL", "ICICIBANK": "ICICI Bank", "ICICIGI": "ICICI Lombard",
    "IDFCFIRSTB": "IDFC First", "IEX": "IEX", "IGL": "IGL", "INDHOTEL": "Indian Hotels",
    "INDUSINDBK": "IndusInd Bank", "INDUSTOWER": "Indus Tower", "INFY": "Infosys",
    "IOC": "IOC", "IRCTC": "IRCTC", "ITC": "ITC", "JINDALSTEL": "Jindal Steel",
    "JSWSTEEL": "JSW Steel", "JUBLFOOD": "Jubilant Food", "KOTAKBANK": "Kotak Bank",
    "LT": "L&T", "LTIM": "LTIMindtree", "LTTS": "L&T Tech", "LUPIN": "Lupin",
    "M&M": "M&M", "M&MFIN": "M&M Finance", "MARICO": "Marico", "MARUTI": "Maruti Suzuki",
    "MCX": "MCX", "METROPOLIS": "Metropolis", "MPHASIS": "Mphasis", "MRF": "MRF",
    "MUTHOOTFIN": "Muthoot Finance", "NATIONALUM": "NALCO", "NAVINFLUOR": "Navin Fluorine",
    "NESTLEIND": "Nestle", "NMDC": "NMDC", "NTPC": "NTPC", "OBEROIRLTY": "Oberoi Realty",
    "ONGC": "ONGC", "PAGEIND": "Page Ind", "PEL": "Piramal Ent", "PERSISTENT": "Persistent Sys",
    "PETRONET": "Petronet LNG", "PFC": "PFC", "PIDILITIND": "Pidilite", "PIIND": "PI Industries",
    "PNB": "PNB", "POLYCAB": "Polycab", "POWERGRID": "PowerGrid", "PVRINOX": "PVR INOX",
    "RECLTD": "REC Ltd", "RELIANCE": "Reliance Ind", "SAIL": "SAIL", "SBICARD": "SBI Card",
    "SBILIFE": "SBI Life", "SBIN": "SBI", "SHREECEM": "Shree Cement", "SHRIRAMFIN": "Shriram Finance",
    "SIEMENS": "Siemens", "SRF": "SRF", "SUNPHARMA": "Sun Pharma", "SUNTV": "Sun TV",
    "SYNGENE": "Syngene", "TATACOMM": "Tata Comm", "TATACONSUM": "Tata Consumer",
    "TATAMOTORS": "Tata Motors", "TATAPOWER": "Tata Power", "TATASTEEL": "Tata Steel",
    "TCS": "TCS", "TECHM": "Tech Mahindra", "TITAN": "Titan", "TORNTPHARM": "Torrent Pharma",
    "TRENT": "Trent", "TVSMOTOR": "TVS Motor", "UBL": "UBL", "ULTRACEMCO": "UltraTech",
    "UNIONBANK": "Union Bank", "UPL": "UPL", "VEDL": "Vedanta", "VOLTAS": "Voltas",
    "WIPRO": "Wipro", "ZEEL": "ZEE Ent", "ZOMATO": "Zomato", "SWIGGY": "Swiggy",
    "INDIGO": "InterGlobe Aviation", "JIOFIN": "Jio Financial"
}

# --- 4. THE DETECTIVE (GROQ FUSION ROLE) ---
async def groq_forensic_audit(ticker, headline, summary):
    """
    Combines News Analysis + Forensic Auditing.
    Focuses on 'First Domino' events like Auditor Exits, NFRA, or Technical Glitches.
    """
    try:
        prompt = (
            f"Role: Forensic Financial Auditor & News Catalyst Analyst.\n"
            f"Current Year: 2026.\n"
            f"Analyze if this news for {ticker} is a 'First Domino' event for a major price drop.\n\n"
            f"Headline: '{headline}'\n"
            f"Summary: '{summary}'\n\n"
            f"CRITICAL TRIGGERS (Respond 'YES' if found):\n"
            f"1. Audit/Governance: NFRA inquiry, Auditor resignation, MGT-7/AOC-4 filing delays, Forensic audit.\n"
            f"2. Regulatory/Technical: DGCA grounded fleet (if Aviation), Technical glitch preventing trading/banking, SEBI Ban.\n"
            f"3. Management: Sudden CEO/CFO exit, Promoter pledge sell-off, Fraud allegations.\n"
            f"Respond ONLY with 'YES' or 'NO'."
        )
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0, # Maximum precision
        )
        return "YES" in completion.choices[0].message.content.strip().upper()
    except: return False

# --- 5. DATA GATHERER (FINNHUB) ---
async def fetch_and_analyze(ticker, name, semaphore):
    async with semaphore:
        try:
            # Check Earnings Calendar First
            today_str = datetime.now().strftime('%Y-%m-%d')
            if ticker in EARNINGS_CALENDAR.get(today_str, []):
                bot.send_message(CHAT_ID, f"📅 *EARNINGS ALERT:* {ticker} ({name}) reports today. Volatility expected.", parse_mode="Markdown")

            # Fetch News
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            news = finnhub_client.company_news(ticker, _from=yesterday, to=today)
            
            for item in news[:3]: # Scan top 3 recent items
                is_danger = await groq_forensic_audit(ticker, item['headline'], item.get('summary', ''))
                if is_danger:
                    msg = (f"🕵️‍♂️ *FORENSIC ALERT: NEGATIVE CATALYST*\n\n"
                           f"*Stock:* {ticker}\n"
                           f"*Event:* {item['headline']}\n"
                           f"*Source:* {item['source']}\n"
                           f"🔗 [Full Report]({item['url']})")
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    return True
            
            await asyncio.sleep(1.1) # Respect Finnhub 60/min limit
            return False
        except Exception as e:
            if "429" in str(e): await asyncio.sleep(15)
            return False

# --- 6. EXECUTION ENGINE ---
async def run_scan():
    print(f"🕵️‍♂️ Detective starting the shift at {datetime.now()}...")
    sem = asyncio.Semaphore(1) 
    
    tasks = [fetch_and_analyze(t, n, sem) for t, n in STOCKS.items()]
    results = await asyncio.gather(*tasks)
    
    alerts = sum(1 for r in results if r)
    bot.send_message(CHAT_ID, f"🏁 *Scan Complete*\nStocks Audited: {len(STOCKS)}\nDominoes Found: {alerts}", parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(run_scan())
