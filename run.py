#!/usr/bin/env python3
"""Cross-platform launcher for the English Learning app (Windows / macOS).

Starts the local web server and opens the default browser. Run with:

    python run.py
"""

from __future__ import annotations

import threading
import webbrowser

import uvicorn

from app.config import load_settings


def _open_browser(url: str) -> None:
    # Small delay so the server is ready before the tab opens.
    timer = threading.Timer(1.5, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()


def main() -> None:
    settings = load_settings()
    url = f"http://{settings.host}:{settings.port}/"
    print(f"English Learning with AI → {url}")
    print("（停止するには Ctrl+C）")
    _open_browser(url)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
