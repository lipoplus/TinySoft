# Development Environment Quick Reference

## TL;DR - Get Started in 60 Seconds

```bash
# 1. Clone repo and cd into it
cd voiceresumeai

# 2. Run interactive setup (pick Podman Compose)
make setup

# 3. That's it! Your environment is ready.
```

Then visit:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Database UI:** http://localhost:5050 (admin@admin.com / admin)

---

## Common Workflows

### Develop and Test a Feature

```bash
# 1. Make sure services are running
make docker-up

# 2. Edit code in apps/voiceresumeapp/ (auto-reloads)

# 3. Test your changes
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 4. View logs to debug
make docker-logs
```

### Run Tests

```bash
make docker-test

# Or run specific test
podman-compose -f docker-compose.local.yml exec voiceresumeapp \
  pytest tests/test_auth.py::test_signup -v
```

### Database Debugging

```bash
# Open PgAdmin UI
# Visit http://localhost:5050
# Login: admin@admin.com / admin
# Add server: host=postgres, user=voiceresumeai, password=voiceresumeai

# Or use psql directly
podman-compose -f docker-compose.local.yml exec postgres \
  psql -U voiceresumeai -d voiceresumeai
```

### View S3/File Storage

```bash
# Open Minio UI
# Visit http://localhost:9001
# Login: minioadmin / minioadmin
# Create bucket "voiceresumeai" if it doesn't exist
```

### Database Migrations

```bash
# Create new migration
podman-compose -f docker-compose.local.yml exec voiceresumeapp \
  alembic revision --autogenerate -m "add column"

# Apply migrations
podman-compose -f docker-compose.local.yml exec voiceresumeapp \
  alembic upgrade head

# Rollback one
podman-compose -f docker-compose.local.yml exec voiceresumeapp \
  alembic downgrade -1
```

### Clean Up and Start Fresh

```bash
# Stop all services and remove data
make docker-down
podman-compose -f docker-compose.local.yml down -v

# Then restart
make docker-up
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill the process using the port
lsof -i :8000    # Find what's using port 8000
kill -9 <PID>    # Kill it

# Then restart
make docker-down && make docker-up
```

### Database Connection Failed
```bash
# Wait longer (services take time to start)
podman-compose -f docker-compose.local.yml logs postgres

# If still failing, check postgres is healthy
podman-compose -f docker-compose.local.yml ps
```

### Python Import Errors
```bash
# Make sure you have the right dependencies
podman-compose -f docker-compose.local.yml exec voiceresumeapp \
  pip install -r requirements.txt

# Or rebuild the image
podman-compose -f docker-compose.local.yml build --no-cache voiceresumeapp
```

### Stuck Containers
```bash
# Force remove everything and start fresh
podman-compose -f docker-compose.local.yml down -v
podman-compose -f docker-compose.local.yml up -d
```

---

## Environment Variables

Create `.env.local` with your configuration:

```bash
cp .env.example .env.local
```

Required variables:
- `OPENAI_API_KEY` — Add your key for transcription/resume generation

Optional:
- `LOG_LEVEL` — debug, info, warning, error
- `SQL_ECHO` — true to see SQL queries in logs

---

## Project Structure

```
.
├── apps/voiceresumeapp/          # Main FastAPI application
│   ├── main.py                   # Entry point
│   ├── requirements.txt           # Python dependencies
│   └── tests/                     # Test suite
├── packages/
│   ├── platform_auth/            # Authentication logic
│   └── platform_db/              # Database models
├── docker-compose.local.yml       # Local dev environment
├── Dockerfile                     # Multi-stage Docker build
├── Makefile                       # Development commands
├── SETUP.md                       # Detailed setup guide
└── scripts/setup-local-dev.sh     # Automated setup script
```

---

## Need Help?

- **Setup issues:** See SETUP.md
- **API docs:** http://localhost:8000/docs (when running)
- **Database issues:** Check PgAdmin UI at http://localhost:5050
- **Logs:** `make docker-logs`
- **Code questions:** See README.md architecture section

---

## Development Checklist

- [ ] Podman and podman-compose installed
- [ ] `.env.local` created (with optional OPENAI_API_KEY)
- [ ] Services running (`make docker-up`)
- [ ] API responding (`curl http://localhost:8000/health`)
- [ ] Database accessible (check PgAdmin)
- [ ] Tests passing (`make docker-test`)

✅ Ready to code!
