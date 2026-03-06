import asyncio
import logging
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

logger = logging.getLogger(__name__)


async def notify_indexnow(urls: list[str], db: Optional[AsyncSession] = None):
    """Notify IndexNow API about updated URLs (Bing, Yandex, Google)."""
    settings = get_settings()
    key = settings.indexnow_api_key
    if not key or not urls:
        return

    host = settings.site_url.replace("https://", "").replace("http://", "")
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{settings.site_url}/{key}.txt",
        "urlList": urls,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.indexnow.org/indexnow",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            logger.info(f"IndexNow response: {resp.status_code} for {len(urls)} URLs")
            if db:
                await _log_indexing(db, urls, "indexnow", resp.status_code, resp.text)
    except Exception as e:
        logger.error(f"IndexNow error: {e}")


async def notify_google_indexing(url: str, db: Optional[AsyncSession] = None, action: str = "URL_UPDATED"):
    """Notify Google Indexing API about a URL update."""
    settings = get_settings()
    creds_path = settings.google_service_account_json
    if not creds_path:
        return

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GoogleAuthRequest

        SCOPES = ["https://www.googleapis.com/auth/indexing"]
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )
        credentials.refresh(GoogleAuthRequest())
        token = credentials.token

        payload = {"url": url, "type": action}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://indexing.googleapis.com/v3/urlNotifications:publish",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )
            logger.info(f"Google Indexing API response: {resp.status_code} for {url}")
            if db:
                await _log_indexing(db, [url], "google", resp.status_code, resp.text)
    except ImportError:
        logger.warning("google-auth not installed, skipping Google Indexing API")
    except Exception as e:
        logger.error(f"Google Indexing API error: {e}")


async def ping_sitemap():
    """Ping Google with the sitemap URL."""
    settings = get_settings()
    sitemap_url = f"{settings.site_url}/sitemap.xml"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://www.google.com/ping?sitemap={sitemap_url}"
            )
            logger.info(f"Sitemap ping response: {resp.status_code}")
    except Exception as e:
        logger.error(f"Sitemap ping error: {e}")


async def notify_search_engines(url: str, db: Optional[AsyncSession] = None):
    """Fire-and-forget: notify all search engines about a URL."""
    settings = get_settings()
    tasks = [ping_sitemap()]

    if settings.indexnow_api_key:
        tasks.append(notify_indexnow([url], db))
    if settings.google_service_account_json:
        tasks.append(notify_google_indexing(url, db))

    await asyncio.gather(*tasks, return_exceptions=True)


async def _log_indexing(db: AsyncSession, urls: list[str], service: str, status_code: int, response: str):
    """Log indexing notification to database."""
    from app.models import IndexingLog

    for url in urls:
        log = IndexingLog(
            url=url,
            service=service,
            status_code=status_code,
            response=response[:500] if response else None,
        )
        db.add(log)

    try:
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log indexing: {e}")
        await db.rollback()
