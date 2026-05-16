"""
Proxy LinkedIn OAuth local.
Si LINKEDIN_REDIRECT_URI pointe vers un port local (ex. http://localhost:8766/callback),
ce module démarre un mini-serveur HTTP qui transfère la requête vers le callback
FastAPI réel (backend-api : /api/social/linkedin/callback).
"""

from __future__ import annotations

import logging
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("brandai.linkedin_proxy")

from app.core.config import settings as _cfg
BRANDAI_API_BASE_URL = _cfg.BRANDAI_API_BASE_URL


def canonical_linkedin_callback(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/api/social/linkedin/callback"


def should_run_proxy(linkedin_redirect_uri: str) -> bool:
    u = (linkedin_redirect_uri or "").strip()
    if not u:
        return False
    return u.rstrip("/") != canonical_linkedin_callback(BRANDAI_API_BASE_URL).rstrip("/")


def start_linkedin_proxy(
    linkedin_redirect_uri: str,
) -> Tuple[Optional[HTTPServer], Optional[threading.Thread]]:
    if not should_run_proxy(linkedin_redirect_uri):
        return None, None

    parsed = urlparse((linkedin_redirect_uri or "").strip())
    if not parsed.hostname or parsed.port is None:
        logger.warning(
            "LINKEDIN_REDIRECT_URI doit inclure un port explicite (ex. http://localhost:8766/callback)."
        )
        return None, None

    forward = canonical_linkedin_callback(BRANDAI_API_BASE_URL)
    expected_path = parsed.path or "/"

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            req_path = self.path.split("?", 1)[0]
            if req_path.rstrip("/") != expected_path.rstrip("/"):
                self.send_error(404, "Not Found")
                return
            q = self.path.split("?", 1)[1] if "?" in self.path else ""
            target = f"{forward}?{q}" if q else forward
            try:
                with urllib.request.urlopen(urllib.request.Request(target), timeout=120) as resp:
                    body = resp.read()
                    ct = resp.headers.get("Content-Type", "text/html; charset=utf-8")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                err_body = e.read() if e.fp else b""
                self.send_response(e.code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
            except OSError as e:
                msg = (
                    f"<html><body><p>Proxy LinkedIn → backend-api impossible ({e}).</p></body></html>"
                ).encode("utf-8")
                self.send_response(502)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            logger.debug("%s - %s", self.address_string(), format % args)

    bind_host = parsed.hostname
    try:
        server = HTTPServer((bind_host, parsed.port), _Handler)
    except OSError as e:
        logger.error(
            "Impossible d'écouter LinkedIn OAuth sur %s:%s (%s). Port déjà utilisé ?",
            bind_host, parsed.port, e,
        )
        return None, None

    def _run() -> None:
        logger.info("Proxy LinkedIn OAuth: %s → %s", linkedin_redirect_uri.strip(), forward)
        server.serve_forever()

    thread = threading.Thread(target=_run, name="linkedin-oauth-proxy", daemon=True)
    thread.start()
    return server, thread


def stop_linkedin_proxy(server: Optional[HTTPServer]) -> None:
    if server is None:
        return
    try:
        server.shutdown()
    except Exception:
        pass
