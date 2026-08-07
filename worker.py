import os, sqlite3, time, random
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
DB_PATH=os.getenv('DB_PATH','finviz.db'); TTL=int(os.getenv('CACHE_TTL_SECONDS','3600')); MAX_PAGES=int(os.getenv('MAX_PAGES','12')); FILTERS=os.getenv('FINVIZ_FILTERS','cap_midover,geo_usa,sh_avgvol_o1000,sh_opt_option,sh_price_u30,ta_sma20_pa,ta_sma50_pa,ta_sma100_pa')
def db():
 c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.execute('CREATE TABLE IF NOT EXISTS results (ticker TEXT PRIMARY KEY, company TEXT, sector TEXT, industry TEXT, country TEXT, market_cap TEXT, pe TEXT, price TEXT, change TEXT, volume TEXT, sma_status TEXT, trend_6m TEXT, updated_at TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT)'); c.commit(); return c
def read(c,status=None):
 rows=[dict(x) for x in c.execute('SELECT * FROM results ORDER BY ticker')]; meta={x['key']:x['value'] for x in c.execute('SELECT key,value FROM meta')}; meta['total_results_loaded']=len(rows)
 if status: meta['status']=status
 return {'results':rows,'meta':meta}
def fetch():
 s=requests.Session(); s.headers['User-Agent']='Mozilla/5.0 FinvizDashboard/1.0'; out={}
 for p in range(MAX_PAGES):
  start=p*20+1; url=f'https://finviz.com/screener.ashx?v=111&f={FILTERS}'+(f'&r={start}' if p else ''); r=s.get(url,timeout=30); r.raise_for_status(); soup=BeautifulSoup(r.text,'html.parser'); table=soup.find('table',class_='screener_table')
  if not table: break
  for tr in table.find_all('tr'):
   cells=[x.get_text(' ',strip=True) for x in tr.find_all('td')]
   if len(cells)>=11 and cells[0].isdigit(): out[cells[1]]={'ticker':cells[1],'company':cells[2],'sector':cells[3],'industry':cells[4],'country':cells[5],'market_cap':cells[6],'pe':cells[7],'price':cells[8],'change':cells[9],'volume':cells[10],'sma_status':'N/D','trend_6m':'N/D'}
  time.sleep(random.uniform(2,4))
 return list(out.values())
def refresh_database(force=False):
 c=db(); meta={x['key']:x['value'] for x in c.execute('SELECT key,value FROM meta')}; now=datetime.now(timezone.utc)
 if not force and meta.get('updated_at'):
  try:
   if (now-datetime.fromisoformat(meta['updated_at'])).total_seconds()<TTL: return read(c,'cache')
  except ValueError: pass
 try:
  rows=fetch(); stamp=now.isoformat(); c.execute('DELETE FROM results'); c.executemany('INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',[(x['ticker'],x['company'],x['sector'],x['industry'],x['country'],x['market_cap'],x['pe'],x['price'],x['change'],x['volume'],x['sma_status'],x['trend_6m'],stamp) for x in rows]); c.execute("INSERT INTO meta VALUES('updated_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(stamp,)); c.execute("INSERT INTO meta VALUES('status','ok') ON CONFLICT(key) DO UPDATE SET value=excluded.value"); c.commit(); return read(c,'ok')
 except Exception as e:
  c.execute("INSERT INTO meta VALUES('status',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",('stale-cache',)); c.commit(); return read(c,'stale-cache')
if __name__=='__main__': refresh_database(True)