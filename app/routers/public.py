from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
import hashlib
import time
import os

from app.database import get_db
from app.models import Post, Project, Tag, Category, Comment, ContactMessage, Section
from app.config import get_settings
from app.services.markdown import render_markdown, estimate_read_time, generate_excerpt
from app.services.email import send_contact_notification, send_contact_confirmation
from app.services.sections import (
    get_page_sections, init_page_sections, get_or_create_section,
    update_section, render_section, create_section, delete_section, DEFAULT_SECTIONS
)
from app.services.auth import verify_session_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Simple CAPTCHA storage (in production, use Redis or similar)
CAPTCHA_STORE = {}


def is_admin_logged_in(request: Request) -> bool:
    """Check if admin is logged in via session cookie."""
    token = request.cookies.get("session")
    if not token:
        return False
    return verify_session_token(token) is not None


async def common_context(request: Request, db: AsyncSession):
    """Common context for all templates."""
    settings = get_settings()
    admin = is_admin_logged_in(request)
    
    return {
        "request": request,
        "settings": settings,
        "site": {
            "site_name": settings.site_name,
            "site_tagline": settings.site_tagline,
            "site_email": "ihemanth.2001@gmail.com",
            "linkedin_url": "https://www.linkedin.com/in/hemanth-irivichetty/",
            "github_url": "https://github.com/Hemanth-stack",
        },
        "now": datetime.utcnow(),
        "is_admin": admin,
    }


async def get_sections_for_page(db: AsyncSession, page: str) -> dict:
    """Get all sections for a page, creating defaults if needed."""
    sections = await get_page_sections(db, page)
    
    # If no sections exist, initialize defaults
    if not sections and page in DEFAULT_SECTIONS:
        sections = await init_page_sections(db, page)
    
    # Ensure all default sections exist
    for key in DEFAULT_SECTIONS.get(page, {}).keys():
        if key not in sections:
            sections[key] = await get_or_create_section(db, page, key)
    
    return sections


def generate_captcha():
    """Generate a simple math CAPTCHA."""
    import random
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    answer = a + b
    token = hashlib.sha256(f"{a}+{b}={answer}:{time.time()}".encode()).hexdigest()[:16]
    CAPTCHA_STORE[token] = {"answer": str(answer), "expires": time.time() + 300}  # 5 min expiry
    return {"question": f"What is {a} + {b}?", "token": token}


def verify_captcha(token: str, answer: str) -> bool:
    """Verify CAPTCHA answer."""
    if token not in CAPTCHA_STORE:
        return False
    data = CAPTCHA_STORE.pop(token)
    if time.time() > data["expires"]:
        return False
    return data["answer"] == answer.strip()


# ============ API Endpoints for Inline Editing ============

@router.get("/api/section/{page}/{section_key}")
async def api_get_section(
    request: Request,
    page: str,
    section_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get section content (for editing)."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    section = await get_or_create_section(db, page, section_key)
    return JSONResponse({
        "id": section.id,
        "page": section.page,
        "section_key": section.section_key,
        "title": section.title,
        "content": section.content,
        "visible": section.visible,
        "order": section.order,
    })


@router.put("/api/section/{page}/{section_key}")
async def api_update_section(
    request: Request,
    page: str,
    section_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Update section content."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    content = data.get("content", "")
    title = data.get("title")
    
    section = await update_section(db, page, section_key, content, title)
    
    return JSONResponse({
        "success": True,
        "html": render_section(section),
        "section_key": section_key,
    })


@router.post("/api/section")
async def api_create_section(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new section."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    page = data.get("page")
    section_key = data.get("section_key")
    title = data.get("title", "")
    content = data.get("content", "")
    order = data.get("order", 99)
    
    if not page or not section_key:
        return JSONResponse({"error": "page and section_key are required"}, status_code=400)
    
    # Check if section already exists
    existing = await get_page_sections(db, page)
    if section_key in existing:
        return JSONResponse({"error": "Section already exists"}, status_code=400)
    
    section = await create_section(db, page, section_key, title, content, order)
    
    return JSONResponse({
        "success": True,
        "section": {
            "id": section.id,
            "page": section.page,
            "section_key": section.section_key,
            "title": section.title,
            "html": render_section(section),
        }
    })


@router.delete("/api/section/{section_id}")
async def api_delete_section(
    request: Request,
    section_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a section."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    success = await delete_section(db, section_id)
    if success:
        return JSONResponse({"success": True})
    return JSONResponse({"error": "Section not found"}, status_code=404)


@router.get("/api/sections/{page}")
async def api_list_sections(
    request: Request,
    page: str,
    db: AsyncSession = Depends(get_db)
):
    """List all sections for a page."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    sections = await get_page_sections(db, page)
    return JSONResponse({
        "sections": [
            {
                "id": s.id,
                "section_key": s.section_key,
                "title": s.title,
                "order": s.order,
                "visible": s.visible,
            }
            for s in sections.values()
        ]
    })


@router.post("/api/markdown")
async def api_render_markdown(request: Request):
    """Render markdown to HTML (for preview)."""
    if not is_admin_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    content = data.get("content", "")
    
    return JSONResponse({
        "html": render_markdown(content)
    })


@router.get("/api/captcha")
async def api_get_captcha():
    """Get a new CAPTCHA challenge."""
    captcha = generate_captcha()
    return JSONResponse(captcha)


# ============ Public Routes ============

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "home")
    
    # Get recent published posts
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .order_by(Post.created_at.desc())
        .limit(3)
    )
    recent_posts = result.scalars().all()
    
    # Get featured projects
    result = await db.execute(
        select(Project)
        .where(Project.featured == True)
        .order_by(Project.order)
        .limit(2)
    )
    featured_projects = result.scalars().all()
    
    # Render section content
    rendered_sections = {
        key: {
            "section": section,
            "html": render_section(section)
        }
        for key, section in sections.items()
    }
    
    return templates.TemplateResponse("index.html", {
        **ctx,
        "sections": rendered_sections,
        "recent_posts": recent_posts,
        "featured_projects": featured_projects,
    })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "about")
    
    rendered_sections = {
        key: {
            "section": section,
            "html": render_section(section)
        }
        for key, section in sections.items()
    }
    
    return templates.TemplateResponse("about.html", {
        **ctx,
        "sections": rendered_sections,
    })


@router.get("/now", response_class=HTMLResponse)
async def now(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "now")
    
    rendered_sections = {
        key: {
            "section": section,
            "html": render_section(section)
        }
        for key, section in sections.items()
    }
    
    return templates.TemplateResponse("now.html", {
        **ctx,
        "sections": rendered_sections,
    })


@router.get("/resume", response_class=HTMLResponse)
async def resume(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "resume")
    
    # Sort sections by order
    sorted_sections = sorted(sections.values(), key=lambda s: s.order)
    
    rendered_sections = {
        s.section_key: {
            "section": s,
            "html": render_section(s)
        }
        for s in sorted_sections
    }
    
    # Also provide as list for ordered display
    sections_list = [
        {
            "section": s,
            "html": render_section(s)
        }
        for s in sorted_sections
    ]
    
    return templates.TemplateResponse("resume.html", {
        **ctx,
        "sections": rendered_sections,
        "sections_list": sections_list,
    })


@router.get("/resume/download")
async def download_resume():
    """Download resume as PDF."""
    pdf_path = "static/resume.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, filename="Hemanth_Irivichetty_Resume.pdf")
    raise HTTPException(status_code=404, detail="Resume PDF not found")


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "contact")
    
    rendered_sections = {
        key: {
            "section": section,
            "html": render_section(section)
        }
        for key, section in sections.items()
    }
    
    # Generate CAPTCHA
    captcha = generate_captcha()
    
    return templates.TemplateResponse("contact.html", {
        **ctx,
        "sections": rendered_sections,
        "captcha": captcha,
        "flash_message": None,
        "flash_type": None,
    })


@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    captcha_token: str = Form(...),
    captcha_answer: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    ctx = await common_context(request, db)
    sections = await get_sections_for_page(db, "contact")
    
    rendered_sections = {
        key: {
            "section": section,
            "html": render_section(section)
        }
        for key, section in sections.items()
    }
    
    # Verify CAPTCHA
    if not verify_captcha(captcha_token, captcha_answer):
        captcha = generate_captcha()
        return templates.TemplateResponse("contact.html", {
            **ctx,
            "sections": rendered_sections,
            "captcha": captcha,
            "flash_message": "CAPTCHA verification failed. Please try again.",
            "flash_type": "error",
        })
    
    # Save to database
    msg = ContactMessage(
        name=name,
        email=email,
        message=message,
    )
    db.add(msg)
    await db.commit()
    
    # Send email notifications
    await send_contact_notification(name, email, "Contact Form Submission", message)
    await send_contact_confirmation(email, name)
    
    captcha = generate_captcha()
    return templates.TemplateResponse("contact.html", {
        **ctx,
        "sections": rendered_sections,
        "captcha": captcha,
        "flash_message": "Thanks for your message! I'll get back to you soon.",
        "flash_type": "success",
    })


# ============ Blog Routes ============

@router.get("/blog", response_class=HTMLResponse)
async def blog_list(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .options(selectinload(Post.tags), selectinload(Post.categories))
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    for post in posts:
        post.read_time = estimate_read_time(post.content)
        if not post.excerpt:
            post.excerpt = generate_excerpt(post.content)
    
    result = await db.execute(select(Tag).order_by(Tag.name))
    all_tags = result.scalars().all()
    
    result = await db.execute(select(Category).order_by(Category.name))
    all_categories = result.scalars().all()
    
    # Get archives (year-month counts)
    archives = await get_blog_archives(db)
    
    return templates.TemplateResponse("blog/list.html", {
        **ctx,
        "posts": posts,
        "all_tags": all_tags,
        "all_categories": all_categories,
        "archives": archives,
        "tag": None,
        "category": None,
        "archive_year": None,
        "archive_month": None,
    })


async def get_blog_archives(db: AsyncSession):
    """Get blog post counts by year/month."""
    result = await db.execute(
        select(
            extract('year', Post.created_at).label('year'),
            extract('month', Post.created_at).label('month'),
            func.count(Post.id).label('count')
        )
        .where(Post.published == True)
        .group_by(extract('year', Post.created_at), extract('month', Post.created_at))
        .order_by(extract('year', Post.created_at).desc(), extract('month', Post.created_at).desc())
    )
    archives = []
    months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for row in result:
        archives.append({
            'year': int(row.year),
            'month': int(row.month),
            'month_name': months[int(row.month)],
            'count': row.count,
        })
    return archives


@router.get("/blog/archive/{year}", response_class=HTMLResponse)
async def blog_by_year(request: Request, year: int, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .where(extract('year', Post.created_at) == year)
        .options(selectinload(Post.tags), selectinload(Post.categories))
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    for post in posts:
        post.read_time = estimate_read_time(post.content)
        if not post.excerpt:
            post.excerpt = generate_excerpt(post.content)
    
    archives = await get_blog_archives(db)
    
    return templates.TemplateResponse("blog/list.html", {
        **ctx,
        "posts": posts,
        "all_tags": [],
        "all_categories": [],
        "archives": archives,
        "tag": None,
        "category": None,
        "archive_year": year,
        "archive_month": None,
    })


@router.get("/blog/archive/{year}/{month}", response_class=HTMLResponse)
async def blog_by_month(request: Request, year: int, month: int, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .where(extract('year', Post.created_at) == year)
        .where(extract('month', Post.created_at) == month)
        .options(selectinload(Post.tags), selectinload(Post.categories))
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    for post in posts:
        post.read_time = estimate_read_time(post.content)
        if not post.excerpt:
            post.excerpt = generate_excerpt(post.content)
    
    archives = await get_blog_archives(db)
    months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    return templates.TemplateResponse("blog/list.html", {
        **ctx,
        "posts": posts,
        "all_tags": [],
        "all_categories": [],
        "archives": archives,
        "tag": None,
        "category": None,
        "archive_year": year,
        "archive_month": {"num": month, "name": months[month]},
    })


@router.get("/blog/category/{slug}", response_class=HTMLResponse)
async def blog_by_category(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    
    if not category:
        return RedirectResponse("/blog")
    
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .where(Post.categories.contains(category))
        .options(selectinload(Post.tags), selectinload(Post.categories))
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    for post in posts:
        post.read_time = estimate_read_time(post.content)
        if not post.excerpt:
            post.excerpt = generate_excerpt(post.content)
    
    archives = await get_blog_archives(db)
    
    return templates.TemplateResponse("blog/list.html", {
        **ctx,
        "posts": posts,
        "all_tags": [],
        "all_categories": [],
        "archives": archives,
        "tag": None,
        "category": category,
        "archive_year": None,
        "archive_month": None,
    })


@router.get("/blog/tag/{slug}", response_class=HTMLResponse)
async def blog_by_tag(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalar_one_or_none()
    
    if not tag:
        return RedirectResponse("/blog")
    
    result = await db.execute(
        select(Post)
        .where(Post.published == True)
        .where(Post.tags.contains(tag))
        .options(selectinload(Post.tags), selectinload(Post.categories))
        .order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    
    for post in posts:
        post.read_time = estimate_read_time(post.content)
        if not post.excerpt:
            post.excerpt = generate_excerpt(post.content)
    
    archives = await get_blog_archives(db)
    
    return templates.TemplateResponse("blog/list.html", {
        **ctx,
        "posts": posts,
        "all_tags": [],
        "all_categories": [],
        "archives": archives,
        "tag": tag,
        "category": None,
        "archive_year": None,
        "archive_month": None,
    })


@router.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(
        select(Post)
        .where(Post.slug == slug)
        .options(selectinload(Post.tags), selectinload(Post.categories), selectinload(Post.comments))
    )
    post = result.scalar_one_or_none()
    
    if not post or not post.published:
        return RedirectResponse("/blog")
    
    comments = [c for c in post.comments if c.approved]
    
    return templates.TemplateResponse("blog/post.html", {
        **ctx,
        "post": post,
        "content": render_markdown(post.content),
        "read_time": estimate_read_time(post.content),
        "comments": comments,
    })


@router.post("/blog/{slug}/comment")
async def add_comment(
    request: Request,
    slug: str,
    author_name: str = Form(...),
    author_email: str = Form(...),
    content: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    
    if not post:
        return RedirectResponse("/blog", status_code=303)
    
    comment = Comment(
        post_id=post.id,
        author_name=author_name,
        author_email=author_email,
        content=content,
        approved=False,
    )
    db.add(comment)
    await db.commit()
    
    return RedirectResponse(f"/blog/{slug}#comments", status_code=303)


# ============ Projects Routes ============

@router.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(
        select(Project).order_by(Project.order, Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    return templates.TemplateResponse("projects/list.html", {
        **ctx,
        "projects": projects,
    })


@router.get("/projects/{slug}", response_class=HTMLResponse)
async def project_detail(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    ctx = await common_context(request, db)
    
    result = await db.execute(select(Project).where(Project.slug == slug))
    project = result.scalar_one_or_none()
    
    if not project:
        return RedirectResponse("/projects")
    
    return templates.TemplateResponse("projects/detail.html", {
        **ctx,
        "project": project,
        "content": render_markdown(project.description),
    })
