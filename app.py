import os
from datetime import datetime

import yfinance as yf
from flask import Flask, jsonify, request, send_from_directory
from worker import refresh_database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)


@app.get('/')
def home():
    return send_from_directory(BASE_DIR, 'dashboard.html')


@app.get('/manifest.json')
def manifest():
    return send_from_directory(BASE_DIR, 'manifest.json')


@app.get('/service-worker.js')
def service_worker():
    return send_from_directory(
        BASE_DIR, 'service-worker.js', mimetype='application/javascript'
    )


@app.get('/api/health')
def health():
    data = refresh_database(force=False)
    return jsonify({'ok': True, 'meta': data['meta']})


@app.get('/api/results')
def results():
    return jsonify(refresh_database(force=False))


@app.post('/api/refresh')
def refresh():
    return jsonify(refresh_database(force=True))


@app.get('/api/quote')
def quote():
    ticker = request.args.get('ticker', 'AAPL').strip().upper()
    if not ticker or not ticker.replace('.', '').replace('-', '').isalnum():
        return jsonify({'error': 'Ticker non valido'}), 400

    try:
        history = yf.Ticker(ticker).history(
            period='5d', interval='15m', prepost=True, auto_adjust=False
        )
        if history.empty:
            return jsonify({'error': 'Nessun dato disponibile per il ticker richiesto'}), 404

        last = history.iloc[-1]
        timestamp = history.index[-1]
        if getattr(timestamp, 'tzinfo', None) is not None:
            local_time = timestamp.tz_convert('America/New_York')
        else:
            local_time = timestamp

        market_time = local_time.hour * 60 + local_time.minute
        if 4 * 60 <= market_time < 9 * 60 + 30:
            session = 'pre-market'
        elif 9 * 60 + 30 <= market_time < 16 * 60:
            session = 'regular'
        elif 16 * 60 <= market_time < 20 * 60:
            session = 'after-hours'
        else:
            session = 'closed'

        return jsonify({
            'ticker': ticker,
            'price': round(float(last['Close']), 4),
            'time': local_time.isoformat(),
            'session': session,
            'updatedAt': datetime.utcnow().isoformat() + 'Z',
        })
    except Exception as exc:
        app.logger.exception('Errore nel recupero della quotazione per %s', ticker)
        return jsonify({'error': 'Impossibile recuperare la quotazione'}), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')))
