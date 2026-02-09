from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

# State file path - relative to web/ directory
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "live_state.json")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/live_data')
def live_data():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": str(e)})
    return jsonify({"error": "State file not found"})

@app.route('/api/execute', methods=['POST'])
def execute_trade():
    data = request.json
    print(f"⚡ SNIPER COMMAND RECEIVED: {data}")
    return jsonify({"status": "QUEUED", "message": f"Order for {data.get('ticker')} queued."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
