# Chapter 14: Advanced CI/CD Patterns

<Exercise 2: Basic ChatOps Hook 🟢>
## 🎯 Objective
Create a simple Python HTTP server that acts as a ChatOps webhook endpoint to trigger deployments.

## 📋 Prerequisites
- Python 3.x installed.

## 📝 Instructions
1. Create a basic HTTP server using `http.server`.
2. Parse incoming POST requests simulating a Slack slash command.

## 💡 Hints
- Use `urllib.parse` to decode the x-www-form-urlencoded body.

## ✅ Expected Output / Solution
```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class ChatOpsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        
        command_text = parsed_data.get('text', [''])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
        if command_text.startswith('deploy '):
            service = command_text.split(' ')[1]
            response = f"🚀 Triggering deployment pipeline for: {service}"
        else:
            response = "Unknown command. Use: deploy <service>"
            
        self.wfile.write(response.encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), ChatOpsHandler)
    print("ChatOps Server running on port 8080...")
    server.serve_forever()
```

## 🧠 Key Takeaway
ChatOps brings deployment execution directly to where developers communicate, increasing visibility.
</Exercise 2: Basic ChatOps Hook 🟢>
