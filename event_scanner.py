import os
import asyncio
from datetime import datetime, timedelta
import finnhub
from groq import Groq
import telebot

# --- 1. SETUP ---
finnhub_client = finnhub.Client(api_key=os.environ.get("FINNHUB_API_KEY"))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
bot = telebot.TeleBot(os.environ.get("TELEGRAM_TOKEN"))
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 2. THE COMPREHENSIVE F&O LIST (2026) ---
# Tickers and Names for the entire segment
FO_STOCKS = {
    "360ONE": "360 ONE WAM", "ABB": "ABB India", "ABBOTINDIA": "Abbott India", "ABCAPITAL": "Aditya Birla Capital",
    "ABFRL": "Aditya Birla Fashion", "ACC": "ACC Limited", "ADANIENSOL": "Adani Energy Solutions", 
    "ADANIENT": "Adani Enterprises", "ADANIGREEN": "Adani Green Energy", "ADANIPORTS": "Adani Ports & SEZ",
    "ALKEM": "Alkem Laboratories", "AMBER": "Amber Enterprises", "AMBUJACEM": "Ambuja Cements", 
    "ANGELONE": "Angel One", "APLAPOLLO": "APL Apollo Tubes", "APOLLOHOSP": "Apollo Hospitals", 
    "APOLLOTYRE": "Apollo Tyres", "ASHOKLEY": "Ashok Leyland", "ASIANPAINT": "Asian Paints", 
    "ASTRAL": "Astral Limited", "AUBANK": "AU Small Finance Bank", "AUROPHARMA": "Aurobindo Pharma", 
    "AXISBANK": "Axis Bank", "BAJAJ-AUTO": "Bajaj Auto", "BAJFINANCE": "Bajaj Finance", 
    "BAJAJFINSV": "Bajaj Finserv", "BALKRISIND": "Balkrishna Industries", "BANDHANBNK": "Bandhan Bank",
    "BANKBARODA": "Bank of Baroda", "BANKINDIA": "Bank of India", "BEL": "Bharat Electronics", 
    "BHARATFORG": "Bharat Forge", "BHEL": "BHEL", "BHARTIARTL": "Bharti Airtel", "BIOCON": "Biocon",
    "BOSCHLTD": "Bosch", "BPCL": "Bharat Petroleum", "BRITANNIA": "Britannia Industries", 
    "BSE": "BSE Limited", "CANBK": "Canara Bank", "CDSL": "CDSL", "CHOLAFIN": "Cholamandalam Finance", 
    "CIPLA": "Cipla", "COALINDIA": "Coal India", "COFORGE": "Coforge", "COLPAL": "Colgate Palmolive",
    "CONCOR": "Container Corp", "COROMANDEL": "Coromandel International", "CROMPTON": "Crompton Greaves",
    "CUMMINSIND": "Cummins India", "DABUR": "Dabur India", "DALBHARAT": "Dalmia Bharat", 
    "DEEPAKNTR": "Deepak Nitrite", "DELHIVERY": "Delhivery", "DIVISLAB": "Divis Laboratories", 
    "DIXON": "Dixon Technologies", "DLF": "DLF Limited", "DMART": "Avenue Supermarts", 
    "DRREDDY": "Dr. Reddy's Lab", "EICHERMOT": "Eicher Motors", "ESCORTS": "Escorts Kubota", 
    "EXIDEIND": "Exide Industries", "FEDERALBNK": "Federal Bank", "GAIL": "GAIL India", 
    "GLENMARK": "Glenmark Pharma", "GMRINFRA": "GMR Airports", "GODREJCP": "Godrej Consumer",
    "GODREJPROP": "Godrej Properties", "GRASIM": "Grasim Industries", "GUJGASLTD": "Gujarat Gas",
    "HAL": "Hindustan Aeronautics", "HAVELLS": "Havells India", "HCLTECH": "HCL Technologies", 
    "HDFCBANK": "HDFC Bank", "HDFCLIFE": "HDFC Life", "HEROMOTOCO": "Hero MotoCorp", 
    "HINDALCO": "Hindalco", "HINDCOPPER": "Hindustan Copper", "HINDPETRO": "HPCL", 
    "HINDUNILVR": "Hindustan Unilever", "ICICIBANK": "ICICI Bank", "ICICIGI": "ICICI Lombard",
    "IDFCFIRSTB": "IDFC First Bank", "IEX": "Indian Energy Exchange", "IGL": "Indraprastha Gas",
    "INDHOTEL": "Indian Hotels", "INDIGO": "Interglobe Aviation", "INDUSINDBK": "IndusInd Bank",
    "INDUSTOWER": "Indus Towers", "INFY": "Infosys", "IOC": "Indian Oil", "IPCALAB": "Ipca Labs",
    "IRCTC": "IRCTC", "ITC": "ITC Limited", "JINDALSTEL": "Jindal Steel", "JSWSTEEL": "JSW Steel",
    "JUBLFOOD": "Jubilant Foodworks", "KOTAKBANK": "Kotak Mahindra Bank", "LT": "Larsen & Toubro",
    "LTIM": "LTIMindtree", "LUPIN": "Lupin", "M&M": "Mahindra & Mahindra", "MARICO": "Marico",
    "MARUTI": "Maruti Suzuki", "MCX": "MCX India", "MPHASIS": "Mphasis", "MRF": "MRF Limited",
    "MUTHOOTFIN": "Muthoot Finance", "NATIONALUM": "National Aluminium", "NAUKRI": "Info Edge",
    "NESTLEIND": "Nestle India", "NMDC": "NMDC Limited", "NTPC": "NTPC", "OBEROIRLTY": "Oberoi Realty",
    "ONGC": "ONGC", "PAGEIND": "Page Industries", "PEL": "Piramal Enterprises", "PFC": "Power Finance Corp",
    "PIDILITIND": "Pidilite", "PIIND": "PI Industries", "PNB": "Punjab National Bank", 
    "POLYCAB": "Polycab India", "POWERGRID": "Power Grid", "RECLTD": "REC Limited", 
    "RELIANCE": "Reliance Industries", "SAIL": "Steel Authority of India", "SBICARD": "SBI Cards",
    "SBILIFE": "SBI Life", "SBIN": "State Bank of India", "SHREECEM": "Shree Cement", 
    "SIEMENS": "Siemens India", "SRF": "SRF Limited", "SUNPHARMA": "Sun Pharma", 
    "TATACOMM": "Tata Communications", "TATACONSUM": "Tata Consumer", "TATAMOTORS": "Tata Motors",
    "TATAPOWER": "Tata Power", "TATASTEEL": "Tata Steel", "TCS": "Tata Consultancy Services",
    "TECHM": "Tech Mahindra", "TITAN": "Titan Company", "TRENT": "Trent Limited", 
    "TVSMOTOR": "TVS Motor", "ULTRACEMCO": "UltraTech Cement", "UPL": "UPL Limited",
    "VEDL": "Vedanta", "VOLTAS": "Voltas", "WIPRO": "Wipro", "ZEEL": "Zee Entertainment"
}

# --- 3. RISK INTELLIGENCE BRAIN ---
async def analyze_event_risk(ticker, name):
    try:
        today_dt = datetime.now()
        today_str = today_dt.strftime('%Y-%m-%d')
        future_30 = (today_dt + timedelta(days=30)).strftime('%Y-%m-%d')
        past_7 = (today_dt - timedelta(days=7)).strftime('%Y-%m-%d')

        # 1. Fetch Earnings Calendar (This specifically looks for FUTURE dates)
        # Note: Finnhub uses 'from' and 'to' for earnings dates
        calendar = finnhub_client.earnings_calendar(_from=today_str, to=future_30, symbol=ticker)
        earnings_info = ""
        if calendar.get('earningsCalendar'):
            e = calendar['earningsCalendar'][0]
            earnings_info = f"UPCOMING EARNINGS: {e['date']} (Estimate EPS: {e.get('eps_estimate', 'N/A')})"

        # 2. Fetch News (Reduced lookback to keep it fresh)
        news = finnhub_client.company_news(ticker, _from=past_7, to=today_str)
        headlines = " | ".join([n['headline'] for n in news[:10]])

        # 3. AI Analysis with "Future 2026" Strictness
        prompt = (
            f"STOCK: {name} ({ticker})\n"
            f"TODAY'S DATE: {today_str}\n"
            f"EARNINGS DATA: {earnings_info}\n"
            f"RECENT NEWS: {headlines}\n\n"
            f"ACT AS: Forensic Risk Analyst.\n"
            f"GOAL: Find any event between {today_str} and {future_30} (YEAR 2026) that will crash the stock.\n"
            f"REQUIREMENT: The date MUST be in the future (2026). Ignore all 2024 or 2025 news.\n"
            f"RESPONSE: If a future risk exists, reply 'DANGER: [Date] | [Risk] | [Reasoning]'. Otherwise reply 'SAFE'."
        )

        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        
        analysis = response.choices[0].message.content
        if "DANGER" in analysis.upper() and "2026" in analysis:
            return f"🚨 *FUTURE RISK ALERT (2026): {name}*\n{analysis}"
        return None
    except Exception as e:
        print(f"Error on {ticker}: {e}")
        return None

# --- 4. THE SCANNER ENGINE ---
async def main():
    print(f"🕵️ Starting Forensic Scan for {len(FO_STOCKS)} Stocks...")
    # Using semaphore to avoid hitting Finnhub/Groq rate limits
    sem = asyncio.Semaphore(1) 
    
    for ticker, name in FO_STOCKS.items():
        async with sem:
            result = await analyze_event_risk(ticker, name)
            if result:
                bot.send_message(CHAT_ID, result, parse_mode="Markdown")
            # 1.2s delay ensures we don't exceed Free Tier limits
            await asyncio.sleep(1.2)

if __name__ == "__main__":
    asyncio.run(main())
