from __future__ import annotations
from typing import List, Set
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup

IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp)(\?|$)", re.IGNORECASE)

def is_probably_image_url(url: str) -> bool:
    return bool(IMAGE_EXT_RE.search(url))

def extract_image_urls_from_page(page_url: str, timeout: int = 20, max_images: int = 40) -> List[str]:
    """
    Fetches the page HTML and extracts candidate image URLs.
    This will NOT work for pages that require JS rendering for content.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioAssetFinder/1.0)"}
    resp = requests.get(page_url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    found: Set[str] = set()

    # og:image
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        found.add(urljoin(page_url, og["content"]))

    # twitter:image
    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        found.add(urljoin(page_url, tw["content"]))

    # <img src=""> and srcset
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            found.add(urljoin(page_url, src))

        srcset = img.get("srcset")
        if srcset:
            parts = [p.strip().split(" ")[0] for p in srcset.split(",") if p.strip()]
            for p in parts:
                found.add(urljoin(page_url, p))

    # Filter
    clean: List[str] = []
    for u in found:
        if u.startswith("http"):
            clean.append(u)

    # Prefer direct image URLs first
    clean.sort(key=lambda x: (not is_probably_image_url(x), len(x)))
    return clean[:max_images]
