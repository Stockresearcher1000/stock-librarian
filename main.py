import os
import asyncio
from datetime import datetime, timedelta
import finnhub
from groq import Groq
from google import genai
from google.genai import types
import telebot

# --- 1. CONFIGURATION & CLIENTS ---
# Initialize clients with GitHub Secrets
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
finnhub_client = finnhub.Client(api_key=os.environ.get("FINNHUB_API_KEY"))
bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 2. THE F&O STOCK UNIVERSE (220+ Stocks) ---
# Updated for Jan 2026 inclusive of new listings
STOCKS = {
    "RELIANCE": "Reliance Industries", "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank",
    "INFY": "Infosys", "TCS": "Tata Consultancy Services", "BHARTIARTL": "Bharti Airtel",
    "AXISBANK": "Axis Bank", "SBIN": "State Bank of India", "LICI": "LIC of India",
    "BAJFINANCE": "Bajaj Finance", "MARUTI": "Maruti Suzuki", "SUNPHARMA": "Sun Pharma",
    "ADANIENT": "Adani Enterprises", "ADANIPORTS": "Adani Ports", "HCLTECH": "HCL Tech",
    "ITC": "ITC Ltd", "KOTAKBANK": "Kotak Mahindra Bank", "TITAN": "Titan Company",
    "ULTRACEMCO": "UltraTech Cement", "ASIANPAINT": "Asian Paints", "WIPRO": "Wipro",
    "M&M": "Mahindra & Mahindra", "NTPC": "NTPC Ltd", "POWERGRID": "Power Grid",
    "ONGC": "ONGC", "COALINDIA": "Coal India", "TATASTEEL": "Tata Steel",
    "TATAMOTORS": "Tata Motors", "JINDALSTEL": "Jindal Steel", "JSWSTEEL": "JSW Steel",
    "HINDALCO": "Hindalco", "GRASIM": "Grasim Industries", "NESTLEIND": "Nestle India",
    "BRITANNIA": "Britannia", "HUL": "Hindustan Unilever", "CIPLA": "Cipla",
    "DRREDDY": "Dr. Reddy's", "DIVISLAB": "Divi's Lab", "APOLLOHOSP": "Apollo Hospitals",
    "EICHERMOT": "Eicher Motors", "HEROMOTOCO": "Hero MotoCorp", "BAJAJ-AUTO": "Bajaj Auto",
    "BPCL": "BPCL", "IOC": "Indian Oil", "HAL": "Hindustan Aeronautics",
    "BEL": "Bharat Electronics", "BHEL": "BHEL", "RECLTD": "REC Ltd",
    "PFC": "PFC", "GAIL": "GAIL", "DLF": "DLF Ltd", "LTIM": "LTIMindtree",
    "TECHM": "Tech Mahindra", "SWIGGY": "Swiggy", "WAAREEENER": "Waaree Energies",
    "PREMIERENE": "Premier Energies", "NTPCGREEN": "NTPC Green", "ZOMATO": "Zomato",
    "PAYTM": "Paytm", "JIOFIN": "Jio Financial", "TRENT": "Trent", "CHOLAFIN": "Cholamandalam",
    "SHRIRAMFIN": "Shriram Finance", "MUTHOOTFIN": "Muthoot Finance", "CANBK": "Canara Bank",
    "IDFCFIRSTB": "IDFC First Bank", "AUROPHARMA": "Aurobindo Pharma", "LUPIN": "Lupin",
    "ALKEM": "Alkem Lab", "GLENMARK": "Glenmark", "TORNTPHARM": "Torrent Pharma",
    "POLYCAB": "Polycab", "HAVELLS": "Havells", "SIEMENS": "Siemens", "ABB": "ABB India",
    "CUMMINSIND": "Cummins", "ASHOKLEY": "Ashok Leyland", "AMBUJACEM": "Ambuja Cement",
    "ACC": "ACC", "SHREECEM": "Shree Cement", "DALBHARAT": "Dalmia Bharat",
    "PIDILITIND": "Pidilite", "BERGEPAINT": "Berger Paints", "COLPAL": "Colgate",
    "GODREJCP": "Godrej Consumer", "MARICO": "Marico", "DABUR": "Dabur",
    "MCDOWELL-N": "United Spirits", "VBL": "Varun Beverages", "TATACONSUM": "Tata Consumer"
    # Note: Shortened list for readability; all 220+ should be added to your final dict.
}

# --- 3. THE AI BRAIN FUNCTIONS ---

async def groq_sentiment_filter(headline):
    """Tier 1: High-speed sentiment scan to filter out noise"""
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a market panic sensor. Respond ONLY with 'YES' or 'NO'."},
                {"role": "user", "content": f"Is this headline highly critical, negative, or a major structural change for the company? Headline: {headline}"}
            ],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content.strip().upper() == "YES"
    except Exception:
        return True # If Groq fails, fallback to investigation to be safe

async def gemini_deep_dive(ticker, headline, url):
    """Tier 2: Deep legal and financial analysis using Search Grounding"""
    prompt = f"""
    INVESTIGATE: {headline} for {ticker}.
    1. Verify this news using Google Search.
    2. Determine if it represents a 'Black Swan' event (fraud, regulatory ban, plant fire, CEO exit).
    3. TARGET ACTION: Provide a SELL, HOLD, or BUY recommendation for the 9:15 AM market open.
    4. IMPACT: Estimate potential % drop if the news is negative.
    """
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
            )
        )
        return response.text
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# --- 4. MAIN ENGINE ---

async def run_scan():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    print(f"Starting Market Scan for {today}...")
    
    for ticker, name in STOCKS.items():
        try:
            # Step A: Get News
            news = finnhub_client.company_news(ticker, _from=yesterday, to=today)
            
            for item in news[:3]: # Scan top 3 recent headlines
                headline = item['headline']
                
                # Step B: Groq Filter (The Scout)
                if await groq_sentiment_filter(headline):
                    print(f"ALERT: Significant news found for {ticker}. Investigating...")
                    
                    # Step C: Gemini Analysis (The Judge)
                    report = await gemini_deep_dive(ticker, headline, item['url'])
                    
                    # Step D: Telegram Alert
                    msg = f"🚨 *URGENT MARKET ALERT: {ticker}*\n\n"
                    msg += f"*News:* {headline}\n\n"
                    msg += f"*Analysis:* \n{report}\n\n"
                    msg += f"[Source]({item['url']})"
                    
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                    await asyncio.sleep(2) # Prevent rate limiting
        except Exception as e:
            print(f"Error scanning {ticker}: {e}")

if __name__ == "__main__":
    asyncio.run(run_scan())
