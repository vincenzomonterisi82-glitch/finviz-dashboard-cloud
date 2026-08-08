import json, time
import yfinance as yf
from worker import refresh_database
payload=refresh_database(force=True)
history={}
def col(df,name):
    x=df[name]
    return x.iloc[:,0] if hasattr(x,'columns') else x
for row in payload.get('results',[]):
    ticker=row['ticker']
    try:
        raw=yf.download(ticker,period='6mo',interval='1d',auto_adjust=True,progress=False,threads=False)
        close=col(raw,'Close').dropna(); op=col(raw,'Open'); high=col(raw,'High'); low=col(raw,'Low')
        records=[]
        for i,date in enumerate(close.index):
            records.append({'date':date.strftime('%Y-%m-%d'),'open':round(float(op.loc[date]),4),'high':round(float(high.loc[date]),4),'low':round(float(low.loc[date]),4),'close':round(float(close.loc[date]),4),'sma20':round(float(close.iloc[:i+1].rolling(20).mean().iloc[-1]),4) if i>=19 else None,'sma50':round(float(close.iloc[:i+1].rolling(50).mean().iloc[-1]),4) if i>=49 else None,'sma100':round(float(close.iloc[:i+1].rolling(100).mean().iloc[-1]),4) if i>=99 else None})
        history[ticker]=records
    except Exception:
        history[ticker]=[]
    time.sleep(0.2)
with open('data.json','w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2)
with open('history.json','w',encoding='utf-8') as f: json.dump(history,f,ensure_ascii=False,separators=(',',':'))
