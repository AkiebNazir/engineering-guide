# BASIC EXAMPLE: Python Inbuilt http.server
# Demonstrates raw HTTP handling without external libraries.
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

db = {}

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/users/"):
            user_id = self.path.split("/")[-1]
            if user_id in db:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(db[user_id]).encode())
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        if self.path == "/users":
            length = int(self.headers.get('content-length', 0))
            body = json.loads(self.rfile.read(length))
            user_id = str(len(db) + 1)
            body["id"] = user_id
            db[user_id] = body
            
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

if __name__ == "__main__":
    print("Listening on 8080...")
    HTTPServer(('', 8080), RequestHandler).serve_forever()
