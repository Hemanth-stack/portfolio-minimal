# SEO Overhaul — Comprehensive Indexing & Discoverability

**Date:** 2026-03-06
**Goal:** Every page and new blog post gets indexed by Google quickly, shows rich previews on social media, and is discoverable via feeds and search.

---

## Current State

Already in place: dynamic sitemap.xml, robots.txt, canonical URLs, basic OG/Twitter meta tags in base.html, JSON-LD structured data on blog posts, meta description/title on most pages, security headers, 404/500 error pages.

### Gaps Identified

| Area | Gap |
|---|---|
| Sitemap | Missing `/now`, `/resume`, `/services` pages |
| OG/Twitter tags | Only `blog/post.html` overrides `og_title`/`og_description`; all others fall back to generic site name |
| RSS feed | None — noted as TODO in existing SEO docs |
| Structured data | Only blog posts have specific schema; services, projects, about pages use generic Person |
| Auto-indexing | No mechanism to notify search engines when content is published |
| Blog post meta | Missing `article:published_time`, `article:tag` OG tags |
| Template inconsistency | Project templates use `settings.site_name` instead of `site.site_name` |

---

## Design

### 1. Template SEO Fixes

**Every template** gets explicit OG + Twitter block overrides reusing its existing title/description values. Affected files:

- `index.html` — add `description`, `og_title`, `og_description`, `twitter_title`, `twitter_description`
- `about.html`, `contact.html`, `now.html`, `resume.html`, `services.html` — add `og_title`, `og_description`, `twitter_title`, `twitter_description`
- `blog/list.html` — same as above
- `projects/list.html`, `projects/detail.html` — same + fix `settings.site_name` → `site.site_name`

**blog/post.html enhancements:**
- Add `article:published_time`, `article:modified_time`, `article:author`, `article:tag` meta tags via a new `{% block article_meta %}` or inline in `{% block head %}`
- Set `twitter_card` to `summary_large_image`

**Structured data enrichment:**
- `services.html` → `ProfessionalService` schema
- `blog/list.html` → `CollectionPage` schema
- `projects/detail.html` → `SoftwareSourceCode` schema
- `about.html` → Person with `jobTitle`, `knowsAbout`

**Sitemap additions:** Add `/now`, `/resume`, `/services` to the static pages list in `sitemap_xml()`.

**base.html:** Add `<link rel="alternate" type="application/rss+xml">` autodiscovery link.

### 2. RSS Feed

New route: `GET /feed.xml` (alias `/rss.xml`)

- Standard RSS 2.0 XML
- `<channel>` with site name, description, link, language
- Each published blog post as `<item>`: title, link, description (excerpt), pubDate (RFC 822), guid (permalink), category tags
- Content-Type: `application/rss+xml`
- Referenced from sitemap.xml and HTML head autodiscovery

### 3. IndexNow Integration

Automatic notification to Bing, Yandex, and Google when content changes.

**Config:** `INDEXNOW_API_KEY` env var (random 32-char hex string). Verification file served at `GET /{key}.txt`.

**Service:** `app/services/seo.py` → `notify_indexnow(urls: list[str])` — async POST to `https://api.indexnow.org/indexnow` with JSON body containing host, key, keyLocation, urlList.

**Hook:** Called after `create_post()` and `update_post()` in `admin.py` when `published=True`. Fire-and-forget via `asyncio.create_task()` — logs errors but never fails the admin request.

**Sitemap ping:** Also pings `https://www.google.com/ping?sitemap={site_url}/sitemap.xml` after publish.

### 4. Google Indexing API

Direct "please crawl now" requests to Google. 200 free requests/day.

**Config:** `GOOGLE_SERVICE_ACCOUNT_JSON` env var (path to service account credentials JSON file inside the container).

**Service:** `app/services/seo.py` → `notify_google_indexing(url: str, action: str = "URL_UPDATED")` — uses `google.auth` for JWT-based auth, POSTs to `https://indexing.googleapis.com/v3/urlNotifications:publish`.

**Hook:** Same as IndexNow — called after post create/update when published. Fire-and-forget.

**Setup requirements:**
1. Create Google Cloud project
2. Enable Web Search Indexing API
3. Create service account + download JSON key
4. Add service account email as owner in Google Search Console
5. Mount JSON key file in Docker container

### 5. Admin SEO Dashboard

New admin page at `/admin/seo`.

**Panels:**
- **Indexing Status** — table of all published posts + static pages with columns: URL, Last Pinged, IndexNow Status, Google API Status
- **Quick Actions** — "Ping All URLs" button, "Ping Selected" button, "Submit Sitemap" button
- **SEO Health Check** — automated checklist: sitemap valid, robots.txt valid, all pages have meta descriptions, RSS feed accessible
- **Recent Pings Log** — last 20 notifications with timestamp, URL, service, HTTP status

**Data model:** New `IndexingLog` table:
```
id: Integer PK
url: String(500)
service: String(20)  — 'indexnow' | 'google'
status_code: Integer
response: Text (nullable)
created_at: DateTime (server_default=now)
```

Alembic migration: `005_add_indexing_logs.py`

### 6. Dependencies

```
google-auth>=2.0.0       # Google Indexing API JWT auth
httpx>=0.27.0             # Async HTTP client for API calls
```

Added to `requirements.txt`.

---

## File Changes Summary

| File | Change |
|---|---|
| `app/config.py` | Add `indexnow_api_key`, `google_service_account_json` settings |
| `app/models.py` | Add `IndexingLog` model |
| `app/services/seo.py` | New — IndexNow, Google Indexing API, sitemap ping functions |
| `app/routers/public.py` | Add RSS feed route, IndexNow verification route, add pages to sitemap |
| `app/routers/admin.py` | Hook indexing calls after post create/update; add `/admin/seo` dashboard route |
| `app/templates/base.html` | Add RSS autodiscovery link |
| `app/templates/index.html` | Add description + OG/Twitter overrides |
| `app/templates/about.html` | Add OG/Twitter overrides + enriched Person schema |
| `app/templates/contact.html` | Add OG/Twitter overrides |
| `app/templates/now.html` | Add OG/Twitter overrides |
| `app/templates/resume.html` | Add OG/Twitter overrides |
| `app/templates/services.html` | Add OG/Twitter overrides + ProfessionalService schema |
| `app/templates/blog/list.html` | Add OG/Twitter overrides + CollectionPage schema |
| `app/templates/blog/post.html` | Add article meta tags, twitter_card override |
| `app/templates/projects/list.html` | Fix site_name inconsistency + add OG/Twitter overrides |
| `app/templates/projects/detail.html` | Fix site_name + add OG/Twitter overrides + SoftwareSourceCode schema |
| `app/templates/admin/seo.html` | New — SEO dashboard template |
| `alembic/versions/005_add_indexing_logs.py` | New migration |
| `requirements.txt` | Add google-auth, httpx |
| `docker-compose.yml` | Mount service account JSON (volume) |

---

## Non-Goals

- No automated SEO scoring algorithm or content analysis
- No programmatic Search Console performance data fetching (can be added later)
- No A/B testing of meta descriptions
- No automatic image optimization or lazy loading changes
