# Blog Enhancements & Hero Fix — Design Document

**Date**: 2026-03-06  
**Status**: Approved

## Overview

Five changes to the portfolio site:

1. Fix hero section visibility for non-admin visitors
2. Add blog post view counts
3. Add single-like button for posts
4. Add prev/next post navigation
5. Improve social sharing meta tags

## Feature 1: Hero Section Bug Fix

**Problem**: `index.html` line 93 gates hero content behind `is_admin`, hiding it from visitors.

**Fix**: Change `{% if sections.hero and is_admin %}` to `{% if sections.hero %}`. Keep edit button inside `{% if is_admin %}`.

**Files**: `app/templates/index.html`

## Feature 2: Blog Post View Count

**Model**: Add `view_count: int = 0` to `Post`.

**Backend**: Atomically increment `view_count` in `blog_post()` route on each page load.

**Display**: "👁 N views" shown in post meta on both list and detail pages.

**Files**: `app/models.py`, `app/routers/public.py`, `app/templates/blog/post.html`, `app/templates/blog/list.html`, new Alembic migration.

## Feature 3: Post Likes

**Model**: Add `like_count: int = 0` to `Post` (same migration as view count).

**Backend**: `POST /blog/{slug}/like` endpoint. Checks `liked_posts` cookie to prevent repeat likes. Atomically increments `like_count`. Returns JSON. Sets cookie with 1-year expiry.

**Frontend**: Heart button near share buttons. JS click handler toggles filled/outline heart, updates count. Cookie checked on load for initial state.

**Files**: `app/routers/public.py`, `app/templates/blog/post.html`, `static/style.css`

## Feature 4: Prev/Next Post Navigation

**Backend**: Two queries in `blog_post()`:
- Previous: `WHERE published AND created_at < current ORDER BY created_at DESC LIMIT 1`
- Next: `WHERE published AND created_at > current ORDER BY created_at ASC LIMIT 1`

**Frontend**: Flex row at bottom of post before comments. "← Previous Title" on left, "Next Title →" on right.

**Files**: `app/routers/public.py`, `app/templates/blog/post.html`, `static/style.css`

## Feature 5: Social Sharing Meta Improvements

**Existing**: OG type/title/description/url, Twitter card/title/description, canonical URL — all in `base.html`.

**Add**:
- `og:image` and `twitter:image` blocks in `base.html` (default: profile photo)
- Upgrade `twitter:card` to `summary_large_image` when image is present
- Blog post template overrides with post-specific values

**Files**: `app/templates/base.html`, `app/templates/blog/post.html`

## Migration

Single Alembic migration `003_add_view_count_and_like_count.py`:
- `ALTER TABLE posts ADD COLUMN view_count INTEGER DEFAULT 0`
- `ALTER TABLE posts ADD COLUMN like_count INTEGER DEFAULT 0`

## Summary of All Files Changed

| File | Changes |
|------|---------|
| `app/models.py` | Add `view_count`, `like_count` to Post |
| `app/routers/public.py` | Increment views, like endpoint, prev/next queries |
| `app/templates/index.html` | Remove `is_admin` guard from hero section |
| `app/templates/base.html` | Add `og:image`, `twitter:image` blocks |
| `app/templates/blog/post.html` | View count, likes, prev/next nav, meta overrides |
| `app/templates/blog/list.html` | View count display |
| `static/style.css` | Styles for likes, prev/next nav |
| `alembic/versions/003_*.py` | New migration |
