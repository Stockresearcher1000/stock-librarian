import os
import time
import requests
from google import genai
from google.genai import types

# 1. THE F&O STOCK LIST
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

# 2. SETUP (Secrets must be in GitHub)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except:
        pass

def analyze_stock_god_mode(stock):
    print(f"🕵️ Deep Scan: {stock}...")
    
    # SYSTEM PROMPT: Strictly looking for negative catalysts, NOT price movements.
    prompt = f"""
    Perform an exhaustive real-time search for '{stock}' on the entire internet.
    Ignore standard price fluctuations or daily market noise. 
    
    Search for these 3 specific 'Black Swan' categories:
    1. LEGAL/FRAUD: Investigations (SEBI, ED, CBI), whistleblower complaints, auditor resignations, or forensic accounting red flags.
    2. DISRUPTIVE EVENTS: Massive factory fires, strikes, product recalls, or promoter pledging/margin call threats.
    3. HIDDEN RISKS: Negative discussion trends on ValuePickr or Reddit, short-seller reports (like Hindenburg style), or major institutional exit rumors.

    CRITICAL INSTRUCTION:
    - Only respond with 'ALERT' if you find a catalyst that can cause a SUSTAINED drop in price.
    - If the news is just a price dip without a major reason, reply 'SKIP'.
    - If the news is positive or neutral, reply 'SKIP'.
    - If you alert, provide a 1-10 'Impact Score' where 10 is a bankruptcy threat.
    """

    try:
        # Gemini 2.0 Flash is currently more powerful for real-time web research than most others 
        # because it is integrated directly with Google's search index.
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        output = response.text
        if "ALERT" in output.upper():
            send_telegram(f"⚡ *GOD-MODE NEGATIVE CATALYST: {stock}*\n\n{output}")
        else:
            print(f"✅ {stock} is clean.")
            
    except Exception as e:
        print(f"Error: {e}")

# 4. EXECUTION
if __name__ == "__main__":
    for stock in STOCKS:
        analyze_stock_god_mode(stock)
        time.sleep(8) # 8-second delay to ensure we finish 180 stocks within 45 mins
