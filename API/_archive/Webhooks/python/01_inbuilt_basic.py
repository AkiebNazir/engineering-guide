# BASIC EXAMPLE: Python Inbuilt http.server
# Demonstrates raw HTTP handling of Webhooks and HMAC SHA256 Signature verification.
import hmac
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET = b"my_super_secret_webhook_key"

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        payload = self.rfile.read(length)
        signature = self.headers.get("X-Signature", "")

        # Verify Signature
        expected_sig = hmac.new(SECRET, payload, hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(expected_sig, signature):
            self.send_response(200)
            print("Webhook Verified and Accepted!")
        else:
            self.send_response(401)
            print("Webhook Signature Invalid!")
            
        self.end_headers()

if __name__ == "__main__":
    print("Listening for webhooks on 8080...")
    HTTPServer(('', 8080), WebhookHandler).serve_forever()
