import os
from flask import Flask, jsonify, send_from_directory
from worker import refresh_database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)
@app.get('/')
def home(): return send_from_directory(BASE_DIR, 'dashboard.html')
@app.get('/manifest.json')
def manifest(): return send_from_directory(BASE_DIR, 'manifest.json')
@app.get('/service-worker.js')
def service_worker(): return send_from_directory(BASE_DIR, 'service-worker.js', mimetype='application/javascript')
@app.get('/api/health')
def health():
    data = refresh_database(force=False); return jsonify({'ok': True, 'meta': data['meta']})
@app.get('/api/results')
def results(): return jsonify(refresh_database(force=False))
@app.post('/api/refresh')
def refresh(): return jsonify(refresh_database(force=True))
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')))