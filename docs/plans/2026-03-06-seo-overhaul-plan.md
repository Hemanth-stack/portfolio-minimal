# SEO Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Every page gets proper SEO metadata, new blog posts auto-notify search engines, RSS feed for discoverability, and an admin SEO dashboard for monitoring.

**Architecture:** Template-layer fixes for meta tags + new `app/services/seo.py` service for IndexNow/Google Indexing API + new admin dashboard route + new RSS feed route. All index notifications are fire-and-forget async tasks.

**Tech Stack:** FastAPI, Jinja2, SQLAlchemy async, google-auth, httpx (already installed), Alembic

---

### Task 1: Add IndexingLog Model + Migration

**Files:**
- Modify: `app/models.py:164-173`
- Create: `alembic/versions/005_add_indexing_logs.py`

**Step 1: Add IndexingLog model to models.py**

After the `ContactMessage` class (line 164), add:

```python
class IndexingLog(Base):
    __tablename__ = "indexing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False)
    service = Column(String(20), nullable=False)  # 'indexnow' or 'google'
    status_code = Column(Integer, nullable=True)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

Add `Text` to the SQLAlchemy imports if not present.

**Step 2: Create Alembic migration**

```bash
docker-compose exec web alembic revision --autogenerate -m "add_indexing_logs"
```

Or create manually as `005_add_indexing_logs.py`:

```python
"""add indexing_logs table

Revision ID: 005_add_indexing_logs
Revises: 004_add_post_views_table
"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_indexing_logs'
down_revision = '004_add_post_views_table'

def upgrade():
    op.create_table(
        'indexing_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('service', sa.String(20), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table('indexing_logs')
```

**Step 3: Run migration**

```bash
docker-compose exec web alembic upgrade head
```

**Step 4: Commit**

```bash
git add app/models.py alembic/versions/005_add_indexing_logs.py
git commit -m "feat: add IndexingLog model and migration"
```

---

### Task 2: Add Config Settings for IndexNow + Google API

**Files:**
- Modify: `app/config.py:6-35`

**Step 1: Add new settings**

After the existing `smtp_from` field, add:

```python
    # SEO / Indexing
    indexnow_api_key: str = ""
    google_service_account_json: str = ""  # Path to JSON file inside container
```

**Step 2: Add to .env.example or document**

In `.env` (or note for the user), the new env vars are:
```
INDEXNOW_API_KEY=<random-32-char-hex>
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

**Step 3: Commit**

```bash
git add app/config.py
git commit -m "feat: add IndexNow and Google Indexing API config settings"
```

---

### Task 3: Create SEO Service (IndexNow + Google Indexing + Sitemap Ping)

**Files:**
- Create: `app/services/seo.py`

**Step 1: Create the service file**

```python
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
```

**Step 2: Commit**

```bash
git add app/services/seo.py
git commit -m "feat: add SEO service with IndexNow, Google Indexing API, sitemap ping"
```

---

### Task 4: Add google-auth to Requirements

**Files:**
- Modify: `requirements.txt`

**Step 1: Add google-auth**

After the `python-jose` line in the Authentication section, add:

```
google-auth>=2.0.0
```

Note: `httpx` is already in requirements.txt (v0.28.1).

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat: add google-auth dependency"
```

---

### Task 5: Hook Indexing into Admin Post Create/Update

**Files:**
- Modify: `app/routers/admin.py:249-251` (create_post commit + redirect)
- Modify: `app/routers/admin.py:329-331` (update_post commit + redirect)

**Step 1: Add import at top of admin.py**

```python
import asyncio
from app.services.seo import notify_search_engines
```

**Step 2: After create_post commit (line 249-251)**

After `await db.commit()` and before the `return RedirectResponse`, add:

```python
    if published:
        url = f"{get_settings().site_url}/blog/{post.slug}"
        asyncio.create_task(notify_search_engines(url, db))
```

**Step 3: After update_post commit (line 329-331)**

Same pattern — after `await db.commit()`, before redirect:

```python
    if post.published:
        url = f"{get_settings().site_url}/blog/{post.slug}"
        asyncio.create_task(notify_search_engines(url, db))
```

**Step 4: Commit**

```bash
git add app/routers/admin.py
git commit -m "feat: auto-notify search engines on post publish/update"
```

---

### Task 6: Add RSS Feed + IndexNow Verification Routes

**Files:**
- Modify: `app/routers/public.py` (add 2 new routes at end, before sitemap or after it)

**Step 1: Add RSS feed route**

```python
@router.get("/feed.xml")
@router.get("/rss.xml")
async def rss_feed(db: AsyncSession = Depends(get_db)):
    """Generate RSS 2.0 feed for blog posts."""
    settings = get_settings()
    base_url = settings.site_url

    result = await db.execute(
        select(Post).where(Post.published == True).order_by(Post.created_at.desc()).limit(20)
    )
    posts = result.scalars().all()

    from email.utils import format_datetime
    from datetime import timezone

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
    xml += '  <channel>\n'
    xml += f'    <title>{settings.site_name}</title>\n'
    xml += f'    <link>{base_url}/blog</link>\n'
    xml += f'    <description>{settings.site_tagline}</description>\n'
    xml += f'    <language>en-us</language>\n'
    xml += f'    <atom:link href="{base_url}/feed.xml" rel="self" type="application/rss+xml" />\n'

    for post in posts:
        pub_date = post.created_at.replace(tzinfo=timezone.utc)
        xml += '    <item>\n'
        xml += f'      <title>{post.title}</title>\n'
        xml += f'      <link>{base_url}/blog/{post.slug}</link>\n'
        xml += f'      <guid isPermaLink="true">{base_url}/blog/{post.slug}</guid>\n'
        xml += f'      <pubDate>{format_datetime(pub_date)}</pubDate>\n'
        xml += f'      <description>{post.excerpt or ""}</description>\n'
        if hasattr(post, 'categories') and post.categories:
            for cat in post.categories:
                xml += f'      <category>{cat.name}</category>\n'
        xml += '    </item>\n'

    xml += '  </channel>\n'
    xml += '</rss>'

    return Response(content=xml, media_type="application/rss+xml")
```

**Step 2: Add IndexNow verification route**

```python
@router.get("/{key}.txt")
async def indexnow_verification(key: str):
    """Serve IndexNow API key verification file."""
    settings = get_settings()
    if settings.indexnow_api_key and key == settings.indexnow_api_key:
        return Response(content=settings.indexnow_api_key, media_type="text/plain")
    from fastapi import HTTPException
    raise HTTPException(status_code=404)
```

**Important:** This catch-all route must be defined LAST in public.py to avoid interfering with other routes.

**Step 3: Commit**

```bash
git add app/routers/public.py
git commit -m "feat: add RSS feed and IndexNow verification routes"
```

---

### Task 7: Add Missing Pages to Sitemap + Services Route

**Files:**
- Modify: `app/routers/public.py:866-873` (sitemap pages array)
- Modify: `app/routers/public.py` (add /services route if missing)

**Step 1: Add /services route**

The template exists but has no route. Add before the sitemap section:

```python
@router.get("/services", response_class=HTMLResponse)
async def services_page(request: Request, db: AsyncSession = Depends(get_db)):
    site = await get_site_context(db)
    return templates.TemplateResponse("services.html", {
        "request": request,
        "settings": get_settings(),
        "site": site,
        "is_admin": is_admin(request),
    })
```

**Step 2: Add missing pages to sitemap**

In the `pages` list inside `sitemap_xml()` (line 866), add after the contact entry:

```python
        {"loc": "/services", "priority": "0.7", "changefreq": "monthly", "lastmod": now},
        {"loc": "/now", "priority": "0.5", "changefreq": "weekly", "lastmod": now},
        {"loc": "/resume", "priority": "0.5", "changefreq": "monthly", "lastmod": now},
```

**Step 3: Commit**

```bash
git add app/routers/public.py
git commit -m "feat: add /services route and missing pages to sitemap"
```

---

### Task 8: Template SEO Fixes — OG/Twitter Overrides

**Files:**
- Modify: `app/templates/index.html:1-5`
- Modify: `app/templates/about.html:1-5`
- Modify: `app/templates/contact.html:1-5`
- Modify: `app/templates/now.html:1-5`
- Modify: `app/templates/resume.html:1-5`
- Modify: `app/templates/services.html:1-5`
- Modify: `app/templates/projects/list.html:1-5`
- Modify: `app/templates/projects/detail.html:1-5`

**Pattern:** For each template, after the existing `{% block description %}` line, add:

```jinja2
{% block og_title %}[Page Title] – {{ site.site_name }}{% endblock %}
{% block og_description %}[Same as description]{% endblock %}
{% block twitter_title %}[Page Title] – {{ site.site_name }}{% endblock %}
{% block twitter_description %}[Same as description]{% endblock %}
```

For `index.html`, also add the missing `{% block description %}`:
```jinja2
{% block description %}{{ site.site_name }} – {{ site.site_tagline }}. AI & MLOps Engineer specializing in LLM inference, RAG systems, and production ML pipelines.{% endblock %}
```

For `projects/list.html` and `projects/detail.html`, also fix `settings.site_name` → `site.site_name`.

**Step 1: Apply to all 8 templates** (details per template in implementation)

**Step 2: Commit**

```bash
git add app/templates/
git commit -m "feat: add OG/Twitter meta overrides to all pages"
```

---

### Task 9: Template SEO Fixes — Blog Post Article Meta + Enriched Schemas

**Files:**
- Modify: `app/templates/blog/post.html:1-25`
- Modify: `app/templates/blog/list.html:1` (minified)
- Modify: `app/templates/services.html:1-5`
- Modify: `app/templates/about.html:1-10`
- Modify: `app/templates/projects/detail.html:1-10`

**Step 1: blog/post.html — add article meta + twitter_card**

After the existing schema_extra block, add a `{% block head %}`:

```jinja2
{% block twitter_card %}summary_large_image{% endblock %}

{% block head %}
<meta property="article:published_time" content="{{ post.created_at.isoformat() }}">
<meta property="article:modified_time" content="{{ post.updated_at.isoformat() }}">
<meta property="article:author" content="{{ site.site_name }}">
{% for tag in post.tags %}
<meta property="article:tag" content="{{ tag.name }}">
{% endfor %}
{% endblock %}
```

**Step 2: blog/list.html — add CollectionPage schema**

Add to the minified line:
```jinja2
{% block schema_type %}CollectionPage{% endblock %}
{% block schema_extra %},"mainEntity": {"@type": "Blog", "name": "Blog"}{% endblock %}
```

**Step 3: services.html — add ProfessionalService schema**

```jinja2
{% block schema_type %}ProfessionalService{% endblock %}
{% block schema_extra %},
    "provider": {"@type": "Person", "name": "{{ site.site_name }}"},
    "areaServed": "Worldwide",
    "serviceType": "AI/ML Consulting"{% endblock %}
```

**Step 4: about.html — enrich Person schema**

```jinja2
{% block schema_extra %},
    "jobTitle": "{{ site.site_tagline }}",
    "knowsAbout": ["AI", "MLOps", "LLMs", "RAG Systems", "Machine Learning"]{% endblock %}
```

**Step 5: projects/detail.html — add SoftwareSourceCode schema**

```jinja2
{% block schema_type %}SoftwareSourceCode{% endblock %}
{% block schema_extra %},
    "name": "{{ project.title }}",
    "description": "{{ project.short_description }}"{% endblock %}
```

**Step 6: Commit**

```bash
git add app/templates/
git commit -m "feat: add article meta tags and enriched structured data schemas"
```

---

### Task 10: RSS Autodiscovery in base.html

**Files:**
- Modify: `app/templates/base.html:28-30`

**Step 1: Add RSS link**

After the twitter:image meta tag (line 28), add:

```html
    
    <!-- RSS Feed -->
    <link rel="alternate" type="application/rss+xml" title="{{ site.site_name }} Blog" href="/feed.xml">
```

**Step 2: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: add RSS autodiscovery link in HTML head"
```

---

### Task 11: Admin SEO Dashboard — Route + Template

**Files:**
- Create: `app/templates/admin/seo.html`
- Modify: `app/routers/admin.py` (add /admin/seo route)
- Modify: `app/templates/admin/base.html:352` (add nav link)

**Step 1: Add nav link in admin/base.html**

Before `<span class="spacer">` (line 352), add:

```html
        <a href="/admin/seo">SEO</a>
```

**Step 2: Add /admin/seo route in admin.py**

```python
@router.get("/seo", response_class=HTMLResponse)
async def seo_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    
    # Get all published posts
    result = await db.execute(
        select(Post).where(Post.published == True).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    # Get recent indexing logs
    from app.models import IndexingLog
    result = await db.execute(
        select(IndexingLog).order_by(IndexingLog.created_at.desc()).limit(20)
    )
    logs = result.scalars().all()
    
    settings = get_settings()
    static_pages = ["/", "/blog", "/projects", "/about", "/contact", "/services", "/now", "/resume"]
    
    return templates.TemplateResponse("admin/seo.html", {
        **ctx,
        "posts": posts,
        "logs": logs,
        "static_pages": static_pages,
        "settings": settings,
    })


@router.post("/seo/ping")
async def ping_urls(request: Request, db: AsyncSession = Depends(get_db)):
    """Manually trigger indexing for selected URLs."""
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    form = await request.form()
    urls = form.getlist("urls")
    
    if urls:
        from app.services.seo import notify_indexnow, notify_google_indexing, ping_sitemap
        import asyncio
        
        tasks = [ping_sitemap()]
        settings = get_settings()
        
        if settings.indexnow_api_key:
            tasks.append(notify_indexnow(urls, db))
        if settings.google_service_account_json:
            for url in urls:
                tasks.append(notify_google_indexing(url, db))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    return RedirectResponse("/admin/seo", status_code=303)
```

**Step 3: Create admin/seo.html template**

Template showing:
- Indexing status table (URL, last pinged, status)
- Quick action buttons (Ping All, Submit Sitemap)
- SEO health checklist
- Recent ping logs table

(Full template HTML in implementation — approximately 150 lines)

**Step 4: Commit**

```bash
git add app/routers/admin.py app/templates/admin/seo.html app/templates/admin/base.html
git commit -m "feat: add admin SEO dashboard with indexing status and ping controls"
```

---

### Task 12: Docker Config + Final Build

**Files:**
- Modify: `docker-compose.yml` (add volume for Google credentials if needed)

**Step 1: Add credentials volume mount** (optional, only when Google API is configured)

Under the `web` service volumes:
```yaml
    volumes:
      - ./credentials:/app/credentials:ro
```

**Step 2: Generate IndexNow API key**

```bash
python3 -c "import secrets; print(secrets.token_hex(16))" 
```

Add the output to `.env` as `INDEXNOW_API_KEY=<value>`.

**Step 3: Rebuild and deploy**

```bash
docker-compose down && docker-compose up -d --build
docker-compose exec web alembic upgrade head
```

**Step 4: Verify**

```bash
curl -s http://localhost:8000/feed.xml | head -20
curl -s http://localhost:8000/sitemap.xml | grep -c '<url>'
curl -s http://localhost:8000/services | head -5
```

**Step 5: Final commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: complete SEO overhaul - indexing, RSS, dashboard"
```

---

## Verification Checklist

After deployment:
- [ ] `curl /sitemap.xml` includes /now, /resume, /services
- [ ] `curl /feed.xml` returns valid RSS 2.0
- [ ] `curl /services` returns 200
- [ ] All pages have unique OG/Twitter meta (inspect with browser dev tools)
- [ ] Blog posts have article:published_time meta tags
- [ ] Admin SEO dashboard loads at /admin/seo
- [ ] Creating a published post triggers IndexNow ping (check logs)
- [ ] IndexNow verification file accessible at /{api_key}.txt
- [ ] Structured data validates at https://search.google.com/test/rich-results
