# Portfolio Makefile
# Usage: make prod

.PHONY: prod dev down logs shell migrate clean help

# Docker compose command (use docker-compose for older versions)
DC := docker-compose

# Production - single command to start everything
prod:
	@echo "🚀 Starting production server..."
	$(DC) up -d --build
	@echo "✅ Site is live at http://localhost:8000"
	@echo "📊 Admin panel at http://localhost:8000/admin"

# Development - with hot reload
dev:
	@echo "🔧 Starting development server..."
	$(DC) up --build

# Stop all containers
down:
	@echo "🛑 Stopping containers..."
	$(DC) down

# View logs
logs:
	$(DC) logs -f web

# Shell into web container
shell:
	$(DC) exec web bash

# Run database migrations
migrate:
	$(DC) exec web alembic upgrade head

# Generate new migration
migration:
	@read -p "Migration message: " msg; \
	$(DC) exec web alembic revision --autogenerate -m "$$msg"

# Clean up everything (containers, volumes, images)
clean:
	@echo "🧹 Cleaning up..."
	$(DC) down -v --rmi local
	@echo "✅ Cleaned up"

# Rebuild without cache
rebuild:
	$(DC) build --no-cache
	$(DC) up -d

# Database backup
backup:
	@mkdir -p backups
	$(DC) exec db pg_dump -U hemanth portfolio > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup saved to backups/"

# Restore from latest backup
restore:
	@latest=$$(ls -t backups/*.sql 2>/dev/null | head -1); \
	if [ -z "$$latest" ]; then echo "❌ No backup found"; exit 1; fi; \
	cat $$latest | $(DC) exec -T db psql -U hemanth portfolio; \
	echo "✅ Restored from $$latest"

# Show status
status:
	$(DC) ps

# Generate resume PDF
resume:
	python3 scripts/generate_resume.py

# Help
help:
	@echo "Portfolio Management Commands"
	@echo "=============================="
	@echo "make prod      - 🚀 Start production (single command)"
	@echo "make dev       - 🔧 Start with logs (development)"
	@echo "make down      - 🛑 Stop all containers"
	@echo "make logs      - 📋 View logs"
	@echo "make shell     - 🐚 Shell into container"
	@echo "make migrate   - 🗄️  Run database migrations"
	@echo "make migration - 📝 Create new migration"
	@echo "make backup    - 💾 Backup database"
	@echo "make restore   - ♻️  Restore latest backup"
	@echo "make clean     - 🧹 Remove everything"
	@echo "make status    - 📊 Show container status"
