import time
import requests
import datetime
import json
import pandas as pd
import yfinance as yf

# Paniere mirato ed esteso di titoli ad alta liquidità (Azioni, ETF, Valute, Commodity)
# Invece di scansionare 500+ azioni a rischio timeout, usiamo un elenco selezionato di 60-70 asset top.
ASSETS_LIST = [
    # Grandi Azioni USA (Tech, Finance, Energy, Consumer, Healthcare)
    {"ticker": "AAPL", "company": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics", "asset_class": "azioni"},
    {"ticker": "MSFT", "company": "Microsoft Corp.", "sector": "Technology", "industry": "Software", "asset_class": "azioni"},
    {"ticker": "NVDA", "company": "NVIDIA Corp.", "sector": "Technology", "industry": "Semiconductors", "asset_class": "azioni"},
    {"ticker": "AMZN", "company": "Amazon.com Inc.", "sector": "Consumer Discretionary", "industry": "Retail", "asset_class": "azioni"},
    {"ticker": "GOOGL", "company": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet", "asset_class": "azioni"},
    {"ticker": "META", "company": "Meta Platforms Inc.", "sector": "Communication Services", "industry": "Internet", "asset_class": "azioni"},
    {"ticker": "TSLA", "company": "Tesla Inc.", "sector": "Consumer Discretionary", "industry": "Auto", "asset_class": "azioni"},
    {"ticker": "AMD", "company": "Advanced Micro Devices", "sector": "Technology", "industry": "Semiconductors", "asset_class": "azioni"},
    {"ticker": "NFLX", "company": "Netflix Inc.", "sector": "Communication Services", "industry": "Entertainment", "asset_class": "azioni"},
    {"ticker": "INTC", "company": "Intel Corp.", "sector": "Technology", "industry": "Semiconductors", "asset_class": "azioni"},
    {"ticker": "QCOM", "company": "Qualcomm Inc.", "sector": "Technology", "industry": "Semiconductors", "asset_class": "azioni"},
    {"ticker": "PYPL", "company": "PayPal Holdings", "sector": "Financials", "industry": "Credit Services", "asset_class": "azioni"},
    {"ticker": "XOM", "company": "Exxon Mobil Corp.", "sector": "Energy", "industry": "Oil & Gas", "asset_class": "azioni"},
    {"ticker": "CVX", "company": "Chevron Corp.", "sector": "Energy", "industry": "Oil & Gas", "asset_class": "azioni"},
    {"ticker": "JPM", "company": "JPMorgan Chase & Co.", "sector": "Financials", "industry": "Banks", "asset_class": "azioni"},
    {"ticker": "BAC", "company": "Bank of America Corp.", "sector": "Financials", "industry": "Banks", "asset_class": "azioni"},
    {"ticker": "WFC", "company": "Wells Fargo & Co.", "sector": "Financials", "industry": "Banks", "asset_class": "azioni"},
    {"ticker": "GS", "company": "Goldman Sachs Group", "sector": "Financials", "industry": "Capital Markets", "asset_class": "azioni"},
    {"ticker": "DIS", "company": "Walt Disney Co.", "sector": "Communication Services", "industry": "Entertainment", "asset_class": "azioni"},
    {"ticker": "BA", "company": "Boeing Co.", "sector": "Industrials", "industry": "Aerospace", "asset_class": "azioni"},
    {"ticker": "CAT", "company": "Caterpillar Inc.", "sector": "Industrials", "industry": "Machinery", "asset_class": "azioni"},
    {"ticker": "JNJ", "company": "Johnson & Johnson", "sector": "Healthcare", "industry": "Drug Manufacturers", "asset_class": "azioni"},
    {"ticker": "PFE", "company": "Pfizer Inc.", "sector": "Healthcare", "industry": "Drug Manufacturers", "asset_class": "azioni"},
    {"ticker": "UNH", "company": "UnitedHealth Group", "sector": "Healthcare", "industry": "Healthcare Plans", "asset_class": "azioni"},
    {"ticker": "KO", "company": "Coca-Cola Co.", "sector": "Consumer Defensive", "industry": "Beverages", "asset_class": "azioni"},
    {"ticker": "PEP", "company": "PepsiCo Inc.", "sector": "Consumer Defensive", "industry": "Beverages", "asset_class": "azioni"},
    {"ticker": "WMT", "company": "Walmart Inc.", "sector": "Consumer Defensive", "industry": "Retail", "asset_class": "azioni"},
    {"ticker": "COST", "company": "Costco Wholesale Corp.", "sector": "Consumer Defensive", "industry": "Retail", "asset_class": "azioni"},
    {"ticker": "MCD", "company": "McDonald's Corp.", "sector": "Consumer Discretionary", "industry": "Restaurants", "asset_class": "azioni"},
    {"ticker": "NKE", "company": "NIKE Inc.", "sector": "Consumer Discretionary", "industry": "Apparel", "asset_class": "azioni"},

    # ETF principali
    {"ticker": "SPY", "company": "SPDR S&P 500 ETF Trust", "sector": "ETF", "industry": "Broad Market", "asset_class": "etf"},
    {"ticker": "QQQ", "company": "Invesco QQQ Trust", "sector": "ETF", "industry": "Technology", "asset_class": "etf"},
    {"ticker": "IWM", "company": "iShares Russell 2000 ETF", "sector": "ETF", "industry": "Small Cap", "asset_class": "etf"},
    {"ticker": "DIA", "company": "SPDR Dow Jones Industrial Average ETF", "sector": "ETF", "industry": "Large Cap", "asset_class": "etf"},
    {"ticker": "GLD", "company": "SPDR Gold Shares", "sector": "ETF", "industry": "Commodity - Gold", "asset_class": "etf"},
    {"ticker": "SLV", "company": "iShares Silver Trust", "sector": "ETF", "industry": "Commodity - Silver", "asset_class": "etf"},
    {"ticker": "TLT", "company": "iShares 20+ Year Treasury Bond ETF", "sector": "ETF", "industry": "Bonds", "asset_class": "etf"},
    {"ticker": "XLE", "company": "Energy Select Sector SPDR Fund", "sector": "ETF", "industry": "Energy", "asset_class": "etf"},
    {"ticker": "XLF", "company": "Financial Select Sector SPDR Fund", "sector": "ETF", "industry": "Financials", "asset_class": "etf"},
    {"ticker": "XLK", "company": "Technology Select Sector SPDR Fund", "sector": "ETF", "industry": "Technology", "asset_class": "etf"},
    
    # Valute (Forex)
    {"ticker": "EURUSD=X", "company": "EUR/USD Exchange Rate", "sector": "Valute", "industry": "Forex", "asset_class": "valute"},
    {"ticker": "GBPUSD=X", "company": "GBP/USD Exchange Rate", "sector": "Valute", "industry": "Forex", "asset_class": "valute"},
    {"ticker": "USDJPY=X", "company": "USD/JPY Exchange Rate", "sector": "Valute", "industry": "Forex", "asset_class": "valute"},
    {"ticker": "AUDUSD=X", "company": "AUD/USD Exchange Rate", "sector": "Valute", "industry": "Forex", "asset_class": "valute"},
    {"ticker": "USDCAD=X", "company": "USD/CAD Exchange Rate", "sector": "Valute", "industry": "Forex", "asset_class": "valute"},

    # Commodity
    {"ticker": "GC=F", "company": "Gold Futures", "sector": "Commodity", "industry": "Precious Metals", "asset_class": "commodity"},
    {"ticker": "SI=F", "company": "Silver Futures", "sector": "Commodity", "industry": "Precious Metals", "asset_class": "commodity"},
    {"ticker": "CL=F", "company": "Crude Oil Futures", "sector": "Commodity", "industry": "Energy", "asset_class": "commodity"},
    {"ticker": "NG=F", "company": "Natural Gas Futures", "sector": "Commodity", "industry": "Energy", "asset_class": "commodity"},
    {"ticker": "ZC=F", "company": "Corn Futures", "sector": "Commodity", "industry": "Agriculture", "asset_class": "commodity"},
    {"ticker": "ZS=F", "company": "Soybean Futures", "sector": "Commodity", "industry": "Agriculture", "asset_class": "commodity"}
]

def get_earnings_dates_formatted(ticker_obj):
    last_e = "01/01/2025"
    next_e = "31/12/2026"
    try:
        ed_df = ticker_obj.earnings_dates
        if ed_df is not None and not ed_df.empty:
            now = pd.Timestamp.now(tz=ed_df.index.tz) if ed_df.index.tz else pd.Timestamp.now()
            past = ed_df[ed_df.index <= now]
            future = ed_df[ed_df.index > now]
            if not past.empty:
                last_e = past.index.max().strftime('%d/%m/%Y')
            if not future.empty:
                next_e = future.index.min().strftime('%d/%m/%Y')
    except Exception:
        pass
    return last_e, next_e

def main():
    results = []
    history = {}
    
    print("\n🔍 Analisi tecnica in corso...")
    
    for idx, s in enumerate(ASSETS_LIST, 1):
        ticker = s["ticker"]
        asset_cls = s["asset_class"]
        try:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="6mo")
            if hist is None or len(hist) < 30:
                continue
                
            prices = hist['Close'].tolist()
            current_price = prices[-1]
            prev_price = prices[0]
            
            w20 = min(20, len(prices))
            w50 = min(50, len(prices))
            w100 = min(100, len(prices))
            
            sma20 = sum(prices[-w20:]) / w20
            sma50 = sum(prices[-w50:]) / w50
            sma100 = sum(prices[-w100:]) / w100
            
            conditions_met = sum([
                current_price > sma20,
                current_price > sma50,
                current_price > sma100
            ])
            
            # Filtro SMA applicato per azioni ed ETF, diretto per valute e commodity
            passa_filtro = (conditions_met >= 2) if asset_cls in ["azioni", "etf"] else True
            
            if passa_filtro:
                last_e, next_e = get_earnings_dates_formatted(t_obj)
                change_pct = ((current_price - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0.0
                
                item = {
                    "ticker": ticker,
                    "company": s["company"],
                    "sector": s["sector"],
                    "industry": s["industry"],
                    "market_cap": "N/D",
                    "volume": "N/D",
                    "pe": "N/D",
                    "logo_url": f"https://assets.finviz.com/images/stocks/{ticker.replace('=X','').replace('=F','')}.png",
                    "asset_class": asset_cls,
                    "price": round(current_price, 4),
                    "change": f"{change_pct:+.2f}%",
                    "sma_status": f"SOPRA {conditions_met}/3 SMA" if asset_cls in ["azioni", "etf"] else "ATTIVO",
                    "trend_6m": "HIGH" if current_price >= prev_price else "LOW",
                    "last_earnings_date": last_e,
                    "next_earnings_date": next_e
                }
                
                results.append(item)
                history[ticker] = [{"date": str(index.date()), "close": float(row['Close'])} for index, row in hist.iterrows()]
                print(f"[{idx}/{len(ASSETS_LIST)}] ✔️ [{asset_cls.upper()}] {ticker} aggiunto.")
            else:
                print(f"[{idx}/{len(ASSETS_LIST)}] ❌ {ticker} escluso.")
        except Exception as e:
            print(f"[{idx}/{len(ASSETS_LIST)}] ⚠️ Errore {ticker}: {e}")
            continue
        time.sleep(0.1)
        
    data_output = {
        "meta": {
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z"
        },
        "results": results
    }
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data_output, f, ensure_ascii=False, indent=2)
        
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False)
        
    print(f"\n🎉 Generati data.json ({len(results)} elementi) e history.json senza timeout!")

if __name__ == "__main__":
    main()
