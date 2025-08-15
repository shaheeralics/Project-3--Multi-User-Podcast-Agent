\
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from readability import Document
import trafilatura

def _strip(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text

def scrape_and_clean(url: str) -> dict:
    """
    Fetches the article at URL, extracts readable content, and returns {title,text}.
    Uses trafilatura first, falls back to readability.
    """
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (podcastify)"})
    r.raise_for_status()

    # Try trafilatura
    extracted = trafilatura.extract(r.text, include_comments=False, include_tables=False, favor_recall=True)
    title = None
    if not extracted:
        # Fallback to readability
        doc = Document(r.text)
        title = doc.short_title()
        html = doc.summary(html_partial=True)
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)
    else:
        soup = BeautifulSoup(r.text, "lxml")
        t = soup.find("title")
        title = _strip(t.get_text()) if t else urlparse(url).netloc
        text = _strip(extracted)

    # Basic cleanup
    text = re.sub(r"(\n\s*){2,}", "\n\n", text)
    text = re.sub(r"\s{2,}", " ", text)

    return {"title": title or url, "text": text}
