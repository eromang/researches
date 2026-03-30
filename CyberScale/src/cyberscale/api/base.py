"""Shared HTTP session with retry logic and rate limiting."""

import time
import requests
from typing import Any


class APIClient:
    """Base HTTP client with session pooling, rate limiting, and retry."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 15,
        min_interval: float = 1.0,
        user_agent: str = "CyberScale/0.1.0",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.min_interval = min_interval
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.monotonic()

    def get(self, path: str, params: dict | None = None) -> Any:
        self._rate_limit()
        url = f"{self.base_url}{path}"
        response = self._session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._session.close()
