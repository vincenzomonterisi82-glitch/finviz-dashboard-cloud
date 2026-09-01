import yfinance as yf

COMMODITY_LIST = {
    'Oro': 'GC=F',
    'Rame': 'HG=F',
    'Argento': 'SI=F',
    'Petrolio greggio WTI': 'CL=F',
    'Gas naturale': 'NG=F',
    'Caffè': 'KC=F',
    'Cacao': 'CC=F',
    'Cotone': 'CT=F',
    'Zucchero': 'SB=F',
    'Suini magri (Lean Hogs)': 'HE=F',
    'Bovini vivi (Live Cattle)': 'LE=F',
    'Mais': 'ZC=F',
    'Soia': 'ZS=F',
    'Farina di soia': 'ZM=F',
    'Frumento tenero invernale (Wheat)': 'ZW=F',
}


def fetch_commodities():
    rows = []
    for display, symbol in COMMODITY_LIST.items():
        row = {
            'ticker': display, 'yahoo_symbol': symbol, 'company': '', 'sector': 'Commodity',
            'industry': 'Futures', 'country': 'USA', 'market_cap': '-', 'pe': '-', 'price': '-',
            'change': '-', 'volume': '-', 'sma_status': 'N/D', 'trend_6m': 'N/D', 'asset_class': 'commodity',
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
                row['price'] = f'{current:.2f}'
        except Exception:
            pass
        rows.append(row)
    return rows
