# BASIC EXAMPLE: Python Inbuilt http.server
# Demonstrates how GraphQL fundamentally runs over standard HTTP POST.
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/graphql":
            length = int(self.headers.get('content-length', 0))
            body = json.loads(self.rfile.read(length))
            
            # Simulated parsing of a basic GraphQL query string
            # e.g. {"query": "query { getUser { name } }"}
            query = body.get("query", "")
            if "getUser" in query:
                response = {"data": {"getUser": {"name": "Alice"}}}
            else:
                response = {"errors": [{"message": "Unknown query or mutation"}]}
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    print("Simulated GraphQL running on 8080...")
    HTTPServer(('', 8080), RequestHandler).serve_forever()
