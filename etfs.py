import yfinance as yf

ETF_LIST = {
    # Settoriali (SPDR Select Sector)
    'XLK': ('XLK', 'Technology'),
    'XLE': ('XLE', 'Energy'),
    'XLF': ('XLF', 'Financials'),
    'XLV': ('XLV', 'Health Care'),
    'XLY': ('XLY', 'Consumer Discretionary'),
    'XLP': ('XLP', 'Consumer Staples'),
    'XLI': ('XLI', 'Industrials'),
    'XLB': ('XLB', 'Materials'),
    'XLU': ('XLU', 'Utilities'),
    'XLRE': ('XLRE', 'Real Estate'),
    'XLC': ('XLC', 'Communication Services'),
    # Non settoriali (ampio mercato)
    'SPY': ('SPY', 'Broad Market'),
    'QQQ': ('QQQ', 'Broad Market'),
    'DIA': ('DIA', 'Broad Market'),
    'IWM': ('IWM', 'Broad Market'),
    # Indici esteri (usato l'indice cash, nessun ticker future continuous confermato su Yahoo Finance)
    'DAX': ('^GDAXI', 'Indice'),
}


def fmt_cap(value):
    if value is None:
        return '-'
    for suffix, div in (('T', 1e12), ('B', 1e9), ('M', 1e6)):
        if value >= div:
            return f'{value/div:.2f}{suffix}'
    return f'{value:.0f}'


def fetch_etfs():
    rows = []
    for display, (symbol, sector) in ETF_LIST.items():
        row = {
            'ticker': display, 'yahoo_symbol': symbol, 'company': display, 'sector': sector,
            'industry': 'ETF', 'country': 'USA', 'market_cap': '-', 'pe': '-', 'price': '-',
            'change': '-', 'volume': '-', 'sma_status': 'N/D', 'trend_6m': 'N/D', 'asset_class': 'etf',
        }
        try:
            tk = yf.Ticker(symbol)
            info = tk.info
            row['company'] = info.get('longName') or info.get('shortName') or display
            aum = info.get('totalAssets')
            if aum:
                row['market_cap'] = fmt_cap(aum)
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
