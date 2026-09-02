import yfinance as yf

CURRENCY_LIST = {
    'EUR': ('6E=F', 'Euro FX Futures'),
    'GBP': ('6B=F', 'British Pound Futures'),
    'AUD': ('6A=F', 'Australian Dollar Futures'),
    'JPY': ('6J=F', 'Japanese Yen Futures'),
    'CAD': ('6C=F', 'Canadian Dollar Futures'),
    'CHF': ('6S=F', 'Swiss Franc Futures'),
    'DXY': ('DX=F', 'US Dollar Index Futures'),
}


def fetch_currencies():
    rows = []
    for display, (symbol, name) in CURRENCY_LIST.items():
        row = {
            'ticker': display, 'yahoo_symbol': symbol, 'company': name, 'sector': 'Valute',
            'industry': 'Futures', 'country': 'USA', 'market_cap': '-', 'pe': '-', 'price': '-',
            'change': '-', 'volume': '-', 'sma_status': 'N/D', 'trend_6m': 'N/D', 'asset_class': 'valute',
        }
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            vol = info.get('regularMarketVolume') or info.get('averageVolume')
            if vol:
                row['volume'] = f'{vol:,}'
            chg = info.get('regularMarketChangePercent')
            if chg is not None:
                row['change'] = f'{chg:.2f}%'
        except Exception:
            pass
        try:
            close = yf.download(symbol, period='1y', interval='1d', auto_adjust=True, progress=False, threads=False)['Close']
            if hasattr(close, 'columns'):
                close = close.iloc[:, 0]
            close = close.dropna()
            if len(close) >= 130:
                current = float(close.iloc[-1])
                values = [float(close.rolling(n).mean().iloc[-1]) for n in (20, 50, 100)]
                above = sum(current > x for x in values)
                row['sma_status'] = f'Sopra {above}/3' if above >= 2 else f'Sotto {3-above}/3'
                old = float(close.iloc[-126])
                row['trend_6m'] = 'HIGH' if current > old else 'LOW'
                row['price'] = f'{current:.6f}'
        except Exception:
            pass
        rows.append(row)
    return rows
