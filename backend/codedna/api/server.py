"""Start the local API (``codedna serve``)."""

from __future__ import annotations

import ipaddress
import json
import sys

from codedna.api.app import create_app, new_token


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def serve(host: str = "127.0.0.1", port: int = 8765, *, token: str | None = None,
          allow_build: bool = False) -> int:
    if not is_loopback(host):
        print(f"error: refusing to listen on {host}; the CodeDNA API is loopback-only",
              file=sys.stderr)
        return 1
    import uvicorn

    token = token or new_token()
    # One JSON line on stdout so the IDE can read the address and token.
    print(json.dumps({"url": f"http://{host}:{port}", "token": token,
                      "allow_build": allow_build}), flush=True)
    if allow_build:
        print("warning: /api/run-tests is enabled; it executes project code on request",
              file=sys.stderr)
    uvicorn.run(create_app(token, allow_build=allow_build), host=host, port=port,
                log_level="warning")
    return 0
