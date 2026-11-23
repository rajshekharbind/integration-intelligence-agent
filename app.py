import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """Fallback Python serverless handler for Vercel if Python runtime is triggered."""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(html_path, "r", encoding="utf-8") as f:
            self.wfile.write(f.read().encode("utf-8"))
        return
