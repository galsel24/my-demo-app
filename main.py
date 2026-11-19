import http.server
import json
import os
import sys
import time
import urllib.parse

# Auto-detect Render PORT or default to 8080
PORT = int(os.environ.get("PORT", 8080))

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Arcadia Financial - F5 XC Demo</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #0f172a; color: #f8fafc; }}
        nav {{ background: #1e293b; padding: 1rem 2rem; border-bottom: 2px solid #3b82f6; display: flex; justify-content: space-between; align-items: center; }}
        .container {{ max-width: 900px; margin: 2rem auto; padding: 1rem; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5); }}
        h2 {{ color: #60a5fa; margin-top: 0; }}
        a {{ color: #38bdf8; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        input, button {{ padding: 0.5rem; margin-top: 0.5rem; border-radius: 4px; border: 1px solid #475569; }}
        input {{ width: 280px; background: #0f172a; color: white; }}
        button {{ background: #2563eb; color: white; font-weight: bold; cursor: pointer; border: none; }}
        button:hover {{ background: #1d4ed8; }}
        code {{ background: #334155; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }}
    </style>
</head>
<body>
    <nav>
        <h2 style="margin:0;">🛡️ Arcadia Financial Core Portal</h2>
        <div>Detected Client IP: <code>{client_ip}</code></div>
    </nav>
    <div class="container">
        <div class="card">
            <h2>1. HTTP Delivery & Inspection</h2>
            <p>Verify traffic steering, routing rules, TLS offloading, and mTLS headers passed by F5 XC.</p>
            <ul>
                <li><a href="/headers">🔍 Inspect Request Headers & mTLS Identity</a></li>
                <li><a href="/cache-test">⚡ CDN & Caching Verification</a></li>
            </ul>
        </div>

        <div class="card">
            <h2>2. WAAP & Security Verification (WAF & Bots)</h2>
            <p>Test WAF signatures, Threat Campaigns, and Bot Protection policies:</p>
            <form action="/login" method="post" style="margin-bottom: 1rem;">
                <strong>Login Endpoint (Bot Defense & Brute Force Target):</strong><br>
                <input type="text" name="username" placeholder="Username (e.g. admin)" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Submit Login</button>
            </form>
            <form action="/search" method="get">
                <strong>Search Endpoint (WAF Attack Vector - SQLi / XSS):</strong><br>
                <input type="text" name="query" placeholder="Search accounts (e.g. ' OR 1=1 --)" required><br>
                <button type="submit">Execute Search</button>
            </form>
        </div>

        <div class="card">
            <h2>3. API Security & Discovery</h2>
            <p>Swagger-documented APIs vs. hidden shadow endpoints:</p>
            <ul>
                <li><a href="/api/v1/accounts">📜 GET /api/v1/accounts (Documented)</a></li>
                <li><a href="/api/v1/sensitive-data">🔒 GET /api/v1/sensitive-data (Data Leakage Demo)</a></li>
                <li><a href="/api/v1/internal-debug">🕵️ GET /api/v1/internal-debug (Shadow API - Undocumented)</a></li>
                <li><a href="/docs">📖 OpenAPI Interactive Spec</a></li>
            </ul>
        </div>

        <div class="card">
            <h2>4. Troubleshooting & Latency Simulator</h2>
            <p>Simulate backend failures to test F5 XC dashboards and alerts:</p>
            <ul>
                <li><a href="/simulate/502">💥 Trigger Bad Gateway (HTTP 502)</a></li>
                <li><a href="/simulate/500">💥 Trigger Internal Server Error (HTTP 500)</a></li>
                <li><a href="/simulate/latency?seconds=3">⏱️ Simulate 3-Second Backend Latency</a></li>
            </ul>
        </div>
    </div>
</body>
</html>
"""


class DemoAppHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean terminal logging
        sys.stdout.write(f"[{self.log_date_time_string()}] {self.command} {self.path} -> {args[1]}\n")

    def _send_json(self, data, status_code=200, extra_headers=None):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html_str, status_code=200):
        payload = html_str.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Home Page
        if path == "/":
            client_ip = self.headers.get("x-forwarded-for", self.client_address[0])
            self._send_html(HOME_HTML.format(client_ip=client_ip))

        # 2. Inspect Headers & mTLS
        elif path == "/headers":
            rows = "".join([f"<tr><td style='padding:6px;border:1px solid #334155;'><strong>{k}</strong></td><td style='padding:6px;border:1px solid #334155;color:#38bdf8;'>{v}</td></tr>" for k, v in self.headers.items()])
            html = f"""<!DOCTYPE html><html><head><title>Headers Inspection</title></head>
            <body style='background:#0f172a;color:#f8fafc;font-family:sans-serif;padding:2rem;'>
            <a href='/' style='color:#38bdf8;'>← Back to Home</a>
            <h2>🔍 HTTP Headers Received by Backend (Origin)</h2>
            <table style='border-collapse:collapse;width:100%;max-width:850px;background:#1e293b;'>
            <tr style='background:#334155;'><th>Header Name</th><th>Value</th></tr>{rows}</table>
            </body></html>"""
            self._send_html(html)

        # 3. Cache Test
        elif path == "/cache-test":
            now = time.time()
            self._send_json(
                {
                    "status": "success",
                    "message": "If CDN caching is enabled on F5 XC LB, consecutive requests will show the SAME timestamp and XC Cache HIT header.",
                    "server_generated_timestamp": now,
                    "cache_control": "public, max-age=120"
                },
                extra_headers={
                    "Cache-Control": "public, max-age=120",
                    "X-Origin-Timestamp": str(now)
                }
            )

        # 4. Search Endpoint (WAF SQLi/XSS target)
        elif path == "/search":
            q = query.get("query", [""])[0]
            self._send_json({
                "search_query": q,
                "results_found": 3,
                "message": f"Results for '{q}' returned successfully."
            })

        # 5. Documented APIs
        elif path == "/api/v1/accounts":
            self._send_json([
                {"account_id": "ACC-100293", "type": "Checking", "balance": 15420.50, "currency": "USD"},
                {"account_id": "ACC-994821", "type": "Savings", "balance": 98200.00, "currency": "USD"}
            ])

        elif path == "/api/v1/sensitive-data":
            self._send_json({
                "account_holder": "Jane Doe",
                "ssn": "123-45-6789",
                "credit_card": "4111-2221-8899-4455",
                "warning": "This endpoint serves sensitive PII/PCI data to test F5 XC data masking."
            })

        # 6. Shadow API (Undocumented endpoint)
        elif path == "/api/v1/internal-debug":
            self._send_json({
                "service": "core-banking",
                "debug_mode": True,
                "cluster_node": "node-04b",
                "shadow_api_status": "This route is NOT in openapi_spec.json to trigger F5 XC Shadow API discovery!"
            })

        # 7. Documentation View
        elif path in ["/docs", "/openapi.json"]:
            self._send_json({
                "openapi": "3.0.0",
                "info": {"title": "Arcadia Financial API", "version": "1.0.0"},
                "paths": {
                    "/api/v1/accounts": {"get": {"summary": "List accounts"}},
                    "/api/v1/transfer": {"post": {"summary": "Transfer money"}},
                    "/api/v1/sensitive-data": {"get": {"summary": "Sensitive profile data"}}
                }
            })

        # 8. Troubleshooting simulators
        elif path == "/simulate/502":
            self._send_json({"error": "Bad Gateway", "code": 502}, status_code=502)

        elif path == "/simulate/500":
            self._send_json({"error": "Internal Server Error", "code": 500}, status_code=500)

        elif path == "/simulate/latency":
            secs = int(query.get("seconds", [3])[0])
            secs = min(max(secs, 1), 10)
            time.sleep(secs)
            self._send_json({"status": "success", "delayed_seconds": secs})

        else:
            self._send_json({"error": "Not Found", "path": path}, status_code=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""

        if path == "/login":
            parsed_form = urllib.parse.parse_qs(body)
            user = parsed_form.get("username", ["unknown"])[0]
            self._send_json({
                "status": "authentication_attempt",
                "user_received": user,
                "note": "If an attack or bot was detected, F5 XC WAF/Bot Defense blocks this before reaching origin."
            })

        elif path == "/api/v1/transfer":
            try:
                payload = json.loads(body)
            except Exception:
                payload = {"raw": body}
            self._send_json({
                "transaction_id": f"TXN-{int(time.time())}",
                "status": "APPROVED",
                "details": payload
            })

        else:
            self._send_json({"error": "Not Found", "path": path}, status_code=404)


if __name__ == "__main__":
    print(f"🚀 Starting Arcadia Demo Server on port {PORT}...")
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), DemoAppHandler)
    server.serve_forever()
