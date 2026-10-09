# server.py
"""极简 Web 服务，使用标准库 http.server。运行：python server.py"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from src.db import init_db
from src import services

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            self.serve_file(os.path.join(TEMPLATE_DIR, "index.html"), "text/html")
        elif path == "/api/members":
            self.serve_json(services.list_members())
        elif path == "/api/tasks":
            self.serve_json(services.list_tasks())
        elif path == "/api/summary":
            self.serve_json(services.summary_all())
        elif path == "/api/summary-by-month":
            self.serve_json(services.summary_by_month())
        elif path == "/api/summary-by-group":
            self.serve_json(services.summary_by_group())
        elif path == "/api/top-members":
            self.serve_json(services.top_members(10))
        else:
            self.send_error(404)

    def serve_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_response(200, "application/json; charset=utf-8", body)

    def serve_file(self, path, content_type):
        if not os.path.exists(path):
            self.send_error(404, f"File not found: {path}")
            return
        with open(path, "rb") as f:
            body = f.read()
        self._send_response(200, f"{content_type}; charset=utf-8", body)

    def _send_response(self, status, content_type, body):
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    init_db()
    port = 34004
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"服务已启动：http://127.0.0.1:{port}")
    print(f"模板目录：{TEMPLATE_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")