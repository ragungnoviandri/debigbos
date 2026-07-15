"""API Logger — writes request/response details to ~/.bigbos/logs/api.log."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class ApiLogger:
    """Logs API calls to a file for debugging."""

    def __init__(self):
        self.log_dir = Path.home() / ".bigbos" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "api.log"

    def log_request(self, provider: str, model: str, method: str,
                    url: str, headers: dict, body: dict, call_ref: Any = None) -> None:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            body_short = json.dumps(body, default=str)[:500]
            entry = (
                f"[{ts}] REQ | {provider}/{model}\n"
                f"  {method} {url}\n"
                f"  body: {body_short}\n"
            )
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def log_response(self, provider: str, model: str, status_code: int,
                     response_body: str = "", error: str = "",
                     usage: dict = None, call_ref: Any = None) -> None:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            if error:
                entry = f"[{ts}] ERR | {provider}/{model} | {error[:300]}\n"
            else:
                resp_short = (response_body or "")[:500]
                usage_str = f" usage={usage}" if usage else ""
                entry = (
                    f"[{ts}] RES | {provider}/{model} | status={status_code}{usage_str}\n"
                    f"  body: {resp_short}\n"
                )
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass


_logger = None


def get_logger() -> ApiLogger:
    global _logger
    if _logger is None:
        _logger = ApiLogger()
    return _logger
