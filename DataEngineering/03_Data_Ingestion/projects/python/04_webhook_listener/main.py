from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time

PAYLOAD_DIR = "payloads"

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if not os.path.exists(PAYLOAD_DIR):
            os.makedirs(PAYLOAD_DIR)
            
        filename = f"payload_{int(time.time())}.json"
        filepath = os.path.join(PAYLOAD_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(post_data)
            
        print(f"Received webhook, saved to {filepath}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "success"}')

def main():
    print('Starting Data Engineering Project: 04_webhook_listener')
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, WebhookHandler)
    print("Listening for webhooks on port 8080...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server.")
        httpd.server_close()

if __name__ == '__main__':
    main()
