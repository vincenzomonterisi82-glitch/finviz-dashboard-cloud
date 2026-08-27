# app.py
from flask import Flask, jsonify, request
import yfinance as yf
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# Cache semplice in memoria
quote_cache = {}
CACHE_TTL_SECONDS = 60  # 1 minuto

def get_latest_quote(ticker: str) -> dict:
    """
    Ottiene l'ultimo prezzo disponibile per il ticker, includendo pre-market e after-hours.
    Usa yfinance per scaricare dati intraday a 15 minuti e restituisce l'ultima candela chiusa o in corso.
    """
    now = datetime.now(pytz.timezone("America/New_York"))
    cache_key = ticker.upper()
    
    # Controllo cache
    if cache_key in quote_cache:
        entry = quote_cache[cache_key]
        if (now - entry["ts"]).total_seconds() < CACHE_TTL_SECONDS:
            return entry["data"]
    
    # Scarica dati intraday a 15 minuti (include pre/after se disponibili)
    try:
        ticker_obj = yf.Ticker(ticker)
        # period='1d' con interval='15m' restituisce le candele del giorno corrente
        df = ticker_obj.history(period="1d", interval="15m")
        
        if df.empty:
            # Fallback: prova con 5 giorni per catturare pre/after
            df = ticker_obj.history(period="5d", interval="15m")
        
        if df.empty:
            return {"error": "Nessun dato disponibile"}
        
        # Prendi l'ultima riga
        last = df.iloc[-1]
        last_price = float(last["Close"])
        last_time = last.index[-1]
        
        # Determina se è pre-market, regular o after-hours
        # Orari NYSE: pre 04:00-09:30, regular 09:30-16:00, after 16:00-20:00
        hour = last_time.hour
        minute = last_time.minute
        
        if hour < 9 or (hour == 9 and minute < 30):
            session = "pre-market"
        elif hour < 16:
            session = "regular"
        else:
            session = "after-hours"
        
        data = {
            "ticker": ticker.upper(),
            "price": last_price,
            "time": last_time.isoformat(),
            "session": session
        }
        
        # Aggiorna cache
        quote_cache[cache_key] = {"data": data, "ts": now}
        return data
        
    except Exception as e:
        return {"error": str(e)}

@app.route("/api/quote", methods=["GET"])
def api_quote():
    ticker = request.args.get("ticker", "AAPL").upper()
    return jsonify(get_latest_quote(ticker))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
