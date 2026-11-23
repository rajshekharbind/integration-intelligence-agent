import hashlib
import json
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import httpx
from src.config import REQUEST_TIMEOUT, CACHE_DIR

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (IntegrationIntelligenceAgent/1.0)"


def _get_cache_path(url: str):
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"page_{url_hash}.json"


def fetch_page_content(url: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetches a documentation page, parses clean text, extracts metadata,
    and returns status code, title, text snippet, and full clean text.
    """
    cache_file = _get_cache_path(url)
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            status_code = resp.status_code
            html = resp.text

            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts, styles, navbars, and footers for clean content
            for tag in soup(["script", "style", "nav", "footer", "svg"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if desc_tag and desc_tag.get("content"):
                meta_desc = desc_tag["content"].strip()

            # Extract headers and paragraphs
            body_text = soup.get_text(separator=" ", strip=True)
            # Limit clean text length to prevent LLM context overflow
            clean_text = body_text[:8000]

            result = {
                "url": str(resp.url),
                "http_status": status_code,
                "title": title or meta_desc[:80],
                "description": meta_desc,
                "clean_text": clean_text,
                "success": status_code < 400
            }

            if use_cache:
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f)
                except Exception:
                    pass

            return result

    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        # Return fallback object
        return {
            "url": url,
            "http_status": 0,
            "title": "Unreachable / Offline",
            "description": str(e),
            "clean_text": f"Error fetching documentation page: {e}",
            "success": False
        }
