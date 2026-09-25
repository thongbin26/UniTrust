"""Safe, bounded public-web content acquisition for user-supplied URLs."""

from app.url_fetch.errors import URLFetchError
from app.url_fetch.fetcher import WebContentFetcher
from app.url_fetch.models import URLExtractionResult

__all__ = ["URLExtractionResult", "URLFetchError", "WebContentFetcher"]
