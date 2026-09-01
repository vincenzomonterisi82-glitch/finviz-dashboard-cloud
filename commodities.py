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
            if len(close) >=
