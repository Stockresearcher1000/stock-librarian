import os
import time
import requests
from google import genai
from google.genai import types

# 1. FULL F&O LIST
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

# 2. SETUP
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except:
        pass

def analyze_short_term_risk(stock):
    print(f"⚡ Scanning Short-Term Catalysts: {stock}...")
    
    # SYSTEM PROMPT: Focused on immediate, negative, news-driven impact.
    prompt = f"""
    Perform a real-time web search for '{stock}'. 
    Identify negative news from the LAST 24-48 HOURS that will trigger a SHORT-TERM price drop.
    
    FOCUS ON:
    1. EARNINGS/GUIDANCE: Recent earnings misses or negative management commentary.
    2. CORPORATE GOVERNANCE: SEBI raids, promoter share pledging increases, or major FII sell-offs.
    3. EXTERNAL SHOCKS: New US trade tariffs, sudden tax changes (LTCG/GST), or industry-specific regulatory bans.
    4. SENTIMENT SHIFTS: Panic in discussion forums (Reddit/X) or short-seller alerts.

    RESPONSE RULES:
    - Respond 'ALERT' ONLY if the news has a high probability of causing a 3%+ drop in the NEXT 5 SESSIONS.
    - IGNORE long-term growth stories, "buy the dip" opportunities, or old news.
    - If no immediate negative catalyst is found, reply 'SKIP'.
    - If alerting, provide: [Risk Score 1-10] and a 2-bullet point summary of the catalyst.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        output = response.text
        if "ALERT" in output.upper():
            send_telegram(f"📉 *SHORT-TERM NEGATIVE ALERT: {stock}*\n\n{output}")
        else:
            print(f"✅ {stock}: No short-term threats.")
            
    except Exception as e:
        print(f"Error analyzing {stock}: {e}")

# 4. EXECUTION LOOP
if __name__ == "__main__":
    for stock in STOCKS:
        analyze_short_term_risk(stock)
        time.sleep(10) # 10-second gap to stay within free tier and allow deep search
