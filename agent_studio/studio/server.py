"""Minimal local HTTP server for the studio (standard library only).

Binds to 127.0.0.1 by default. API keys stay in the server's environment and are
never sent to the browser.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from studio import service

STATIC = Path(__file__).resolve().parent / "static"
MAX_BODY = 2_000_000


class Handler(BaseHTTPRequestHandler):
    server_version = "ECAAStudio/0.1"

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    # --- helpers ------------------------------------------------------------------
    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(length) or b"{}")

    # --- routes -------------------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/catalog":
            return self._json(200, service.catalog())
        if path in ("/", ""):
            path = "/index.html"
        target = (STATIC / path.lstrip("/")).resolve()
        if STATIC not in target.parents or not target.is_file():
            return self._json(404, {"error": "not found"})
        body = target.read_bytes()
        self.send_response(200)
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_header("Content-Type", kind + ("; charset=utf-8" if kind.startswith("text")
                                                 or kind.endswith("javascript") else ""))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            payload = self._body()
            if path == "/api/oracle":
                return self._json(200, service.oracle_for(payload.get("state") or {}))
            if path == "/api/prompt":
                return self._json(200, service.system_prompt_for(payload.get("agent") or {},
                                                                 payload.get("domain", "")))
            if path == "/api/run":
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()
                for line in service.stream_run(payload):
                    try:
                        self.wfile.write(line.encode("utf-8"))
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break  # the browser went away; the run finishes in the background
                return None
        except (ValueError, KeyError, TypeError) as error:
            return self._json(400, {"error": str(error)})
        return self._json(404, {"error": "not found"})


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines into the environment without overriding or printing them."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if value.strip():
                os.environ.setdefault(key.strip(), value.strip())


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    url = f"http://{host}:{port}/"
    print(f"ECAA Agent Studio running at {url}  (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    _load_dotenv(service.ROOT / ".env")
    serve(args.host, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
