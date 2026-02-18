from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import os
import requests
from serpapi import GoogleSearch


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    thumbnail_url: str = ""
    image_url: str = ""
    source: str = "web"


class BaseSearchProvider:
    def search(self, query: str, count: int = 10) -> List[SearchResult]:
        raise NotImplementedError

    def search_images(self, query: str, count: int = 20, tbs: str = "itp:photo,isz:l") -> List[SearchResult]:
        raise NotImplementedError("Image search not supported by this provider.")


class MockSearchProvider(BaseSearchProvider):
    def search(self, query: str, count: int = 10) -> List[SearchResult]:
        return [
            SearchResult(
                title="Example result (replace with real search provider)",
                url="https://example.com",
                snippet=f"Query was: {query}",
                source="mock",
            )
        ]

    def search_images(self, query: str, count: int = 20, tbs: str = "itp:photo,isz:l") -> List[SearchResult]:
        return [
            SearchResult(
                title="Example image result (mock)",
                url="https://example.com",
                snippet=f"Query was: {query}",
                source="mock_images",
            )
        ]


class BingWebSearchProvider(BaseSearchProvider):
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or os.environ.get("BING_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
        self.api_key = api_key or os.environ.get("BING_API_KEY")

    def search(self, query: str, count: int = 10) -> List[SearchResult]:
        if not self.api_key:
            raise RuntimeError("Missing BING_API_KEY env var.")
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": count, "textDecorations": False, "textFormat": "Raw"}
        r = requests.get(self.endpoint, headers=headers, params=params, timeout=20)
        r.raise_for_status()
        data: Dict[str, Any] = r.json()

        results: List[SearchResult] = []
        for item in data.get("webPages", {}).get("value", []):
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", "") or "",
                    source="bing_web",
                )
            )
        return results


class SerpApiSearchProvider(BaseSearchProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SERPAPI_API_KEY")

    def _require_key(self):
        if not self.api_key:
            raise RuntimeError("Missing SERPAPI_API_KEY env var.")

    def search(self, query: str, count: int = 10) -> List[SearchResult]:
        self._require_key()
        params = {"engine": "google", "q": query, "api_key": self.api_key, "num": min(count, 10)}
        data = GoogleSearch(params).get_dict()

        results: List[SearchResult] = []
        organic = data.get("organic_results", []) or []
        for item in organic[:count]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "") or "",
                    source="serpapi_web",
                )
            )
        return results

    def search_images(self, query: str, count: int = 20, tbs: str = "itp:photo,isz:l") -> List[SearchResult]:
        self._require_key()
        params = {
            "engine": "google_images",
            "q": query,
            "api_key": self.api_key,
            "ijn": 0,
            "tbs": tbs,
        }
        data = GoogleSearch(params).get_dict()

        results: List[SearchResult] = []
        images = data.get("images_results", []) or []
        for item in images[:count]:
            results.append(
                SearchResult(
                    title=item.get("title", "") or item.get("source", ""),
                    url=item.get("link", "") or "",
                    snippet=item.get("source", "") or "",
                    thumbnail_url=item.get("thumbnail", "") or "",
                    image_url=item.get("original", "") or "",
                    source="serpapi_images",
                )
            )
        return results
