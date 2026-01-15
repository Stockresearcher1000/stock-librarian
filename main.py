import os
import asyncio
import time
import finnhub
from google import genai
from google.genai import types
from tavily import TavilyClient
from exa_py import Exa
from telegram import Bot
from telegram.constants import ParseMode

# --- 1. CONFIGURATION & CLIENTS ---
# These are pulled from your GitHub Secrets
FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
TAVILY_KEY = os.environ.get('TAVILY_API_KEY')
EXA_KEY = os.environ.get('EXA_API_KEY')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Initialize Clients
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)
gemini_client = genai.Client(api_key=GEMINI_KEY)
tavily = TavilyClient(api_key=TAVILY_KEY)
exa = Exa(api_key=EXA_KEY)
tg_bot = Bot(token=TG_TOKEN)

# --- 2. SMART STOCK DICTIONARY (Test Set) ---
# Format: "TICKER": "Common Search Name"
STOCKS = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "HDFCBANK": "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "INFY": "Infosys",
    "TATAMOTORS": "Tata Motors",
    "SBIN": "State Bank of India",
    "ADANIENT": "Adani Enterprises",
    "BHARTIARTL": "Bharti Airtel",
    "ITC": "ITC Limited"
}

# --- 3. INTELLIGENCE FUNCTIONS ---

async def scout_stock(ticker):
    """Stage 1: Fast scanning for negative keywords in headlines."""
    try:
        # Scan news from last 48 hours to cover holiday gaps
        news = finnhub_client.company_news(ticker, _from="2026-01-14", to="2026-01-16")
        
        trigger_words = ['fire', 'raid', 'lawsuit', 'fraud', 'sebi', 'nclt', 'fine', 'scam', 'crash', 'investigation', 'arrest']
        
        for n in news:
            headline = n['headline'].lower()
            if any(word in headline for word in trigger_words):
                return n['headline'], n['url']
        return None
    except Exception as e:
        print(f"Scout Error for {ticker}: {e}")
        return None

async def deep_dive_investigation(ticker, headline):
    """Stage 2: Deep-web search and AI reasoning."""
    common_name = STOCKS.get(ticker, ticker)
    
    # Combined search for Ticker and Name
    search_query = f"({ticker} OR '{common_name}') CRITICAL negative news {headline} Jan 2026"
    
    # Tavily for live news links
    web_data = tavily.search(query=search_query, search_depth="advanced")
    
    # Exa for PDF/Regulatory filings
    exa_data = exa.search(f"official legal regulatory document {common_name} {ticker} Jan 2026", num_results=2)

    # Gemini Analysis with Google Search Grounding
    search_tool = types.Tool(google_search=types.GoogleSearch())
    prompt = (
        f"You are a Senior Financial Risk Analyst. Analyze this event for {common_name} ({ticker}):\n"
        f"Initial Headline: {headline}\n"
        f"Search Evidence: {web_data}\n"
        f"Exa Filings: {exa_data}\n\n"
        f"Identify if this is a high-impact negative event. "
        f"Format as a Telegram alert: Use 🚨 for high risk, ⚠️ for medium. "
        f"Include a 'Why it matters' section and 'Source Links'."
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(tools=[search_tool])
    )
    return response.text

# --- 4. EXECUTION ENGINE ---

async def run_market_scan():
    print(f"🚀 Round 1: Starting 8:30 AM IST Intelligence Scan...")
    
    # Process in batches of 5 to strictly avoid rate limits
    items = list(STOCKS.items())
    for i in range(0, len(items), 5):
        batch = items[i:i+5]
        
        for ticker, name in batch:
            print(f"Checking {name} ({ticker})...")
            found_news = await scout_stock(ticker)
            
            if found_news:
                headline, source_url = found_news
                report = await deep_dive_investigation(ticker, headline)
                
                # Send to Telegram
                alert_text = f"<b>CRITICAL MARKET INTELLIGENCE</b>\n\n{report}"
                await tg_bot.send_message(chat_id=CHAT_ID, text=alert_text, parse_mode=ParseMode.HTML)
                print(f"✅ Alert sent for {ticker}")
            
            await asyncio.sleep(1.5) # Gap between individual stocks
        
        print(f"Batch {i//5 + 1} complete. Pausing...")
        await asyncio.sleep(10) # Gap between batches

if __name__ == "__main__":
    asyncio.run(run_market_scan())
