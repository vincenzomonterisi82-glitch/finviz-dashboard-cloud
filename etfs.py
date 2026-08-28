import yfinance as yf

ETF_LIST = {
    # Settoriali (SPDR Select Sector)
    'XLK': 'Technology',
    'XLE': 'Energy',
    'XLF': 'Financials',
    'XLV': 'Health Care',
    'XLY': 'Consumer Discretionary',
    'XLP': 'Consumer Staples',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLC': 'Communication Services',
    # Non settoriali (ampio mercato)
    'SPY': 'Broad Market',
    'QQQ': 'Broad Market',
    'DIA': 'Broad Market',
    'IWM': 'Broad Market',
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
    for ticker, sector in ETF_LIST.items():
        row = {
            'ticker': ticker, 'company': ticker, 'sector': sector, 'industry': 'ETF',
            'country': 'USA', 'market_cap': '-', 'pe': '-', 'price': '-', 'change': '-',
            'volume': '-', 'sma_status': 'N/D', 'trend_6m': 'N/D', 'asset_class': 'etf',
        }
        try:
            tk = yf.Ticker(ticker)
            info = tk.info
            row['company'] = info.get('longName') or info.get('shortName') or ticker
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
            close = yf.download(ticker, period='1y', interval='1d', auto_adjust=True, progress=False, threads=False)['Close']
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
