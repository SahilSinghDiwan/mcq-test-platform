# MCQ Testing Platform - Deployment Checklist

## Pre-Deployment Setup

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Generate secure `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set strong database password
- [ ] Configure SMTP credentials
- [ ] Set `DEBUG=false` for production
- [ ] Set correct `CORS_ORIGINS` for your domain

### 2. Question Bank
- [ ] Place all question images in `question_images/` folder
- [ ] Ensure images are named: `question_XXX_topic.png`
- [ ] Verify image file formats (PNG recommended)
- [ ] Create `questions.json` with question metadata
- [ ] Run: `python upload_questions.py questions.json`
- [ ] Verify at least 20 questions loaded

### 3. User Management
- [ ] Create `users.csv` with whitelisted emails
- [ ] Run: `python add_users.py users.csv`
- [ ] Verify users created: `curl http://localhost:8000/admin/whitelist`

### 4. Docker Setup
- [ ] Verify Docker daemon running
- [ ] Check available disk space (min 5GB)
- [ ] Verify ports 3000, 8000, 5432, 6379 are free
- [ ] Build images: `docker-compose build`

### 5. Database
- [ ] Create backup of initial schema
- [ ] Verify database connectivity
- [ ] Check all tables created
- [ ] Run: `docker-compose exec db psql -U testadmin -d mcq_platform \dt`

### 6. Email Testing
- [ ] Test SMTP connection
- [ ] Send test OTP email
- [ ] Verify email delivery
- [ ] Check email formatting

## Startup Commands

### Initial Start
```bash
# Start all services
docker-compose up -d

# Wait for healthy status
sleep 30
docker-compose ps

# Verify services
curl http://localhost:8000/health
curl http://localhost:3000
```

### Load Questions
```bash
python upload_questions.py questions.json
```

### Load Users
```bash
python add_users.py users.csv
```

### Verify Setup
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check database tables
docker-compose exec db psql -U testadmin -d mcq_platform \dt

# Check Redis
docker-compose exec redis redis-cli ping

# Check question count
curl http://localhost:8000/admin/questions | grep -o '"id"' | wc -l

# Check user count
curl http://localhost:8000/admin/whitelist | grep -o '"email"' | wc -l
```

## Daily Operations

### Monitor Services
```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f --tail=100

# Specific service logs
docker-compose logs backend
docker-compose logs frontend
```

### Backup Database
```bash
# Backup
docker-compose exec db pg_dump -U testadmin mcq_platform > backup.sql

# Restore
docker-compose exec -T db psql -U testadmin mcq_platform < backup.sql
```

### View Results
```bash
# All results
curl http://localhost:8000/admin/results

# Specific user
curl http://localhost:8000/admin/results/email@example.com

# Statistics
curl http://localhost:8000/admin/statistics
```

### Manage Users
```bash
# Add single user
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com"}'

# Remove user
curl -X DELETE http://localhost:8000/admin/whitelist/old@example.com

# Reset user (allow retake)
curl -X POST http://localhost:8000/admin/reset-user/email@example.com

# Block user
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
UPDATE users SET status = 'BLOCKED' WHERE email = 'email@example.com';
EOF
```

## Troubleshooting Quick Guide

### Services Won't Start
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Error
```bash
docker-compose restart db
docker-compose exec db pg_isready -U testadmin
```

### Frontend Not Loading
```bash
docker-compose restart frontend
docker-compose logs frontend
curl http://localhost:3000
```

### API Not Responding
```bash
docker-compose restart backend
docker-compose logs backend
curl http://localhost:8000/health
```

### Email Not Sending
```bash
# Verify SMTP credentials
echo $SMTP_USER $SMTP_PASSWORD

# Test SMTP
docker-compose exec backend python << 'EOF'
from app.config import get_settings
import smtplib

s = get_settings()
try:
    srv = smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT)
    srv.starttls()
    srv.login(s.SMTP_USER, s.SMTP_PASSWORD)
    srv.quit()
    print("✓ SMTP OK")
except Exception as e:
    print(f"✗ SMTP Failed: {e}")
EOF
```

### Images Not Loading
```bash
# Check files exist
ls -la question_images/ | head

# Fix permissions
chmod 755 question_images/*

# Restart backend
docker-compose restart backend
```

### Port Already in Use
```bash
# Find process
lsof -i :8000
lsof -i :3000
lsof -i :5432
lsof -i :6379

# Kill process (if needed)
kill -9 <PID>
```

## Performance Optimization

### Database Optimization
```bash
# Analyze database
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
ANALYZE;
REINDEX DATABASE mcq_platform;
EOF

# Vacuum old data
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
DELETE FROM test_sessions WHERE created_at < NOW() - INTERVAL '30 days';
VACUUM ANALYZE;
EOF
```

### Redis Optimization
```bash
# Check memory
docker-compose exec redis redis-cli INFO memory

# Set max memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Save config
docker-compose exec redis redis-cli CONFIG REWRITE
```

### Backend Optimization
```bash
# Increase workers in production
# Edit Dockerfile:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Security Checklist

- [ ] Change default database password
- [ ] Generate strong SECRET_KEY
- [ ] Disable DEBUG mode
- [ ] Set specific CORS_ORIGINS
- [ ] Use HTTPS in production
- [ ] Restrict admin endpoints
- [ ] Enable database backups
- [ ] Monitor error logs
- [ ] Rotate SMTP credentials periodically
- [ ] Keep Docker images updated

## Maintenance Schedule

### Daily
- Monitor service health
- Check error logs
- Verify database connectivity

### Weekly
- Backup database
- Review test results
- Check disk space

### Monthly
- Database optimization
- Docker image updates
- Security audit
- Performance review

### Quarterly
- Complete backup test restore
- Security assessment
- Capacity planning

## Emergency Procedures

### Complete System Restart
```bash
docker-compose down
docker system prune -a --volumes
docker-compose up -d
```

### Data Recovery
```bash
# From backup
docker-compose exec -T db psql -U testadmin mcq_platform < backup.sql
```

### Database Corruption
```bash
docker-compose down
docker volume rm mcq-postgres-data
docker-compose up -d
# Restore from backup
```

### All Data Loss (Clean Start)
```bash
docker-compose down -v
docker-compose up -d
python add_users.py users.csv
python upload_questions.py questions.json
```

---

**For detailed troubleshooting, see README.md**