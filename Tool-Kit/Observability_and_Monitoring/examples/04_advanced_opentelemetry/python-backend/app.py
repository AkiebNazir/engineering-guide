from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route('/process_payment')
def process_payment():
    time.sleep(0.5) # Simulate DB lookup
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
