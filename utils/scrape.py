"""
Web scraping and content cleaning utilities for podcast generation.
Uses trafilatura for robust article extraction and cleaning.
"""

import requests
from typing import Dict, Optional
import re
from urllib.parse import urljoin, urlparse

try:
    import trafilatura
    from trafilatura.settings import use_config
    from readability import Document
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

def scrape_and_clean(url: str) -> Dict[str, str]:
    """
    Scrape and clean article content from a URL
    
    Args:
        url: URL of the article to scrape
        
    Returns:
        Dictionary with 'title' and 'text' keys containing cleaned content
        
    Raises:
        Exception: If scraping fails or dependencies are missing
    """
    if not SCRAPING_AVAILABLE:
        raise Exception("Scraping dependencies not available. Please install trafilatura and readability-lxml.")
    
    if not url or not url.strip():
        raise Exception("URL cannot be empty")
    
    # Validate URL format
    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            raise Exception("Invalid URL format")
    except Exception:
        raise Exception("Invalid URL format")
    
    try:
        # Step 1: Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url.strip(), headers=headers, timeout=30)
        response.raise_for_status()
        
        # Step 2: Extract content using trafilatura (primary method)
        config = use_config()
        config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
        
        extracted = trafilatura.extract(
            response.text,
            url=url,
            config=config,
            include_comments=False,
            include_tables=True,
            include_formatting=False,
            favor_precision=True
        )
        
        # Step 3: Extract title using trafilatura
        title = trafilatura.extract_metadata(response.text, fast=True)
        article_title = ""
        
        if title and hasattr(title, 'title') and title.title:
            article_title = title.title
        else:
            # Fallback: try to extract title from HTML
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    article_title = title_tag.get_text().strip()
            except:
                article_title = "Untitled Article"
        
        # Step 4: Fallback to readability if trafilatura fails
        if not extracted or len(extracted.strip()) < 100:
            try:
                doc = Document(response.text)
                extracted = doc.summary()
                if not article_title:
                    article_title = doc.title()
                
                # Clean up readability output
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(extracted, 'html.parser')
                extracted = soup.get_text()
                
            except Exception as e:
                raise Exception(f"Both trafilatura and readability extraction failed: {str(e)}")
        
        if not extracted or len(extracted.strip()) < 50:
            raise Exception("Could not extract meaningful content from the article")
        
        # Step 5: Clean and normalize the extracted text
        cleaned_text = _clean_extracted_text(extracted)
        cleaned_title = _clean_title(article_title)
        
        return {
            "title": cleaned_title,
            "text": cleaned_text,
            "url": url
        }
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch webpage: {str(e)}")
    except Exception as e:
        if "extraction failed" in str(e).lower():
            raise e
        raise Exception(f"Error processing article: {str(e)}")

def _clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted article text
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common navigation/footer text patterns
    patterns_to_remove = [
        r'Subscribe to our newsletter.*',
        r'Follow us on.*',
        r'Share this article.*',
        r'Related articles.*',
        r'You might also like.*',
        r'Advertisement.*',
        r'Click here to.*',
        r'Sign up for.*',
        r'Cookie policy.*',
        r'Privacy policy.*',
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[-]{3,}', '---', text)
    
    # Clean up spacing around punctuation
    text = re.sub(r'\s+([.!?])', r'\1', text)
    text = re.sub(r'([.!?])\s*([.!?])', r'\1 \2', text)
    
    # Remove very short lines that are likely navigation/UI elements
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Keep lines that are substantial or contain sentence-ending punctuation
        if len(line) > 15 or (len(line) > 5 and any(punct in line for punct in '.!?')):
            cleaned_lines.append(line)
    
    text = ' '.join(cleaned_lines)
    
    # Final cleanup
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def _clean_title(title: str) -> str:
    """
    Clean and normalize article title
    
    Args:
        title: Raw title text
        
    Returns:
        Cleaned title
    """
    if not title:
        return "Untitled Article"
    
    # Remove common title suffixes
    suffixes_to_remove = [
        r'\s*-\s*.*?News.*',
        r'\s*\|\s*.*',
        r'\s*-\s*.*?\.com.*',
        r'\s*-\s*Home.*',
    ]
    
    for suffix in suffixes_to_remove:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    # Clean up whitespace and punctuation
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Remove excessive punctuation
    title = re.sub(r'[.]{2,}', '', title)
    
    # Ensure reasonable length
    if len(title) > 100:
        title = title[:97] + "..."
    
    return title if title else "Untitled Article"

def test_scraping_setup() -> bool:
    """
    Test if scraping dependencies are available
    
    Returns:
        True if scraping is available, False otherwise
    """
    return SCRAPING_AVAILABLE

def get_scraping_error() -> Optional[str]:
    """
    Get the scraping setup error message if any
    
    Returns:
        Error message if scraping is disabled, None otherwise
    """
    return None if SCRAPING_AVAILABLE else "Missing dependencies: trafilatura, readability-lxml"
