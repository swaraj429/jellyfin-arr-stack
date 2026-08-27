import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = 80
CADDY_API = os.getenv("CADDY_API", "http://caddy:2019")
STATIC_DIR = Path("/app/static")


def get_caddy_config():
    try:
        with urllib.request.urlopen(
            f"{CADDY_API}/config/apps/http/servers/srv0/routes",
            timeout=3,
        ) as response:
            return json.loads(response.read())
    except Exception:
        return []


def discover_services():
    routes = get_caddy_config()
    services = []
    seen = set()

    def walk(node):
        if not isinstance(node, dict):
            return

        # Look for path matchers on this route
        paths = []

        for matcher in node.get("match", []):
            for path in matcher.get("path", []):
                if isinstance(path, str):
                    paths.append(path)

        # Determine whether this route contains a reverse proxy
        upstream = None

        for handler in node.get("handle", []):
            if handler.get("handler") == "reverse_proxy":
                upstreams = handler.get("upstreams", [])

                if upstreams:
                    upstream = upstreams[0].get("dial")

            # Caddy `route {}` creates nested routes inside
            # a subroute handler.
            if handler.get("handler") == "subroute":
                for child in handler.get("routes", []):
                    walk(child)

        # If this route is a reverse proxy route,
        # extract the /service/* path.
        if upstream:
            for path in paths:
                if not path.endswith("/*"):
                    continue

                base = path[:-2]

                if not base or base == "/" or base in seen:
                    continue

                seen.add(base)

                name = (
                    base.strip("/")
                    .replace("-", " ")
                    .replace("_", " ")
                    .title()
                )

                services.append({
                    "name": name,
                    "path": base + "/",
                    "upstream": upstream,
                })

        # Also handle normal nested route arrays.
        for child in node.get("routes", []):
            walk(child)

    for route in routes:
        walk(route)

    services.sort(key=lambda x: x["name"].lower())

    return services

class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filename):
        path = STATIC_DIR / filename

        if not path.exists():
            self.send_error(404)
            return

        content = path.read_bytes()

        if filename.endswith(".html"):
            content_type = "text/html; charset=utf-8"
        elif filename.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif filename.endswith(".js"):
            content_type = "application/javascript"
        else:
            content_type = "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/services":
            self.send_json({
                "services": discover_services()
            })
            return

        if path == "/api/health":
            self.send_json({
                "status": "online",
                "services": len(discover_services())
            })
            return

        if path == "/":
            self.serve_file("index.html")
            return

        if path in ("/app.js", "/style.css"):
            self.serve_file(path.lstrip("/"))
            return

        self.send_error(404)

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)

print(f"Dashboard listening on :{PORT}")

server.serve_forever()
