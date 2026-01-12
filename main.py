import os
import requests
from google import genai
from google.genai import types

# --- CONFIGURATION ---
STOCKS = [

    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ACC", "ADANIENT", "ADANIPORTS", "ALKEM", "AMBUJACEM",

    "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO",

    "BAJAJFINSV", "BAJFINANCE", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG",

    "BHARTIARTL", "BHEL", "BIOCON", "BPCL", "BRITANNIA", "BSOFT", "CANBK", "CANFINHOME", "CHAMBLFERT", "CHOLAFIN",

    "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND", "DABUR",

    "DALBHARAT", "DEEPAKNTR", "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND",

    "FEDERALBNK", "GAIL", "GLENMARK", "GMRINFRA", "GNFC", "GODREJCP", "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL",

    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK",

    "ICICIGI", "ICICIPRULI", "IDFC", "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", "INDIACEM", "INDIAMART", "INDIGO",

    "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IPCALAB", "IRCTC", "ITC", "JINDALSTEL", "JKCEMENT", "JSWSTEEL",

    "JUBLFOOD", "KOTAKBANK", "L&TFH", "LALPATHLAB", "LICHSGFIN", "LT", "LTIM", "LTTS", "LUPIN", "M&M",

    "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MCX", "METROPOLIS", "MFSL", "MGL", "MOTHERSON", "MPHASIS",

    "MRF", "MUTHOOTFIN", "NATIONALUM", "NAVINFLUOR", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", "OFSS", "ONGC",

    "PAGEIND", "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", "POWERGRID",

    "PVRINOX", "RAMCOCEM", "RBLBANK", "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM",

    "SHRIRAMFIN", "SIEMENS", "SRF", "STL", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACHEM", "TATACOMM", "TATACONSUM",

    "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TRENT", "TVSMOTOR", "UBL", "ULTRACEMCO",

    "UPL", "VEDL", "VOLTAS", "WIPRO", "ZEEL", "ZYDUSLIFE"

]
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_intelligence(stock):
    # This prompt forces the AI to act as a Financial Intelligence Analyst
    prompt = f"""
    Act as an Advanced Financial Intelligence Analyst. 
    Perform a deep scan for {stock} on the NSE/BSE.
    
    1. SEARCH: Current negative news, unverified rumors on Reddit/X (Twitter), 
       and upcoming events (earnings, board meets, regulatory deadlines) for the next 14 days.
    2. LOOK FOR: Auditor resignations, SEBI probes, promoter pledging, 
       US tariff rumors, and 'deepfake' or 'leak' discussions on social media.
    3. FILTER: Only report if there is a 'Short-Term Negative Catalyst' that could 
       drop the price by >2% in the next week.
    
    If no major threat is found, respond with 'CLEAR'.
    If a threat is found, provide:
    - STOCK: {stock}
    - RISK SCORE: (1-10)
    - CATALYST: (The specific rumor or news)
    - SOURCE: (News site or Social Media platform)
    - ACTION: (Immediate sell, watch closely, etc.)
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    return response.text

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# --- EXECUTION ---
print("🚀 Sentinax-FO: Starting Advanced Intelligence Scan...")
for stock in STOCKS:
    result = get_intelligence(stock)
    if "CLEAR" not in result.upper():
        send_telegram(f"⚠️ *SENTINAX-FO ALERT*\n\n{result}")
        print(f"❗ Alert sent for {stock}")
    else:
        print(f"✅ {stock}: No immediate threats found.")
