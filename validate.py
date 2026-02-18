from __future__ import annotations
from dataclasses import dataclass
import requests

@dataclass
class UrlCheck:
    ok: bool
    status: int
    content_type: str
    final_url: str
    reason: str = ""

def check_image_url(url: str, timeout: int = 15) -> UrlCheck:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioAssetFinder/1.0)"}
    try:
        r = requests.head(url, headers=headers, allow_redirects=True, timeout=timeout)
        status = r.status_code
        ct = (r.headers.get("Content-Type") or "").lower()
        final_url = r.url
        if status >= 400:
            return UrlCheck(False, status, ct, final_url, "HTTP error")
        if "image/" not in ct:
            return UrlCheck(False, status, ct, final_url, "Not an image content-type")
        return UrlCheck(True, status, ct, final_url, "")
    except Exception as e:
        return UrlCheck(False, 0, "", url, f"HEAD failed: {e}")
