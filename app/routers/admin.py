from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from slugify import slugify

from app.database import get_db
from app.models import Post, Project, Page, Tag, Category, Comment, ContactMessage, SiteSettings, ResumeSection
from app.config import get_settings
from app.services.auth import verify_session_token, create_session_token
from app.services.markdown import generate_excerpt
from app.services.content import get_all_settings, DEFAULT_SETTINGS

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def get_session_token(request: Request) -> str | None:
    return request.cookies.get("session")


async def require_auth(request: Request):
    """Check if user is authenticated."""
    token = get_session_token(request)
    if not token:
        return None
    return verify_session_token(token)


async def admin_context(request: Request, db: AsyncSession, flash_message: str = None, flash_type: str = None):
    site_settings = await get_all_settings(db)
    return {
        "request": request,
        "settings": get_settings(),
        "site": site_settings,
        "flash_message": flash_message,
        "flash_type": flash_type,
    }


# ============ Auth ============

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if await require_auth(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    settings = get_settings()
    
    if username == settings.admin_username and password == settings.admin_password:
        token = create_session_token(username)
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie("session", token, httponly=True, max_age=86400*7)
        return response
    
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": "Invalid username or password"
    })


@router.get("/logout")
async def logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("session")
    return response


# ============ Dashboard ============

@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    
    # Get stats
    posts_count = await db.scalar(select(func.count(Post.id)))
    projects_count = await db.scalar(select(func.count(Project.id)))
    pending_comments = await db.scalar(
        select(func.count(Comment.id)).where(Comment.approved == False)
    )
    unread_messages = await db.scalar(
        select(func.count(ContactMessage.id)).where(ContactMessage.read == False)
    )
    
    # Recent messages
    result = await db.execute(
        select(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(5)
    )
    recent_messages = result.scalars().all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        **ctx,
        "stats": {
            "posts": posts_count,
            "projects": projects_count,
            "comments_pending": pending_comments,
            "messages_unread": unread_messages,
        },
        "recent_messages": recent_messages,
    })


# ============ Site Settings ============

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    site_settings = await get_all_settings(db)
    
    # Group settings for display
    setting_groups = {
        "Profile": ["site_name", "site_tagline", "site_email", "site_phone", "linkedin_url", "github_url"],
        "Home Page": ["home_greeting", "home_intro", "home_current", "home_what_i_do", "home_cta"],
        "Other": ["footer_text"],
    }
    
    return templates.TemplateResponse("admin/settings.html", {
        **ctx,
        "site_settings": site_settings,
        "setting_groups": setting_groups,
    })


@router.post("/settings")
async def update_settings(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    form = await request.form()
    
    for key in DEFAULT_SETTINGS.keys():
        if key in form:
            value = form[key]
            result = await db.execute(select(SiteSettings).where(SiteSettings.key == key))
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.value = value
            else:
                db.add(SiteSettings(key=key, value=value))
    
    await db.commit()
    return RedirectResponse("/admin/settings", status_code=303)


# ============ Posts ============

@router.get("/posts", response_class=HTMLResponse)
async def posts_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()
    
    return templates.TemplateResponse("admin/posts/list.html", {
        **ctx,
        "posts": posts,
    })


@router.get("/posts/new", response_class=HTMLResponse)
async def new_post_form(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    return templates.TemplateResponse("admin/posts/form.html", {
        **ctx,
        "post": None,
    })


@router.post("/posts/new")
async def create_post(
    request: Request,
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(...),
    excerpt: str = Form(""),
    tags: str = Form(""),
    categories: str = Form(""),
    published: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    if not slug:
        slug = slugify(title)
    
    if not excerpt:
        excerpt = generate_excerpt(content)
    
    post = Post(
        title=title,
        slug=slug,
        content=content,
        excerpt=excerpt,
        published=published,
    )
    
    # Handle tags
    if tags:
        tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        for name in tag_names:
            result = await db.execute(select(Tag).where(Tag.name == name))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=name, slug=slugify(name))
                db.add(tag)
            post.tags.append(tag)
    
    # Handle categories
    if categories:
        cat_names = [c.strip() for c in categories.split(",") if c.strip()]
        for name in cat_names:
            result = await db.execute(select(Category).where(Category.name == name))
            category = result.scalar_one_or_none()
            if not category:
                category = Category(name=name, slug=slugify(name))
                db.add(category)
            post.categories.append(category)
    
    db.add(post)
    await db.commit()
    
    return RedirectResponse("/admin/posts", status_code=303)


@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(
        select(Post).where(Post.id == post_id).options(selectinload(Post.tags), selectinload(Post.categories))
    )
    post = result.scalar_one_or_none()
    
    if not post:
        return RedirectResponse("/admin/posts", status_code=303)
    
    return templates.TemplateResponse("admin/posts/form.html", {
        **ctx,
        "post": post,
    })


@router.post("/posts/{post_id}/edit")
async def update_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(...),
    excerpt: str = Form(""),
    tags: str = Form(""),
    categories: str = Form(""),
    published: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(
        select(Post).where(Post.id == post_id).options(selectinload(Post.tags), selectinload(Post.categories))
    )
    post = result.scalar_one_or_none()
    
    if not post:
        return RedirectResponse("/admin/posts", status_code=303)
    
    post.title = title
    post.slug = slug or slugify(title)
    post.content = content
    post.excerpt = excerpt or generate_excerpt(content)
    post.published = published
    post.updated_at = datetime.utcnow()
    
    # Update tags
    post.tags.clear()
    if tags:
        tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        for name in tag_names:
            result = await db.execute(select(Tag).where(Tag.name == name))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=name, slug=slugify(name))
                db.add(tag)
            post.tags.append(tag)
    
    # Update categories
    post.categories.clear()
    if categories:
        cat_names = [c.strip() for c in categories.split(",") if c.strip()]
        for name in cat_names:
            result = await db.execute(select(Category).where(Category.name == name))
            category = result.scalar_one_or_none()
            if not category:
                category = Category(name=name, slug=slugify(name))
                db.add(category)
            post.categories.append(category)
    
    await db.commit()
    return RedirectResponse("/admin/posts", status_code=303)


@router.post("/posts/{post_id}/delete")
async def delete_post(request: Request, post_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if post:
        await db.delete(post)
        await db.commit()
    
    return RedirectResponse("/admin/posts", status_code=303)


# ============ Projects ============

@router.get("/projects", response_class=HTMLResponse)
async def admin_projects_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Project).order_by(Project.order))
    projects = result.scalars().all()
    
    return templates.TemplateResponse("admin/projects/list.html", {
        **ctx,
        "projects": projects,
    })


@router.get("/projects/new", response_class=HTMLResponse)
async def new_project_form(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    return templates.TemplateResponse("admin/projects/form.html", {
        **ctx,
        "project": None,
    })


@router.post("/projects/new")
async def create_project(
    request: Request,
    title: str = Form(...),
    slug: str = Form(""),
    short_description: str = Form(...),
    description: str = Form(...),
    tech_stack: str = Form(""),
    metrics: str = Form(""),
    github_url: str = Form(""),
    live_url: str = Form(""),
    order: int = Form(0),
    featured: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    project = Project(
        title=title,
        slug=slug or slugify(title),
        short_description=short_description,
        description=description,
        tech_stack=tech_stack,
        metrics=metrics,
        github_url=github_url or None,
        live_url=live_url or None,
        order=order,
        featured=featured,
    )
    
    db.add(project)
    await db.commit()
    
    return RedirectResponse("/admin/projects", status_code=303)


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_form(request: Request, project_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        return RedirectResponse("/admin/projects", status_code=303)
    
    return templates.TemplateResponse("admin/projects/form.html", {
        **ctx,
        "project": project,
    })


@router.post("/projects/{project_id}/edit")
async def update_project(
    request: Request,
    project_id: int,
    title: str = Form(...),
    slug: str = Form(""),
    short_description: str = Form(...),
    description: str = Form(...),
    tech_stack: str = Form(""),
    metrics: str = Form(""),
    github_url: str = Form(""),
    live_url: str = Form(""),
    order: int = Form(0),
    featured: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        return RedirectResponse("/admin/projects", status_code=303)
    
    project.title = title
    project.slug = slug or slugify(title)
    project.short_description = short_description
    project.description = description
    project.tech_stack = tech_stack
    project.metrics = metrics
    project.github_url = github_url or None
    project.live_url = live_url or None
    project.order = order
    project.featured = featured
    
    await db.commit()
    return RedirectResponse("/admin/projects", status_code=303)


@router.post("/projects/{project_id}/delete")
async def delete_project(request: Request, project_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if project:
        await db.delete(project)
        await db.commit()
    
    return RedirectResponse("/admin/projects", status_code=303)


# ============ Pages ============

@router.get("/pages", response_class=HTMLResponse)
async def pages_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Page))
    pages = result.scalars().all()
    
    # Add default pages if not in DB
    existing_slugs = {p.slug for p in pages}
    default_pages = [
        {"slug": "about", "title": "About"},
        {"slug": "now", "title": "Now"},
    ]
    
    for dp in default_pages:
        if dp["slug"] not in existing_slugs:
            pages.append(type('Page', (), {'slug': dp["slug"], 'title': dp["title"], 'updated_at': None})())
    
    return templates.TemplateResponse("admin/pages/list.html", {
        **ctx,
        "pages": pages,
    })


@router.get("/pages/{slug}/edit", response_class=HTMLResponse)
async def edit_page_form(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Page).where(Page.slug == slug))
    page = result.scalar_one_or_none()
    
    # Create default page if it doesn't exist
    if not page:
        from app.services.content import DEFAULT_PAGES
        defaults = DEFAULT_PAGES.get(slug, {"title": slug.title(), "content": "", "meta_description": ""})
        page = Page(slug=slug, title=defaults["title"], content=defaults.get("content", ""), meta_description=defaults.get("meta_description", ""))
        db.add(page)
        await db.commit()
        await db.refresh(page)
    
    return templates.TemplateResponse("admin/pages/form.html", {
        **ctx,
        "page": page,
    })


@router.post("/pages/{slug}/edit")
async def update_page(
    request: Request,
    slug: str,
    title: str = Form(...),
    content: str = Form(...),
    meta_description: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Page).where(Page.slug == slug))
    page = result.scalar_one_or_none()
    
    if not page:
        page = Page(slug=slug, title=title, content=content, meta_description=meta_description)
        db.add(page)
    else:
        page.title = title
        page.content = content
        page.meta_description = meta_description
        page.updated_at = datetime.utcnow()
    
    await db.commit()
    return RedirectResponse("/admin/pages", status_code=303)


# ============ Resume Sections ============

@router.get("/resume", response_class=HTMLResponse)
async def resume_sections_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(ResumeSection).order_by(ResumeSection.order))
    sections = result.scalars().all()
    
    # Initialize defaults if empty
    if not sections:
        from app.services.content import DEFAULT_RESUME_SECTIONS
        for section_data in DEFAULT_RESUME_SECTIONS:
            db.add(ResumeSection(**section_data))
        await db.commit()
        
        result = await db.execute(select(ResumeSection).order_by(ResumeSection.order))
        sections = result.scalars().all()
    
    return templates.TemplateResponse("admin/resume/list.html", {
        **ctx,
        "sections": sections,
    })


@router.get("/resume/new", response_class=HTMLResponse)
async def new_resume_section_form(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    return templates.TemplateResponse("admin/resume/form.html", {
        **ctx,
        "section": None,
    })


@router.post("/resume/new")
async def create_resume_section(
    request: Request,
    section_type: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    order: int = Form(0),
    visible: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    section = ResumeSection(
        section_type=section_type,
        title=title,
        content=content,
        order=order,
        visible=visible,
    )
    db.add(section)
    await db.commit()
    
    return RedirectResponse("/admin/resume", status_code=303)


@router.get("/resume/{section_id}/edit", response_class=HTMLResponse)
async def edit_resume_section_form(request: Request, section_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(ResumeSection).where(ResumeSection.id == section_id))
    section = result.scalar_one_or_none()
    
    if not section:
        return RedirectResponse("/admin/resume", status_code=303)
    
    return templates.TemplateResponse("admin/resume/form.html", {
        **ctx,
        "section": section,
    })


@router.post("/resume/{section_id}/edit")
async def update_resume_section(
    request: Request,
    section_id: int,
    section_type: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    order: int = Form(0),
    visible: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(ResumeSection).where(ResumeSection.id == section_id))
    section = result.scalar_one_or_none()
    
    if not section:
        return RedirectResponse("/admin/resume", status_code=303)
    
    section.section_type = section_type
    section.title = title
    section.content = content
    section.order = order
    section.visible = visible
    
    await db.commit()
    return RedirectResponse("/admin/resume", status_code=303)


@router.post("/resume/{section_id}/delete")
async def delete_resume_section(request: Request, section_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(ResumeSection).where(ResumeSection.id == section_id))
    section = result.scalar_one_or_none()
    
    if section:
        await db.delete(section)
        await db.commit()
    
    return RedirectResponse("/admin/resume", status_code=303)


# ============ Comments ============

@router.get("/comments", response_class=HTMLResponse)
async def comments_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.post))
        .order_by(Comment.approved, Comment.created_at.desc())
    )
    comments = result.scalars().all()
    
    return templates.TemplateResponse("admin/comments/list.html", {
        **ctx,
        "comments": comments,
    })


@router.post("/comments/{comment_id}/approve")
async def approve_comment(request: Request, comment_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if comment:
        comment.approved = True
        await db.commit()
    
    return RedirectResponse("/admin/comments", status_code=303)


@router.post("/comments/{comment_id}/delete")
async def delete_comment(request: Request, comment_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if comment:
        await db.delete(comment)
        await db.commit()
    
    return RedirectResponse("/admin/comments", status_code=303)


# ============ Messages ============

@router.get("/messages", response_class=HTMLResponse)
async def messages_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(
        select(ContactMessage).order_by(ContactMessage.created_at.desc())
    )
    messages = result.scalars().all()
    
    return templates.TemplateResponse("admin/messages/list.html", {
        **ctx,
        "messages": messages,
    })


@router.get("/messages/{message_id}", response_class=HTMLResponse)
async def message_detail(request: Request, message_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(ContactMessage).where(ContactMessage.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        return RedirectResponse("/admin/messages", status_code=303)
    
    # Mark as read
    if not message.read:
        message.read = True
        await db.commit()
    
    return templates.TemplateResponse("admin/messages/detail.html", {
        **ctx,
        "message": message,
    })


@router.post("/messages/{message_id}/delete")
async def delete_message(request: Request, message_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(ContactMessage).where(ContactMessage.id == message_id))
    message = result.scalar_one_or_none()
    
    if message:
        await db.delete(message)
        await db.commit()
    
    return RedirectResponse("/admin/messages", status_code=303)


# ============ Categories ============

@router.get("/categories", response_class=HTMLResponse)
async def categories_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    
    return templates.TemplateResponse("admin/categories/list.html", {
        **ctx,
        "categories": categories,
    })


@router.post("/categories/new")
async def create_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    category = Category(
        name=name,
        slug=slugify(name),
        description=description,
    )
    db.add(category)
    await db.commit()
    
    return RedirectResponse("/admin/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
async def delete_category(request: Request, category_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    
    if category:
        await db.delete(category)
        await db.commit()
    
    return RedirectResponse("/admin/categories", status_code=303)


# ============ Tags ============

@router.get("/tags", response_class=HTMLResponse)
async def tags_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    ctx = await admin_context(request, db)
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    
    return templates.TemplateResponse("admin/tags/list.html", {
        **ctx,
        "tags": tags,
    })


@router.post("/tags/new")
async def create_tag(
    request: Request,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    tag = Tag(name=name, slug=slugify(name))
    db.add(tag)
    await db.commit()
    
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/delete")
async def delete_tag(request: Request, tag_id: int, db: AsyncSession = Depends(get_db)):
    if not await require_auth(request):
        return RedirectResponse("/admin/login", status_code=303)
    
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    
    if tag:
        await db.delete(tag)
        await db.commit()
    
    return RedirectResponse("/admin/tags", status_code=303)
