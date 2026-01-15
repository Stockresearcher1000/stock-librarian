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

# --- 3. THE ANALYST (GROQ) ---
async def groq_risk_analysis(ticker, headline):
    """Groq is the high-limit Brain. We can call this much faster."""
    try:
        prompt = (
            f"Role: Senior Financial Risk Analyst.\n"
            f"Identify if this headline for {ticker} is a catalyst for a >= 2% price drop.\n"
            f"Headline: '{headline}'\n"
            f"Respond 'YES' only if it is a major negative company-specific event (Fraud, Regulatory Ban, Huge Miss)."
        )
        # Using Groq's Llama 3.3 70B (High speed/limits)
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return "YES" in completion.choices[0].message.content.strip().upper()
    except: return False

# --- 4. THE DATA GATHERER (FINNHUB) ---
async def fetch_and_analyze(ticker, name, semaphore):
    """This function manages the Finnhub rate limit."""
    async with semaphore:
        try:
            # Finnhub is the slow employee (60 calls/min)
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            
            news = finnhub_client.company_news(ticker, _from=yesterday, to=today)
            
            for item in news[:2]:
                # Send the data to the high-speed Brain (Groq)
                if await groq_risk_analysis(ticker, item['headline']):
                    msg = f"🚨 *NEGATIVE CATALYST*\n\n*Stock:* {ticker}\n*News:* {item['headline']}\n🔗 [Link]({item['url']})"
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    return True
            
            # CRITICAL: Forces the script to wait 1.1s before the next Finnhub call
            await asyncio.sleep(1.1) 
            return False
        except Exception as e:
            if "429" in str(e):
                await asyncio.sleep(10) # Emergency cooling if we hit a wall
            return False

# --- 5. EXECUTION ENGINE ---
async def run_scan():
    print(f"🚀 Starting Stabilized Scan...")
    # This semaphore acts as the gatekeeper for Finnhub
    sem = asyncio.Semaphore(1) 
    
    tasks = [fetch_and_analyze(t, n, sem) for t, n in STOCKS.items()]
    results = await asyncio.gather(*tasks)
    
    alerts = sum(1 for r in results if r)
    bot.send_message(CHAT_ID, f"🏁 Scan Complete. {len(STOCKS)} checked. {alerts} alerts sent.", parse_mode="Markdown")

if __name__ == "__main__":
    asyncio.run(run_scan())
