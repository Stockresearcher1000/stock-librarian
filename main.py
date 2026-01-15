import os
import time
import asyncio
import finnhub
from tiingo import TiingoClient
from google import genai
from google.genai import types
from tavily import TavilyClient
from exa_py import Exa
from telegram import Bot

# --- 1. SETUP CLIENTS ---
# Initialize all agents with the keys you added to Secrets
finnhub_client = finnhub.Client(api_key=os.environ.get('FINNHUB_API_KEY'))
tiingo_config = {'api_key': os.environ.get('TIINGO_API_KEY'), 'session': True}
tiingo_client = TiingoClient(tiingo_config)
gemini_client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
tavily = TavilyClient(api_key=os.environ.get('TAVILY_API_KEY'))
exa = Exa(api_key=os.environ.get('EXA_API_KEY'))
tg_bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'))
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- 2. THE 200 STOCK LIST ---
# Add your full list here. Example subset provided:
STOCKS = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "TATAMOTORS", "SBIN", "BHARTIARTL"] # Add all 200+

# --- 3. THE INTELLIGENCE LOGIC ---

async def scout_stock(stock):
    """Stage 1: The Scout (Finnhub & Tiingo) - Cheap & Fast"""
    try:
        # Check Finnhub for last 48 hours of news
        news = finnhub_client.company_news(stock, _from="2026-01-14", to="2026-01-16")
        
        # Look for 'Negative Keywords' in headlines
        trigger_words = ['fire', 'raid', 'lawsuit', 'fraud', 'sebi', 'nclt', 'fine', 'scam', 'crash']
        suspicious_news = [n for n in news if any(word in n['headline'].lower() for word in trigger_words)]
        
        if suspicious_news:
            return suspicious_news[0]['headline'], suspicious_news[0]['url']
        return None
    except Exception as e:
        print(f"Error scouting {stock}: {e}")
        return None

async def deep_dive(stock, initial_headline):
    """Stage 2: The Investigators (Gemini, Tavily, Exa) - Deep & Smart"""
    print(f"🚨 Crisis detected for {stock}. Investigating...")
    
    # Tavily searches the live web for the specific event
    search_query = f"Reason for {stock} negative news {initial_headline} Jan 2026"
    web_data = tavily.search(query=search_query, search_depth="advanced")
    
    # Exa hunts for regulatory/legal PDFs or filings
    exa_results = exa.search(f"official SEBI NCLT legal filing {stock} Jan 2026", num_results=2)
    
    # Stage 3: The Manager (Gemini) analyzes all gathered data
    search_tool = types.Tool(google_search=types.GoogleSearch())
    prompt = (
        f"URGENT ANALYSIS: {stock} has reported '{initial_headline}'. "
        f"Web Search Results: {web_data}. "
        f"Determine if this is a high-risk event (Plant fire, Fraud, CEO exit). "
        f"Format the output for Telegram with 🚨 and clear bullet points."
    )
    
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(tools=[search_tool])
    )
    return response.text

# --- 4. THE MASTER ORCHESTRATOR ---

async def main():
    print(f"🚀 Starting God-Mode Scan at {time.strftime('%H:%M:%S')} IST")
    
    # Optimized Batching: Scan stocks in groups of 10 to respect rate limits
    batch_size = 10
    for i in range(0, len(STOCKS), batch_size):
        batch = STOCKS[i : i + batch_size]
        print(f"Scanning batch {i//batch_size + 1}...")
        
        for stock in batch:
            scout_result = await scout_stock(stock)
            
            if scout_result:
                headline, url = scout_result
                report = await deep_dive(stock, headline)
                
                # Send the final alert to Telegram
                final_msg = f"<b>CRITICAL ALERT: {stock}</b>\n\n{report}\n\nSource: {url}"
                await tg_bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='HTML')
            
            # Small pause to be gentle on APIs
            await asyncio.sleep(1) 
        
        # Wait 10 seconds between batches to avoid IP blocks
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
