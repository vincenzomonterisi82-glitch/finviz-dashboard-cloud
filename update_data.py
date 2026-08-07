import json
from worker import refresh_database
with open('data.json','w',encoding='utf-8') as f:
    json.dump(refresh_database(force=True),f,ensure_ascii=False,indent=2)
