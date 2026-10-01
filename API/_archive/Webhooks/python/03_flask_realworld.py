# REAL-WORLD EXAMPLE: Flask (External 2)
# Demonstrates: Webhook verification and classic request handling
from flask import Flask, request, abort, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = b"whsec_my_super_secret"

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    # Flask provides get_data() to get the raw bytes needed for HMAC
    payload = request.get_data()
    signature = request.headers.get('Stripe-Signature')

    if not signature:
        abort(400, description="Missing signature")

    expected_sig = hmac.new(WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        abort(401, description="Invalid signature")

    event = request.get_json()
    if event.get("type") == "checkout.session.completed":
        print(f"Fulfilling order for {event['data']['object']['id']}")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=5000)
