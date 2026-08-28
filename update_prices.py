import json, time
from datetime import datetime, timezone
import yfinance as yf

with open('data.json', encoding='utf-8') as f:
    payload = json.load(f)

tickers = [row['ticker'] for row in payload.get('results', [])]

CHUNK = 150

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

prices = {}
run_started = datetime.now(timezone.utc)

for group in chunks(tickers, CHUNK):
    try:
        df = yf.download(
            tickers=' '.join(group),
            period='1d',
            interval='1m',
            prepost=True,
            group_by='ticker',
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception:
        continue

    for t in group:
        try:
            sub = df[t] if len(group) > 1 else df
            sub = sub.dropna(subset=['Close'])
            if sub.empty:
                continue

            last_time = sub.index[-1]
            if last_time.tzinfo is None:
                last_time = last_time.tz_localize('America/New_York')
            eastern = last_time.tz_convert('America/New_York')
            last_time_utc = last_time.tz_convert('UTC')

            hm = eastern.hour * 60 + eastern.minute
            if 9 * 60 + 30 <= hm < 16 * 60:
                session = 'Regular'
            elif hm < 9 * 60 + 30:
                session = 'Pre-market'
            else:
                session = 'After-hours'

            last_close = float(sub.iloc[-1]['Close'])

            prices[t] = {
                'last_price': round(last_close, 2),
                'last_price_session': session,
                'last_price_time': last_time_utc.isoformat(),
                'date': eastern.strftime('%Y-%m-%d'),
                'today_open': round(float(sub.iloc[0]['Open']), 4),
                'today_high': round(float(sub['High'].max()), 4),
                'today_low': round(float(sub['Low'].min()), 4),
                'today_close': round(last_close, 4),
            }
        except Exception:
            continue

    time.sleep(1)

with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(
        {'updated_at': run_started.isoformat(), 'prices': prices},
        f, ensure_ascii=False, indent=2
    )