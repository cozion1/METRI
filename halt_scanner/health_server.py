"""
health_server.py – Health check endpoint for cloud deployments
Runs alongside main.py to provide a /health endpoint
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PORT = 8080


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            status = {
                "status": "ok",
                "service": "HaltScanner Pro",
                "timestamp": datetime.now().isoformat(),
            }

            # Check if scanner ran recently
            log_file = DATA_DIR / "daily_log.json"
            if log_file.exists():
                try:
                    data = json.loads(log_file.read_text(encoding="utf-8"))
                    status["last_scan_entries"] = len(data)
                except Exception:
                    pass

            budget_file = DATA_DIR / "budget_tracker.json"
            if budget_file.exists():
                try:
                    budget = json.loads(budget_file.read_text(encoding="utf-8"))
                    status["api_calls_today"] = budget.get("calls", 0)
                    status["est_cost_today"] = budget.get("est_cost", 0)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs


def start_health_server():
    """מפעיל health server ב-thread נפרד."""
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
