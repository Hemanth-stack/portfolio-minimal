from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routers import public, admin


templates = Jinja2Templates(directory="app/templates")


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for static files."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add cache headers for static files
        if request.url.path.startswith("/static/"):
            # Cache static files for 1 year (immutable assets)
            if request.url.path.endswith((".css", ".js", ".woff2", ".woff", ".ttf")):
                response.headers["Cache-Control"] = "public, max-age=86400"
            # Cache images for 1 month
            elif request.url.path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp")):
                response.headers["Cache-Control"] = "public, max-age=2592000"
            # Cache PDFs for 1 week
            elif request.url.path.endswith(".pdf"):
                response.headers["Cache-Control"] = "public, max-age=604800"
            else:
                response.headers["Cache-Control"] = "public, max-age=86400"
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Hemanth's Portfolio",
    description="Personal website and blog",
    lifespan=lifespan,
)

# Add cache control middleware
app.add_middleware(CacheControlMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(public.router)
app.include_router(admin.router)


# Add custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper error pages."""
    from datetime import datetime
    if exc.status_code == 404:
        from app.config import get_settings
        return templates.TemplateResponse(
            "errors/404.html",
            {
                "request": request,
                "settings": get_settings(),
                "site": {
                    "site_name": get_settings().site_name,
                    "site_tagline": get_settings().site_tagline,
                    "site_email": "ihemanth.2001@gmail.com",
                },
                "now": datetime.utcnow(),
            },
            status_code=404
        )
    elif exc.status_code >= 500:
        from app.config import get_settings
        return templates.TemplateResponse(
            "errors/500.html",
            {
                "request": request,
                "settings": get_settings(),
                "site": {
                    "site_name": get_settings().site_name,
                    "site_tagline": get_settings().site_tagline,
                    "site_email": "ihemanth.2001@gmail.com",
                },
                "now": datetime.utcnow(),
            },
            status_code=500
        )
    return Response(content=str(exc.detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return templates.TemplateResponse("422.html", {"request": request, "errors": exc.errors()}, status_code=422)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with 500 error page."""
    from app.config import get_settings
    from datetime import datetime
    import traceback
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    
    return templates.TemplateResponse(
        "errors/500.html",
        {
            "request": request,
            "settings": get_settings(),
            "site": {
                "site_name": get_settings().site_name,
                "site_tagline": get_settings().site_tagline,
                "site_email": "ihemanth.2001@gmail.com",
            },
            "now": datetime.utcnow(),
        },
        status_code=500
    )
