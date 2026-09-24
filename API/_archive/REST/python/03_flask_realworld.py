# REAL-WORLD EXAMPLE: Flask (External 2)
# Demonstrates: Blueprints, Error Handling, Request Validation, API Key Auth
from flask import Flask, request, jsonify, abort
from functools import wraps
import uuid

app = Flask(__name__)
db = {}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-KEY') != 'my-secure-key':
            abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e.description)), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify(error=str(e.description)), 401

@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e.description)), 404

@app.route("/api/v1/orders", methods=["POST"])
@require_api_key
def create_order():
    data = request.get_json()
    if not data or 'item_id' not in data or 'quantity' not in data:
        abort(400, description="Missing item_id or quantity")
        
    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "item_id": data["item_id"],
        "quantity": data["quantity"],
        "status": "pending"
    }
    db[order_id] = order
    
    return jsonify({"message": "Order created", "order": order}), 201

@app.route("/api/v1/orders/<order_id>", methods=["GET"])
@require_api_key
def get_order(order_id):
    order = db.get(order_id)
    if not order:
        abort(404, description="Order not found")
    return jsonify(order), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
