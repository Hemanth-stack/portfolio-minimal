# Blog Enhancements & Hero Fix — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix hero visibility for non-admin users, add view counts + likes to blog posts, add prev/next navigation, and improve social sharing meta tags.

**Architecture:** Server-side counter approach for views and likes (simple integer columns on Post model). Cookie-based deduplication for likes. Two additional queries for prev/next navigation. Template block overrides for meta tags.

**Tech Stack:** FastAPI, SQLAlchemy (async), Alembic, Jinja2, vanilla JS

---

### Task 1: Fix Hero Section Visibility

**Files:**
- Modify: `app/templates/index.html:92-104`

**Step 1: Edit the hero section template**

Change lines 92-104 from:

```html
{# Editable Hero Content (admin only, hidden from visitors) #}
{% if sections.hero and is_admin %}
<div class="editable-section" 
     data-section-id="{{ sections.hero.section.id }}"
     data-page="home"
     data-section-key="hero">
    <button type="button" class="edit-section-btn" title="Edit section">
        {{ pencil_icon() }}
    </button>
    <div class="section-content">
        {{ sections.hero.html | safe }}
    </div>
</div>
{% endif %}
```

To:

```html
{# Editable Hero Content (visible to all visitors) #}
{% if sections.hero %}
<div class="editable-section" 
     data-section-id="{{ sections.hero.section.id }}"
     data-page="home"
     data-section-key="hero">
    {% if is_admin %}
    <button type="button" class="edit-section-btn" title="Edit section">
        {{ pencil_icon() }}
    </button>
    {% endif %}
    <div class="section-content">
        {{ sections.hero.html | safe }}
    </div>
</div>
{% endif %}
```

**Step 2: Verify visually**

Run the dev server, visit `/` while logged out. The hero introduction text should now be visible.

**Step 3: Commit**

```bash
git add app/templates/index.html
git commit -m "fix: show hero section content to all visitors, not just admins"
```

---

### Task 2: Add view_count and like_count to Post Model

**Files:**
- Modify: `app/models.py:35-51`
- Create: `alembic/versions/003_add_view_and_like_counts.py`

**Step 1: Add columns to Post model**

In `app/models.py`, add two columns to the `Post` class after the `updated_at` field (line 47):

```python
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
```

Note: `Integer` is already imported in `models.py`.

**Step 2: Create Alembic migration**

Create `alembic/versions/003_add_view_and_like_counts.py`:

```python
"""Add view_count and like_count to posts

Revision ID: 003_add_view_and_like_counts
Revises: 002_remove_subject
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_view_and_like_counts'
down_revision = '002_remove_subject'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('posts', sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('posts', 'like_count')
    op.drop_column('posts', 'view_count')
```

**Step 3: Run migration**

```bash
alembic upgrade head
```

Expected: migration applies successfully.

**Step 4: Commit**

```bash
git add app/models.py alembic/versions/003_add_view_and_like_counts.py
git commit -m "feat: add view_count and like_count columns to Post model"
```

---

### Task 3: Implement View Count Increment

**Files:**
- Modify: `app/routers/public.py:656-684` (blog_post route)

**Step 1: Add view count increment to blog_post route**

In `app/routers/public.py`, after fetching and validating the post (after line 669: `raise HTTPException...`), add:

```python
    # Increment view count
    post.view_count = (post.view_count or 0) + 1
    await db.commit()
```

Also pass `view_count` to the template context (it's already on the post object, but for clarity). The existing template context at line 676 already passes `post`, which includes `view_count`.

**Step 2: Pass view_count in blog list route**

In `app/routers/public.py`, in the blog list route (around line 460), after the `for post in posts:` loop that sets `read_time`, the `view_count` is already on each post object so no changes needed.

**Step 3: Commit**

```bash
git add app/routers/public.py
git commit -m "feat: increment view count on blog post page load"
```

---

### Task 4: Display View Count in Templates

**Files:**
- Modify: `app/templates/blog/post.html:29-31`
- Modify: `app/templates/blog/list.html` (post-meta line)

**Step 1: Update blog post detail template**

In `app/templates/blog/post.html`, change line 30 from:

```html
            {{ post.created_at.strftime('%B %d, %Y') }} · {{ read_time }} min read
```

To:

```html
            {{ post.created_at.strftime('%B %d, %Y') }} · {{ read_time }} min read · 👁 {{ post.view_count or 0 }} views
```

**Step 2: Update blog list template**

In `app/templates/blog/list.html`, find the post-meta div inside the post loop:

```html
                    <div class="post-meta">
                        {{ post.created_at.strftime('%b %d, %Y') }} · {{ post.read_time }} min read
                    </div>
```

Change to:

```html
                    <div class="post-meta">
                        {{ post.created_at.strftime('%b %d, %Y') }} · {{ post.read_time }} min read · 👁 {{ post.view_count or 0 }}
                    </div>
```

**Step 3: Commit**

```bash
git add app/templates/blog/post.html app/templates/blog/list.html
git commit -m "feat: display view count on blog list and post pages"
```

---

### Task 5: Implement Like Endpoint

**Files:**
- Modify: `app/routers/public.py` (add new route)

**Step 1: Add POST /blog/{slug}/like endpoint**

Add after the existing `blog_post` route (after line 684):

```python
@router.post("/blog/{slug}/like", response_class=JSONResponse)
async def like_post(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).where(Post.slug == slug, Post.published == True)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check cookie for already-liked
    liked_posts_cookie = request.cookies.get("liked_posts", "")
    liked_slugs = [s.strip() for s in liked_posts_cookie.split(",") if s.strip()]
    
    already_liked = slug in liked_slugs
    if not already_liked:
        post.like_count = (post.like_count or 0) + 1
        await db.commit()
        liked_slugs.append(slug)
    
    response = JSONResponse({
        "like_count": post.like_count,
        "liked": True
    })
    
    if not already_liked:
        response.set_cookie(
            "liked_posts",
            ",".join(liked_slugs),
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,
            samesite="lax"
        )
    
    return response
```

**Step 2: Commit**

```bash
git add app/routers/public.py
git commit -m "feat: add POST /blog/{slug}/like endpoint with cookie dedup"
```

---

### Task 6: Add Like Button to Blog Post Template

**Files:**
- Modify: `app/templates/blog/post.html:55-61` (near share buttons)

**Step 1: Add like button after share buttons**

In `app/templates/blog/post.html`, after the share-buttons div (after line 61), add:

```html
    {# Like button #}
    <div class="post-like">
        <button class="like-btn {% if post.slug in request.cookies.get('liked_posts', '').split(',') %}liked{% endif %}" 
                data-slug="{{ post.slug }}" 
                aria-label="Like this post">
            <span class="like-icon">♡</span>
            <span class="like-count">{{ post.like_count or 0 }}</span>
        </button>
    </div>
```

**Step 2: Add JavaScript for like button**

In the same template, add a `{% block scripts %}` section at the bottom:

```html
{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.querySelector('.like-btn');
    if (!btn) return;
    
    // Set initial state from cookie
    const liked = document.cookie.split(';')
        .map(c => c.trim())
        .find(c => c.startsWith('liked_posts='));
    const likedSlugs = liked ? liked.split('=')[1].split(',') : [];
    if (likedSlugs.includes(btn.dataset.slug)) {
        btn.classList.add('liked');
        btn.querySelector('.like-icon').textContent = '♥';
    }
    
    btn.addEventListener('click', async () => {
        if (btn.classList.contains('liked')) return;
        
        const res = await fetch(`/blog/${btn.dataset.slug}/like`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            btn.classList.add('liked');
            btn.querySelector('.like-icon').textContent = '♥';
            btn.querySelector('.like-count').textContent = data.like_count;
        }
    });
});
</script>
{% endblock %}
```

**Step 3: Commit**

```bash
git add app/templates/blog/post.html
git commit -m "feat: add like button with JS to blog post template"
```

---

### Task 7: Add Prev/Next Post Navigation

**Files:**
- Modify: `app/routers/public.py:656-684` (blog_post route)
- Modify: `app/templates/blog/post.html` (before comments section)

**Step 1: Add prev/next queries to blog_post route**

In `app/routers/public.py`, inside the `blog_post` function, before the `render_template` return, add:

```python
    # Get previous and next posts
    prev_result = await db.execute(
        select(Post)
        .where(Post.published == True, Post.created_at < post.created_at)
        .order_by(Post.created_at.desc())
        .limit(1)
    )
    prev_post = prev_result.scalar_one_or_none()
    
    next_result = await db.execute(
        select(Post)
        .where(Post.published == True, Post.created_at > post.created_at)
        .order_by(Post.created_at.asc())
        .limit(1)
    )
    next_post = next_result.scalar_one_or_none()
```

Add `prev_post` and `next_post` to the template context dict.

**Step 2: Add navigation template**

In `app/templates/blog/post.html`, before `<section class="comments"`, add:

```html
    {# Prev/Next Navigation #}
    {% if prev_post or next_post %}
    <nav class="post-nav">
        <div class="post-nav-prev">
            {% if prev_post %}
            <span class="post-nav-label">← Previous</span>
            <a href="/blog/{{ prev_post.slug }}">{{ prev_post.title }}</a>
            {% endif %}
        </div>
        <div class="post-nav-next">
            {% if next_post %}
            <span class="post-nav-label">Next →</span>
            <a href="/blog/{{ next_post.slug }}">{{ next_post.title }}</a>
            {% endif %}
        </div>
    </nav>
    {% endif %}
```

**Step 3: Commit**

```bash
git add app/routers/public.py app/templates/blog/post.html
git commit -m "feat: add prev/next post navigation to blog posts"
```

---

### Task 8: Style Likes and Prev/Next Navigation

**Files:**
- Modify: `static/style.css` (append styles)

**Step 1: Add CSS for like button**

Append to `static/style.css`:

```css
/* Post Like Button */
.post-like {
    margin: 1.5rem 0;
}
.like-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: 1px solid var(--border);
    border-radius: 2rem;
    padding: 0.4rem 1rem;
    cursor: pointer;
    font-size: 1rem;
    color: var(--text-muted);
    transition: all 0.2s ease;
}
.like-btn:hover {
    border-color: #e74c3c;
    color: #e74c3c;
}
.like-btn.liked {
    border-color: #e74c3c;
    color: #e74c3c;
    cursor: default;
}
.like-btn.liked .like-icon {
    color: #e74c3c;
}
```

**Step 2: Add CSS for prev/next navigation**

Append to `static/style.css`:

```css
/* Post Navigation */
.post-nav {
    display: flex;
    justify-content: space-between;
    gap: 2rem;
    margin: 2rem 0;
    padding: 1.5rem 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
}
.post-nav-prev, .post-nav-next {
    flex: 1;
}
.post-nav-next {
    text-align: right;
}
.post-nav-label {
    display: block;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 0.25rem;
}
.post-nav a {
    font-weight: 500;
}
```

**Step 3: Commit**

```bash
git add static/style.css
git commit -m "style: add CSS for like button and prev/next navigation"
```

---

### Task 9: Social Sharing Meta Improvements

**Files:**
- Modify: `app/templates/base.html:14-27`
- Modify: `app/templates/blog/post.html:1-8`

**Step 1: Add og:image and twitter:image blocks to base.html**

In `app/templates/base.html`, after the `og:locale` meta tag (line 21) add:

```html
    <meta property="og:image" content="{% block og_image %}{{ settings.site_url }}/static/profile.jpg{% endblock %}">
```

Replace the existing twitter:card line (line 24) with:

```html
    <meta name="twitter:card" content="{% block twitter_card %}summary{% endblock %}">
```

After twitter:description (line 26) add:

```html
    <meta name="twitter:image" content="{% block twitter_image %}{{ settings.site_url }}/static/profile.jpg{% endblock %}">
```

**Step 2: Override in blog post template**

In `app/templates/blog/post.html`, the existing blocks for `og_type`, `og_title`, `og_description` are already set. No override needed for `og:image` unless posts have featured images (they don't currently).

**Step 3: Commit**

```bash
git add app/templates/base.html app/templates/blog/post.html
git commit -m "feat: add og:image and twitter:image meta tags for social sharing"
```

---

### Task 10: Final Verification

**Step 1: Run the dev server and verify all features**

```bash
make run  # or uvicorn app.main:app --reload
```

Checklist:
- [ ] Visit `/` logged out — hero intro visible
- [ ] Visit `/` logged in — hero intro visible + edit button
- [ ] Visit `/blog` — view counts shown
- [ ] Visit `/blog/{slug}` — view count increments, like button works
- [ ] Click like — heart fills, count increments, re-click blocked
- [ ] Prev/next navigation shows at bottom of post
- [ ] View page source — og:image and twitter:image tags present

**Step 2: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: final adjustments for blog enhancements"
```
