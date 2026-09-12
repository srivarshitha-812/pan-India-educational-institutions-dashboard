"""
Base source scraper class with rate limiting, exponential backoff, and caching.
"""
import time
import json
import requests
import urllib3
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import DEFAULT_HEADERS, REQUEST_TIMEOUT, RATE_LIMIT_DELAY, RAW_DIRS
from src.database import Database
from src.checkpoint import CheckpointManager
from src.deduplicator import Deduplicator
from src.logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseSourceCollector:
    source_name: str = "base"

    def __init__(self, db: Database, checkpoint_mgr: CheckpointManager, deduplicator: Deduplicator):
        self.db = db
        self.checkpoint_mgr = checkpoint_mgr
        self.deduplicator = deduplicator
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify = False
        self.last_request_time = 0.0
        self.raw_dir = RAW_DIRS.get(self.source_name, RAW_DIRS["udise"])

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
        reraise=True
    )
    def fetch_url(self, url: str, method: str = "GET", params: Optional[Dict] = None, data: Optional[Any] = None, json_data: Optional[Any] = None, headers: Optional[Dict] = None) -> requests.Response:
        self._rate_limit()
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        logger.debug("[%s] %s -> %s", self.source_name.upper(), method, url)
        if method.upper() == "GET":
            response = self.session.get(url, params=params, headers=req_headers, timeout=REQUEST_TIMEOUT)
        elif method.upper() == "POST":
            response = self.session.post(url, params=params, data=data, json=json_data, headers=req_headers, timeout=REQUEST_TIMEOUT)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response

    def save_raw_data(self, filename: str, content: Union[str, bytes, Dict, List]):
        """Saves raw snapshot of data to data/raw/<source>/."""
        file_path = self.raw_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, (dict, list)):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        elif isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))
        logger.debug("[%s] Saved raw cache to %s", self.source_name.upper(), file_path)
