# Finviz Dashboard cloud

Dashboard Finviz cloud con backend Flask, worker programmato e PWA per Samsung S24 Ultra.

## Deploy
1. Collega il repository a Render.
2. Crea il Web Service con `pip install -r requirements.txt` e `gunicorn app:app`.
3. Crea il Cron Job con `python worker.py`.
4. Apri l'URL HTTPS sul Samsung e scegli Installa app.

## Importante
Prima del deploy definitivo va collegato uno storage persistente, preferibilmente PostgreSQL. Il parser usa dati pubblici dello screener: per uso stabile verificare limiti e condizioni di Finviz o usare API/export autorizzati.