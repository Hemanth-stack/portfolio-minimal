from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import init_db
from app.routers import public, admin


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for static files."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add cache headers for static files
        if request.url.path.startswith("/static/"):
            # Cache static files for 1 year (immutable assets)
            if request.url.path.endswith((".css", ".js", ".woff2", ".woff", ".ttf")):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            # Cache images for 1 month
            elif request.url.path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp")):
                response.headers["Cache-Control"] = "public, max-age=2592000"
            # Cache PDFs for 1 week
            elif request.url.path.endswith(".pdf"):
                response.headers["Cache-Control"] = "public, max-age=604800"
            else:
                response.headers["Cache-Control"] = "public, max-age=86400"
        
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
