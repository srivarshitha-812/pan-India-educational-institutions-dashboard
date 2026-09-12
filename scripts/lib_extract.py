"""
lib_extract.py — Common extraction utilities for Pan-India Census
=================================================================
Shared by all source-specific extraction scripts.

Features:
- Rate-limited HTTP (default 1 req/s)
- Exponential backoff on 429/503
- Checkpoint save/load (JSON)
- Resumable iteration
- Consistent logging
"""

import json
import os
import time
import logging
import urllib.request
import urllib.error
import gzip
from datetime import date
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / "data" / "raw"
CHECKPOINT_DIR = BASE / "data" / "checkpoints"
LOG_DIR = BASE / "data" / "logs"
RESEARCH_DIR = BASE / "data" / "SOURCE_RESEARCH"

for d in (RAW_DIR, CHECKPOINT_DIR, LOG_DIR, RESEARCH_DIR):
    d.mkdir(parents=True, exist_ok=True)

EXTRACTION_DATE = str(date.today())


# ── Logging ──────────────────────────────────────────────────────────────────
def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        if log_file:
            fh = logging.FileHandler(LOG_DIR / log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
    return logger


# ── HTTP utilities ────────────────────────────────────────────────────────────
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}


class RateLimitedSession:
    """
    Simple rate-limited HTTP session with exponential backoff.

    Args:
        rps: Requests per second (default 1.0)
        max_retries: Max retry attempts on 429/503
        timeout: Socket timeout in seconds
        extra_headers: Additional headers merged with defaults
    """

    def __init__(
        self,
        rps: float = 1.0,
        max_retries: int = 5,
        timeout: int = 20,
        extra_headers: dict | None = None,
    ):
        self.min_interval = 1.0 / rps
        self.max_retries = max_retries
        self.timeout = timeout
        self.headers = dict(DEFAULT_HEADERS)
        if extra_headers:
            self.headers.update(extra_headers)
        self._last_call = 0.0

    def _wait(self):
        elapsed = time.monotonic() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()

    def get(
        self,
        url: str,
        params: dict | None = None,
        extra_headers: dict | None = None,
        as_json: bool = True,
    ) -> tuple[int, bytes | dict | None]:
        """
        GET request with rate limiting and retry.

        Returns:
            (status_code, parsed_json_or_bytes)
        """
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        hdrs = dict(self.headers)
        if extra_headers:
            hdrs.update(extra_headers)

        delay = 1.0
        for attempt in range(self.max_retries):
            self._wait()
            req = urllib.request.Request(url, headers=hdrs, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    # Decompress if needed
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    if as_json:
                        return resp.status, json.loads(raw.decode("utf-8", errors="replace"))
                    return resp.status, raw
            except urllib.error.HTTPError as e:
                if e.code in (429, 503, 502, 504):
                    wait = delay * (2 ** attempt)
                    print(f"  [RETRY {attempt+1}] {e.code} on {url[:80]}... sleeping {wait:.1f}s")
                    time.sleep(wait)
                    continue
                return e.code, None
            except Exception as ex:
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                    continue
                return 0, None
        return 0, None

    def post(
        self,
        url: str,
        data: bytes | None = None,
        json_body: dict | None = None,
        extra_headers: dict | None = None,
        as_json: bool = True,
    ) -> tuple[int, bytes | dict | None]:
        """POST request with rate limiting and retry."""
        hdrs = dict(self.headers)
        if extra_headers:
            hdrs.update(extra_headers)

        if json_body is not None:
            data = json.dumps(json_body).encode()
            hdrs["Content-Type"] = "application/json"

        delay = 1.0
        for attempt in range(self.max_retries):
            self._wait()
            req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    if as_json:
                        return resp.status, json.loads(raw.decode("utf-8", errors="replace"))
                    return resp.status, raw
            except urllib.error.HTTPError as e:
                if e.code in (429, 503, 502, 504):
                    wait = delay * (2 ** attempt)
                    print(f"  [RETRY {attempt+1}] {e.code} on {url[:80]}... sleeping {wait:.1f}s")
                    time.sleep(wait)
                    continue
                body = b""
                try:
                    body = e.read()
                except Exception:
                    pass
                return e.code, body
            except Exception as ex:
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                    continue
                return 0, None
        return 0, None


# ── Checkpoint utilities ──────────────────────────────────────────────────────
def load_checkpoint(source: str) -> dict:
    path = CHECKPOINT_DIR / f"{source}_checkpoint.json"
    tmp_path = CHECKPOINT_DIR / f"{source}_checkpoint.json.tmp"
    for p in (path, tmp_path):
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load checkpoint from {p}: {e}")
    return {}


def save_checkpoint(source: str, state: dict):
    path = CHECKPOINT_DIR / f"{source}_checkpoint.json"
    tmp_path = CHECKPOINT_DIR / f"{source}_checkpoint.json.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        # On Windows, replace will atomically overwrite path
        tmp_path.replace(path)
    except Exception as e:
        print(f"[ERROR] Failed to save checkpoint for {source}: {e}")


# ── Raw data save/load ────────────────────────────────────────────────────────
def save_raw(source: str, key: str, data: list | dict):
    """Save raw JSON response to data/raw/<source>/ directory."""
    dir_ = RAW_DIR / source.lower()
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{source.lower()}_{key.lower().replace(' ', '_')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_raw(source: str, key: str) -> list | dict | None:
    """Load previously saved raw JSON."""
    path = RAW_DIR / source.lower() / f"{source.lower()}_{key.lower().replace(' ', '_')}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Empty arrays (2 bytes = []) count as "no data"
        if isinstance(data, list) and len(data) == 0:
            return None
        return data
    return None


def existing_states(source: str) -> set:
    """Return set of state keys that already have non-empty raw data."""
    dir_ = RAW_DIR / source.lower()
    if not dir_.exists():
        return set()
    done = set()
    for f in dir_.glob(f"{source.lower()}_*.json"):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and len(data) > 0:
                # Extract state from filename: <source>_<state>_<suffix>.json
                stem = f.stem  # e.g. "aishe_telangana_directory"
                prefix = f"{source.lower()}_"
                if stem.startswith(prefix):
                    rest = stem[len(prefix):]
                    # state is everything before last underscore-separated suffix
                    # e.g. "telangana_directory" → "telangana"
                    parts = rest.rsplit("_", 1)
                    if len(parts) == 2:
                        done.add(parts[0])
                    else:
                        done.add(rest)
        except Exception:
            pass
    return done


# ── Standard Indian states/UTs list ──────────────────────────────────────────
STATES_UTS = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]
