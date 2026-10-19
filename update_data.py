import time
import requests
import csv
import io
import datetime
import json
import pandas as pd
import yfinance as yf

# URL pubblico per scaricare la lista dei ticker (es. S&P 500)
TICKERS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"

def fetch_stock_list():
    stocks = []
    print("⏳ Scaricamento della lista dei titoli da fonte pubblica...")
    try:
        response = requests.get(TICKERS_URL, timeout=10)
        if response.status_code == 200:
            f = io.StringIO(response.text)
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Symbol', '').strip()
                company = row.get('Security', '').strip()
                sector = row.get('GICS Sector', '').strip()
                ticker = ticker.replace('.', '-')
                if ticker:
                    stocks.append({
                        "ticker": ticker,
                        "company": company,
                        "sector": sector,
                        "industry": "N/D",
                        "market_cap": "N/D",
                        "volume": "N/D",
                        "pe": "N/D",
                        "logo_url": f"https://assets.finviz.com/images/stocks/{ticker}.png",
                        "asset_class": "azioni"
                    })
            print(f"✅ Caricati con successo {len(stocks)} titoli azionari.")
        else:
            stocks = get_fallback_stocks()
    except Exception as e:
        print(f"⚠️ Errore di rete: {e}, uso paniere predefinito.")
        stocks = get_fallback_stocks()
    return stocks

def get_fallback_stocks():
    return [
        {"ticker": "AAPL", "company": "Apple Inc.", "sector": "Information Technology", "industry": "Consumer Electronics", "market_cap": "3.0B", "volume": "50M", "pe": "30", "logo_url": "https://assets.finviz.com/images/stocks/AAPL.png", "asset_class": "azioni"},
        {"ticker": "MSFT", "company": "Microsoft Corp.", "sector": "Information Technology", "industry": "Software", "market_cap": "2.8B", "volume": "25M", "pe": "32", "logo_url": "https://assets.finviz.com/images/stocks/MSFT.png", "asset_class": "azioni"},
        {"ticker": "NVDA", "company": "NVIDIA Corp.", "sector": "Information Technology", "industry": "Semiconductors", "market_cap": "2.5B", "volume": "40M", "pe": "60", "logo_url": "https://assets.finviz.com/images/stocks/NVDA.png", "asset_class": "azioni"},
        {"ticker": "AMZN", "company": "Amazon.com Inc.", "sector": "Consumer Discretionary", "industry": "Retail", "market_cap": "1.9B", "volume": "30M", "pe": "45", "logo_url": "https://assets.finviz.com/images/stocks/AMZN.png", "asset_class": "azioni"},
        {"ticker": "GOOGL", "company": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet", "market_cap": "2.0B", "volume": "20M", "pe": "28", "logo_url": "https://assets.finviz.com/images/stocks/GOOGL.png", "asset_class": "azioni"},
        {"ticker": "XOM", "company": "Exxon Mobil Corp.", "sector": "Energy", "industry": "Oil & Gas", "market_cap": "450M", "volume": "15M", "pe": "12", "logo_url": "https://assets.finviz.com/images/stocks/XOM.png", "asset_class": "azioni"},
        {"ticker": "SPY", "company": "SPDR S&P 500 ETF Trust", "sector": "ETF", "industry": "ETF", "market_cap": "500B", "volume": "70M", "pe": "N/D", "logo_url": "https://assets.finviz.com/images/stocks/SPY.png", "asset_class": "etf"}
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
    stocks = fetch_stock_list()
    results = []
    history = {}
    
    print("\n🔍 Analisi tecnica e generazione dati per la dashboard...")
    
    for idx, s in enumerate(stocks, 1):
        ticker = s["ticker"]
        try:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="6mo")
            if hist is None or len(hist) < 100:
                continue
                
            prices = hist['Close'].tolist()
            current_price = prices[-1]
            prev_price = prices[0]
            
            sma20 = sum(prices[-20:]) / 20
            sma50 = sum(prices[-50:]) / 50
            sma100 = sum(prices[-100:]) / 100
            
            conditions_met = sum([
                current_price > sma20,
                current_price > sma50,
                current_price > sma100
            ])
            
            # Richiede che il prezzo sia sopra almeno 2 su 3 delle SMA
            if conditions_met >= 2:
                last_e, next_e = get_earnings_dates_formatted(t_obj)
                change_pct = ((current_price - prices[-2]) / prices[-2]) * 100 if len(prices) >= 2 else 0.0
                
                s["price"] = round(current_price, 4)
                s["change"] = f"{change_pct:+.2f}%"
                s["sma_status"] = f"SOPRA {conditions_met}/3 SMA"
                s["trend_6m"] = "HIGH" if current_price >= prev_price else "LOW"
                s["last_earnings_date"] = last_e
                s["next_earnings_date"] = next_e
                
                results.append(s)
                
                history[ticker] = [{"date": str(index.date()), "close": float(row['Close'])} for index, row in hist.iterrows()]
                print(f"[{idx}/{len(stocks)}] ✔️ {ticker} ({s['price']}) aggiunto.")
            else:
                print(f"[{idx}/{len(stocks)}] ❌ {ticker} escluso.")
        except Exception as e:
            print(f"[{idx}/{len(stocks)}] ⚠️ Errore {ticker}: {e}")
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
        
    print(f"\n🎉 Generati data.json ({len(results)} titoli) e history.json con successo!")

if __name__ == "__main__":
    main()
