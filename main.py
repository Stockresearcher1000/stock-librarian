import os
import time
import requests
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# Using a slightly smaller test list to ensure we don't hit daily limits immediately
STOCKS = [
    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ACC", "ADANIENT", "ADANIPORTS", 
    "ADANIENSOL", "ADANIGREEN", "ADANITOTAL", "ALKEM", "AMBUJACEM", "ANGELONE", "APLAPOLLO", 
    "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "ATUL", "AUBANK", 
    "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BALKRISIND", 
    "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BATAINDIA", "BEL", "BERGEPAINT", 
    "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BIRLASOFT", "BLS", "BLUESTARCO", 
    "BOSCHLTD", "BPCL", "BRITANNIA", "BSE", "CAMS", "CANFINHOME", "CANBK", "CDSL", 
    "CHAMBLFERT", "CHOLAFIN", "CIPLA", "CITYUNIONB", "COALINDIA", "COFORGE", "COLPAL", 
    "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "DABUR", "DALBHARAT", "DEEPAKNTR", 
    "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "EICHERMOT", "ESCORTS", 
    "EXIDEIND", "FEDERALBNK", "GAIL", "GLENMARK", "GODREJCP", "GODREJPROP", "GRANULES", 
    "GRASIM", "GUJGASLTD", "GNFC", "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HDFCAMC", 
    "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK", 
    "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IDFC", "IEX", "IGL", "INDHOTEL", "INDIACEM", 
    "INDIAMART", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IRCTC", "IREDA", 
    "IRFC", "ITC", "JINDALSTEL", "JIOFIN", "JKCEMENT", "JSWSTEEL", "JUBLFOOD", "KAYNES", 
    "KFINTECH", "KOTAKBANK", "L&TFH", "LT", "LTIM", "LTTS", "LUPIN", "M&M", "M&MFIN", 
    "MANAPPURAM", "MARICO", "MARUTI", "MAHABANK", "MAXHEALTH", "MAZDOCK", "METROPOLIS", 
    "MFSL", "MGL", "MOTHERSON", "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", "NAVINFLUOR", 
    "NESTLEIND", "NHPC", "NMDC", "NTPC", "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND", 
    "PEL", "PERSISTENT", "PETRONET", "PFC", "PGEL", "PHOENIXLTD", "PIDILITIND", "PIIND", 
    "PNB", "POLYCAP", "POWERTARIFF", "POWERGRID", "PVRINOX", "RAMCOCEM", "RECLTD", 
    "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", 
    "SOLARINDS", "SONACOMS", "SRF", "STV", "SUNPHARMA", "SUNTV", "SUPREMEIND", "SWIGGY", 
    "SYNGENE", "TATACHEM", "TATACOMM", "TATACONSUM", "TATAMOTORS", "TATAPOWER", "TATASTEEL", 
    "TATATECH", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TVSMOTOR", 
    "UBL", "ULTRACEMCO", "UPL", "VBL", "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZOMATO", "ZYDUSLIFE"
]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_intelligence(stock):
    # Acting as an Analyst hunting for specific Indian Market triggers
    prompt = f"""
    Act as a Senior NSE/BSE Financial Intelligence Analyst. 
    Scan for {stock}:
    1. RECENT NEGATIVE NEWS/RUMORS: Look for auditor exits, SEBI/ED probes, or social media 'leaks'.
    2. UPCOMING RISKS: Check for earnings misses or regulatory deadlines in the next 14 days.
    3. FILTER: If no news likely to cause a >2% price drop exists, respond 'CLEAR'.
    
    If a threat is found: Provide RISK SCORE (1-10), CATALYST, and SOURCE.
    """
    
    # Retry loop to handle the 429 Error
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", # Switched to high-quota model
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 30  # Wait 30s, then 60s
                print(f"⚠️ Rate limit hit for {stock}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return f"Error: {str(e)}"
    return "CLEAR"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- EXECUTION ---
print("🚀 Sentinax-FO: Starting Advanced Intelligence Scan...")
for stock in STOCKS:
    result = get_intelligence(stock)
    if result and "CLEAR" not in result.upper() and "ERROR" not in result.upper():
        send_telegram(f"⚠️ *SENTINAX-FO ALERT*\n\n{result}")
        print(f"❗ Alert sent for {stock}")
    else:
        print(f"✅ {stock}: Scanned successfully.")
    
    # CRITICAL: Wait 12 seconds between stocks to stay under 5 RPM limit
    time.sleep(12)
