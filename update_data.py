import json,time
from datetime import datetime,timezone
import yfinance as yf
from worker import refresh_database
payload=refresh_database(force=True); today=datetime.now(timezone.utc).date()
for row in payload.get('results', []):
 row['last_earnings_date']='N/D'; row['next_earnings_date']='N/D'; row['logo_url']=f"https://assets.parqet.com/logos/symbol/{row['ticker']}?format=png"
 tk=yf.Ticker(row['ticker'])
 try:
  dates=tk.get_earnings_dates(limit=12); parsed=[]
  if dates is not None and not dates.empty:
   for value in dates.index:
    stamp=value.to_pydatetime() if hasattr(value,'to_pydatetime') else value; parsed.append(stamp.date() if hasattr(stamp,'date') else stamp)
   past=[x for x in parsed if x<today]; future=[x for x in parsed if x>=today]
   if past: row['last_earnings_date']=max(past).strftime('%d/%m/%Y')
   if future: row['next_earnings_date']=min(future).strftime('%d/%m/%Y')
 except Exception: pass
 try:
  info=tk.info; candidates=[]
  if info.get('regularMarketPrice') is not None and info.get('regularMarketTime'):
   candidates.append(('Regular',info['regularMarketPrice'],info['regularMarketTime']))
  if info.get('preMarketPrice') is not None and info.get('preMarketTime'):
   candidates.append(('Pre-market',info['preMarketPrice'],info['preMarketTime']))
  if info.get('postMarketPrice') is not None and info.get('postMarketTime'):
   candidates.append(('After-hours',info['postMarketPrice'],info['postMarketTime']))
  if candidates:
   candidates.sort(key=lambda x:x[2],reverse=True); sess,price,ts=candidates[0]
   row['last_price']=round(float(price),2); row['last_price_session']=sess
   row['last_price_time']=datetime.fromtimestamp(ts,tz=timezone.utc).isoformat()
  else:
   row['last_price']=None; row['last_price_session']='N/D'; row['last_price_time']=None
 except Exception:
  row['last_price']=None; row['last_price_session']='N/D'; row['last_price_time']=None
 time.sleep(.15)
history={}
def col(df,name):
 x=df[name]; return x.iloc[:,0] if hasattr(x,'columns') else x
for row in payload.get('results',[]):
 ticker=row['ticker']
 try:
  raw=yf.download(ticker,period='2y',interval='1d',auto_adjust=True,progress=False,threads=False); close=col(raw,'Close').dropna(); op=col(raw,'Open'); high=col(raw,'High'); low=col(raw,'Low'); records=[]
  for i,date in enumerate(close.index):
   records.append({'date':date.strftime('%Y-%m-%d'),'open':round(float(op.loc[date]),4),'high':round(float(high.loc[date]),4),'low':round(float(low.loc[date]),4),'close':round(float(close.loc[date]),4),'sma20':round(float(close.iloc[:i+1].rolling(20).mean().iloc[-1]),4) if i>=19 else None,'sma50':round(float(close.iloc[:i+1].rolling(50).mean().iloc[-1]),4) if i>=49 else None,'sma100':round(float(close.iloc[:i+1].rolling(100).mean().iloc[-1]),4) if i>=99 else None})
  history[ticker]=records
 except Exception: history[ticker]=[]
 time.sleep(.15)
with open('data.json','w',encoding='utf-8') as f: json.dump(payload,f,ensure_ascii=False,indent=2,default=str)
with open('history.json','w',encoding='utf-8') as f: json.dump(history,f,ensure_ascii=False,separators=(',',':'))
