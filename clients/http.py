from __future__ import annotations
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class HTTPError(Exception):
    pass

class HttpClient:
    def __init__(self, base_url: str, headers: dict | None = None, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout

    @retry(
        retry=retry_if_exception_type(HTTPError),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
        if resp.status_code >= 400:
            raise HTTPError(f"GET {url} -> {resp.status_code}: {resp.text[:200]}")
        return resp.json()
