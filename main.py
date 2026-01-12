import time
from google import genai
from google.genai import types

# Initialize your Gemini Client
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# 2026 NSE F&O LIST (Approx. 200 Stocks including new 2025-26 additions)
STOCKS = [
    "ABB", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ALKEM", "AMBUJACEM", "APOLLOHOSP", 
    "ASIANPAINT", "ASTRAL", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", 
    "BALKRISIND", "BANDHANBNK", "BANKBARODA", "BEL", "BERGEPAINT", "BHARTIARTL", "BIOCON", 
    "BOSCHLTD", "BPCL", "BRITANNIA", "CANBK", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", 
    "COLPAL", "CONCOR", "CUMMINSIND", "DABUR", "DALBHARAT", "DEEPAKNTR", "DELHIVERY", "DIVISLAB", 
    "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS", "ETERNAL", "EXIDEIND", "FEDERALBNK", 
    "GAIL", "GLENMARK", "GMRINFRA", "GODREJCP", "GODREJPROP", "GRASIM", "GUJGASLTD", "HAL", 
    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", 
    "HINDPETRO", "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IEX", 
    "IGL", "INDHOTEL", "INDIACEM", "INDIAMART", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", 
    "IPCALAB", "IRCTC", "IRFC", "ITC", "JINDALSTEL", "JIOFIN", "JKCEMENT", "JSWENERGY", 
    "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "L&TFH", "LICI", "LT", "LTIM", "LUPIN", "M&M", 
    "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MCX", "METROPOLIS", "MPHASIS", "MRF", 
    "MUTHOOTFIN", "NATIONALUM", "NAVINFLUOR", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", 
    "OFSS", "ONGC", "PAGEIND", "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", 
    "PNB", "POLYCAB", "POWERTARID", "PVRINOX", "RAMCOCEM", "RBLBANK", "RECLTD", "RELIANCE", 
    "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SRF", 
    "SUNPHARMA", "SUNTV", "SUPREMEIND", "SWIGGY", "SYNGENE", "TATACOMM", "TATACONSUM", 
    "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", "TORNTPHARM", "TRENT", 
    "TVSMOTOR", "UBL", "ULTRACEMCO", "UPL", "VEDL", "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
]

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_batch_intelligence(stock_group):
    stock_list_str = ", ".join(stock_group)
    
    prompt = f"""
    You are an Omniscient Financial Forensic Auditor. 
    Analyze these stocks for HIGH-PROBABILITY price crashes: {stock_list_str}.
    
    CRITICAL TRIGGERS TO TRACK:
    1. LEGAL & COURT: Search for upcoming Supreme Court or SAT judgments (e.g., SAT Appeal No. 348/2023). Look for 'Reserved Judgments' about to be delivered.
    2. REGULATORY: Check for SEBI 'Adjudication Orders' or RBI 'Monetary Penalties' issued in the last 24-48 hours.
    3. INSIDER WARNINGS: Search for 'Auditor Resignations' (e.g., AD-1 filings) or 'Forensic Audit' rumors.
    
    FILTERING CRITERIA:
    - ONLY alert if you are 95%+ confident of a NEGATIVE price impact >5%.
    - If it's just general news or a "buy" rating, IGNORE IT.
    
    RESPONSE FORMAT:
    - If NO God-tier threat is found, respond ONLY with: NULL
    - If a threat IS found, respond with:
      🚨 STOCK: [Name]
      ⚖️ LEGAL/CATALYST: [Specific Case No. or Regulatory Order]
      💥 IMPACT: [Expected % fall]
      📅 TIMING: [When the impact is expected]
      🧠 CONFIDENCE: [High/Absolute]
    """
    
    try:
        # Using Gemini 2.0 Flash for high-speed search and reasoning
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "NULL"

def main():
    print("🔎 Starting God-Mode Risk Scan for F&O Stocks...")
    # Checking in batches of 10 to maintain high search accuracy
    for stock_group in chunks(STOCKS, 10):
        print(f"Checking Risk: {stock_group[0]} to {stock_group[-1]}...")
        
        report = get_batch_intelligence(stock_group)
        
        if report and report.upper() != "NULL":
            # Replace with your actual telegram send function
            print(f"Sending Urgent Alert: \n{report}")
            # send_telegram(report)
        else:
            print("Status: Clear (No high-impact threats)")
        
        # Throttling to respect API limits and allow deep searching
        time.sleep(20)

if __name__ == "__main__":
    main()
