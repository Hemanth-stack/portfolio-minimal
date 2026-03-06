"""One-time bulk indexing: submit all site URLs to IndexNow + Google Indexing API."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session
from app.models import Post, Project
from app.config import get_settings
from app.services.seo import notify_indexnow, notify_google_indexing, ping_sitemap, _log_indexing


STATIC_PAGES = [
    "/",
    "/blog",
    "/projects",
    "/about",
    "/contact",
    "/services",
    "/now",
    "/resume",
]


async def main():
    settings = get_settings()
    base = settings.site_url

    # Collect all URLs
    urls = [f"{base}{p}" for p in STATIC_PAGES]

    async with async_session() as db:
        # Published blog posts
        result = await db.execute(select(Post).where(Post.published == True))
        for post in result.scalars().all():
            urls.append(f"{base}/blog/{post.slug}")

        # Projects
        result = await db.execute(select(Project))
        for project in result.scalars().all():
            urls.append(f"{base}/projects/{project.slug}")

        print(f"Submitting {len(urls)} URLs for indexing...\n")
        for u in urls:
            print(f"  {u}")
        print()

        # 1) IndexNow — batch submit all at once
        if settings.indexnow_api_key:
            print("→ Sending to IndexNow (batch)...")
            await notify_indexnow(urls, db)
            print("  Done.\n")
        else:
            print("⚠ IndexNow not configured (INDEXNOW_API_KEY missing)\n")

        # 2) Google Indexing API — one URL at a time (API limit)
        if settings.google_service_account_json:
            print("→ Sending to Google Indexing API (one by one)...")
            for i, url in enumerate(urls, 1):
                print(f"  [{i}/{len(urls)}] {url}")
                await notify_google_indexing(url, db)
                await asyncio.sleep(0.5)  # rate-limit courtesy
            print("  Done.\n")
        else:
            print("⚠ Google Indexing API not configured (GOOGLE_SERVICE_ACCOUNT_JSON missing)\n")

        # 3) Ping sitemap
        print("→ Pinging sitemap...")
        await ping_sitemap()
        print("  Done.\n")

    print("✓ Bulk indexing complete!")


if __name__ == "__main__":
    asyncio.run(main())
