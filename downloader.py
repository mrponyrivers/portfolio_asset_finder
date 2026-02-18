from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import requests


@dataclass
class DownloadResult:
    ok: bool
    filepath: Optional[str]
    reason: str
    content_type: str = ""
    bytes_written: int = 0


def _safe_ext_from_content_type(ct: str) -> str:
    ct = (ct or "").lower()
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "png" in ct:
        return ".png"
    if "webp" in ct:
        return ".webp"
    return ""


def _filename_from_url(url: str) -> str:
    p = urlparse(url).path
    name = Path(p).name
    return name if name else ""


def download_image(url: str, out_dir: Path, base_name: str, min_kb: int = 30, timeout: int = 25) -> DownloadResult:
    """
    Downloads an image URL to out_dir.
    - Skips tiny files (icons/thumbnails) using min_kb threshold
    - Uses content-type to pick extension
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioAssetFinder/1.0)"}

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=timeout)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")

        ext = _safe_ext_from_content_type(ct)
        if not ext:
            # fallback from URL name
            from_url = _filename_from_url(url).lower()
            if from_url.endswith((".jpg", ".jpeg")):
                ext = ".jpg"
            elif from_url.endswith(".png"):
                ext = ".png"
            elif from_url.endswith(".webp"):
                ext = ".webp"

        if not ext:
            return DownloadResult(False, None, "Not an image (content-type not recognized).", ct, 0)

        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        filename = f"{base_name}_{h}{ext}"
        path = out_dir / filename

        total = 0
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                total += len(chunk)

        if total < (min_kb * 1024):
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
            return DownloadResult(False, None, f"Skipped: too small ({total/1024:.1f} KB).", ct, total)

        return DownloadResult(True, str(path), "Downloaded", ct, total)

    except Exception as e:
        return DownloadResult(False, None, f"Download failed: {e}", "", 0)
