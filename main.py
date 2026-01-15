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

# --- 2. COMPLETE NSE F&O STOCK UNIVERSE ---
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
    "JIOFIN": "Jio Financial"
}

# --- 3. THE RISK ANALYST FILTER ---
async def is_high_impact_negative(ticker, headline):
    """Uses Groq to filter strictly for catalysts of >= 2% price drops."""
    try:
        prompt = (
            f"Role: Senior Financial Risk Analyst.\n"
            f"Target: Identify specific NEGATIVE catalysts for {ticker} that could cause a 2% price drop.\n"
            f"Headline: '{headline}'\n\n"
            f"RULES:\n"
            f"- MUST be company-specific (fraud, lawsuit, fire, regulatory ban, huge earnings miss).\n"
            f"- NO generic sector news. NO marketing news. NO stock price updates.\n\n"
            f"Respond only with 'YES' or 'NO'."
        )
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return "YES" in completion.choices[0].message.content.strip().upper()
    except Exception:
        return False

# --- 4. EXECUTION ENGINE ---
async def run_scan():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    stocks_scanned = 0
    alerts_sent = 0
    start_time = datetime.now()

    print(f"🚀 Starting High-Impact Negative Catalyst Scan...")
    
    for ticker, name in STOCKS.items():
        try:
            stocks_scanned += 1
            news = finnhub_client.company_news(ticker, _from=yesterday, to=today)
            
            for item in news[:2]:
                if await is_high_impact_negative(ticker, item['headline']):
                    msg = (
                        f"🚨 *CRITICAL NEGATIVE CATALYST*\n\n"
                        f"*Stock:* {ticker} ({name})\n"
                        f"*News:* {item['headline']}\n\n"
                        f"🔗 [View Source]({item['url']})"
                    )
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    alerts_sent += 1
                    await asyncio.sleep(1.2) # Avoid API rate limits
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")

    # --- 5. FINAL SUMMARY NOTIFICATION (Proof of Life) ---
    duration = (datetime.now() - start_time).seconds
    if alerts_sent == 0:
        summary = (
            f"✅ *Daily Scan Complete: All Clear*\n\n"
            f"• *Stocks Scanned:* {stocks_scanned}\n"
            f"• *Negative News Found:* None\n"
            f"• *Verdict:* No high-impact threats (>= 2% drop) detected.\n"
            f"• *Duration:* {duration}s"
        )
    else:
        summary = f"🏁 *Scan Complete:* {stocks_scanned} stocks checked. {alerts_sent} high-impact alerts sent."
    
    bot.send_message(CHAT_ID, summary, parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(run_scan())
