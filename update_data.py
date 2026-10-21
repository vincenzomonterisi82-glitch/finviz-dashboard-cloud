import time
import requests
import csv
import io
import datetime
import json
import pandas as pd
import yfinance as yf

# Lista estesa suddivisa per categorie (Azioni, ETF, Valute, Commodity)
ASSETS_CONFIG = [
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
    
    # Valute (Forex Futures / Ticker Yahoo)
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

def fetch_stock_list():
    stocks = []
    # Aggiungiamo subito le categorie fisse (ETF, Valute, Commodity)
    for item in ASSETS_CONFIG:
        stocks.append({
            "ticker": item["ticker"],
            "company": item["company"],
            "sector": item["sector"],
            "industry": item["industry"],
            "market_cap": "N/D",
            "volume": "N/D",
            "pe": "N/D",
            "logo_url": f"https://assets.finviz.com/images/stocks/{item['ticker'].replace('=X','').replace('=F','')}.png",
            "asset_class": item["asset_class"]
        })

    # Scarichiamo le azioni dall'S&P 500
    print("⏳ Scaricamento della lista delle azioni S&P 500...")
    TICKERS_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    try:
        response = requests.get(TICKERS_URL, timeout=10)
        if response.status_code == 200:
            f = io.StringIO(response.text)
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Symbol', '').strip().replace('.', '-')
                company = row.get('Security', '').strip()
                sector = row.get('GICS Sector', '').strip()
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
            print(f"✅ Totale asset caricati (tra azioni e altri strumenti): {len(stocks)}")
    except Exception as e:
        print(f"⚠️ Errore nel download S&P 500: {e}")
        
    return stocks

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
        asset_cls = s["asset_class"]
        try:
            t_obj = yf.Ticker(ticker)
            hist = t_obj.history(period="6mo")
            if hist is None or len(hist) < 50:
                continue
                
            prices = hist['Close'].tolist()
            current_price = prices[-1]
            prev_price = prices[0]
            
            # Per valute/commodity usiamo finestre più corte se i dati giornalieri sono limitati
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
            
            # Per azioni/etf richiediamo >= 2/3, per valute/commodity filtriamo direttamente o teniamo uguali
            passa_filtro = (conditions_met >= 2) if asset_cls in ["azioni", "etf"] else True
            
            if passa_filtro:
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
                print(f"[{idx}/{len(stocks)}] ✔️ [{asset_cls.upper()}] {ticker} ({s['price']}) aggiunto.")
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
        
    print(f"\n🎉 Generati data.json ({len(results)} elementi) e history.json con successo!")

if __name__ == "__main__":
    main()
