# Hemanth's Portfolio - iamhemanth.in

A minimal, content-focused personal website and blog built with FastAPI.

## Features

- 📝 **Blog** with Markdown, tags, and comments
- 💼 **Projects** showcase with tech stack and metrics
- 📄 **Static pages** (About, Now, Resume)
- ✉️ **Contact form** with Gmail SMTP
- 🔐 **Admin panel** for content management
- 🌙 **Dark/Light mode** (auto-switches based on system preference)
- 📱 **Responsive** minimal design
- 🔍 **SEO-friendly** with Open Graph meta tags

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (async)
- **Database:** PostgreSQL
- **Templates:** Jinja2
- **Styling:** Minimal CSS (~200 lines)

## Quick Start

### 1. Clone and setup

```bash
cd /opt/hemanth/portfolio
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Required settings:
- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`: Admin login credentials
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `SMTP_*`: Gmail SMTP settings (use App Password)

### 3. Setup PostgreSQL

```bash
# Create database
sudo -u postgres createdb portfolio

# Or with Docker
docker run -d --name postgres \
  -e POSTGRES_DB=portfolio \
  -e POSTGRES_USER=hemanth \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  postgres:15
```

### 4. Run migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "initial"

# Apply migrations
alembic upgrade head
```

### 5. Run the server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit:
- Website: http://localhost:8000
- Admin: http://localhost:8000/admin

## Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this password in `SMTP_PASSWORD`

## Production Deployment

### With systemd

Create `/etc/systemd/system/portfolio.service`:

```ini
[Unit]
Description=Portfolio Website
After=network.target

[Service]
Type=simple
User=hemanth
WorkingDirectory=/opt/hemanth/portfolio
Environment=PATH=/opt/hemanth/portfolio/venv/bin
ExecStart=/opt/hemanth/portfolio/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable portfolio
sudo systemctl start portfolio
```

### With Nginx

```nginx
server {
    listen 80;
    server_name iamhemanth.in www.iamhemanth.in;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/hemanth/portfolio/static;
        expires 30d;
    }
}
```

### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Project Structure

```
portfolio/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # DB models
│   ├── routers/
│   │   ├── public.py        # Public routes
│   │   └── admin.py         # Admin routes
│   ├── services/
│   │   ├── auth.py          # Authentication
│   │   ├── email.py         # SMTP
│   │   └── markdown.py      # Markdown processing
│   └── templates/           # Jinja2 templates
├── static/
│   ├── style.css            # Minimal CSS
│   └── resume.pdf           # Your resume
├── alembic/                  # DB migrations
├── requirements.txt
├── .env
└── README.md
```

## Admin Panel

Access at `/admin` with your configured credentials.

Features:
- **Dashboard:** Quick stats and recent messages
- **Posts:** Create/edit blog posts with Markdown preview
- **Projects:** Manage portfolio projects
- **Pages:** Edit About and Now pages
- **Comments:** Moderate blog comments
- **Messages:** View contact form submissions

## Customization

### Styling

Edit `static/style.css`. The design uses CSS variables for easy theming:

```css
:root {
    --bg: #fff;
    --fg: #111;
    --link: #0066cc;
    --max-width: 640px;
}
```

### Adding new pages

1. Add route in `app/routers/public.py`
2. Create template in `app/templates/`
3. Add nav link in `app/templates/base.html`

## License

MIT
# portfolio-minimal
