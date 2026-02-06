# MCQ Testing Platform

A production-ready, proctored MCQ testing platform built with React, FastAPI, PostgreSQL, and Redis. Features anti-cheat mechanisms, real-time proctoring, and comprehensive result analytics.

## Features

- **OTP-based Authentication**: Secure email verification
- **Anti-Cheat Proctoring**:
  - Tab switching detection
  - Copy/paste prevention
  - DevTools blocking
  - Keyboard shortcut prevention
  - Auto-submit on violations
- **Strict Time Limits**: Per-question countdown timers
- **One-Time Attempt**: Users can only take the test once
- **Real-time Feedback**: Instant warning system
- **Admin Dashboard**: Results viewing and user management
- **Email Notifications**: OTP and completion emails

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Vite, Axios
- **Caching**: Redis
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd mcq-test-platform
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
# Database
POSTGRES_USER=testadmin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=mcq_platform

# Redis
REDIS_URL=redis://redis:6379

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com

# Application
SECRET_KEY=generate_a_secure_key_here
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]

# Test Config
OTP_EXPIRY_MINUTES=5
QUESTION_TIME_LIMIT_SECONDS=120
MAX_BLUR_WARNINGS=2
TOTAL_QUESTIONS_PER_TEST=20
```

### 3. Start Docker Compose

```bash
docker-compose up -d
```

**Wait for services to be healthy** (30-60 seconds):

```bash
docker-compose ps
```

All services should show "healthy" or "running".

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Adding Users

### Option 1: Single User (Manual)

```bash
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

### Option 2: Bulk Users (CSV)

Create `users.csv`:
```csv
email
user1@example.com
user2@example.com
user3@example.com
```

Run the bulk import script:

```bash
python backend/add_users.py users.csv
```

### Option 3: Direct Database Query

```bash
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
INSERT INTO users (email, status, created_at) VALUES 
('user1@example.com', 'PENDING', NOW()),
('user2@example.com', 'PENDING', NOW()),
('user3@example.com', 'PENDING', NOW());
EOF
```

---

## Question Image Generation

The platform uses images for displaying questions. You can generate these images automatically from a JSON file using the provided script.

### Using `scripts/create_test_images.py`

This script reads question data from `scripts/questions.json` and generates a corresponding PNG image for each question, saving them into the `question_images/` directory.

To generate images:

1.  Ensure your `scripts/questions.json` file is correctly formatted with `question`, `options`, `topic`, and `difficulty` fields for each question. An example structure is available in `scripts/questions.json`.
2.  Run the script:
    ```bash
    python scripts/create_test_images.py
    ```
    This will create or overwrite image files in `question_images/` as specified by the `image_path` field in your `questions.json`.

---

## Adding Questions

### Prerequisites

1.  Prepare your question images. You can:
    *   Manually place PNG images in the `question_images/` folder.
    *   Generate them automatically from a `questions.json` file using `scripts/create_test_images.py` (see "Question Image Generation" section above).
2.  Ensure your `questions.json` file (if used) references the correct `image_path` for each question.

### Option 1: Via Admin API

```bash
curl -X POST http://localhost:8000/admin/questions \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "question_001_python_easy.png",
    "correct_option": "A",
    "difficulty": "EASY",
    "topic": "Python",
    "explanation": "Explanation of the answer"
  }'
```

### Option 2: Bulk Import (JSON)

Create `questions.json`:
```json
[
  {
    "image_path": "question_001_python_easy.png",
    "correct_option": "A",
    "difficulty": "EASY",
    "topic": "Python",
    "explanation": "Explanation"
  },
  {
    "image_path": "question_002_python_medium.png",
    "correct_option": "B",
    "difficulty": "MEDIUM",
    "topic": "Python",
    "explanation": "Explanation"
  }
]
```

Run the bulk import script:

```bash
python backend/upload_questions.py questions.json
```

### Option 3: Create Helper Script

Create `backend/bulk_questions.py`:

```python
import json
import requests

API_URL = "http://localhost:8000/admin/questions"

with open("questions.json") as f:
    questions = json.load(f)

for q in questions:
    response = requests.post(API_URL, json=q)
    if response.status_code == 200:
        print(f"✓ Added: {q['image_path']}")
    else:
        print(f"✗ Failed: {q['image_path']} - {response.text}")
```

Run:
```bash
python backend/bulk_questions.py
```

---

## Managing Users & Results

### View All Users

```bash
curl http://localhost:8000/admin/whitelist
```

### View User Results

```bash
curl http://localhost:8000/admin/results/user@example.com
```

### View All Results

```bash
curl http://localhost:8000/admin/results
```

### Reset User (Allow Retake)

```bash
curl -X POST http://localhost:8000/admin/reset-user/user@example.com
```

### Block User

```bash
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
UPDATE users SET status = 'BLOCKED' WHERE email = 'user@example.com';
EOF
```

---

## Docker Compose Commands

### Start All Services

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
docker-compose logs -f redis
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Data

```bash
docker-compose down -v
```

### Rebuild Services

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## Troubleshooting

### 1. Services Won't Start

**Problem**: `docker-compose up` fails

**Solutions**:
```bash
# Check Docker daemon
docker ps

# Check logs
docker-compose logs

# Restart Docker
docker-compose down
docker-compose up -d

# Check ports are free
lsof -i :3000    # Frontend
lsof -i :8000    # Backend
lsof -i :5432    # Database
lsof -i :6379    # Redis
```

### 2. Database Connection Failed

**Problem**: Backend can't connect to PostgreSQL

**Solutions**:
```bash
# Check database is running
docker-compose ps db

# Check database health
docker-compose exec db pg_isready -U testadmin

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### 3. Redis Connection Failed

**Problem**: Backend can't connect to Redis

**Solutions**:
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### 4. Frontend Can't Reach Backend

**Problem**: CORS errors or 502 Bad Gateway

**Solutions**:
```bash
# Check backend is healthy
curl http://localhost:8000/health

# Check CORS_ORIGINS in .env includes frontend URL
# Default: http://localhost:3000

# Restart frontend
docker-compose restart frontend

# Check logs
docker-compose logs frontend
```

### 5. Questions Not Loading

**Problem**: 404 errors when fetching images

**Solutions**:
```bash
# Check question_images folder exists
ls -la question_images/

# Check files are there
ls question_images/ | head

# Verify file permissions
chmod 755 question_images/*

# Restart backend
docker-compose restart backend
```

### 6. OTP Email Not Sending

**Problem**: Emails fail with SMTP error

**Solutions**:
```bash
# Verify SMTP credentials in .env
- Gmail: Enable "App Passwords" (2FA required)
- Check SMTP_HOST and SMTP_PORT
- Verify SMTP_USER and SMTP_PASSWORD

# Test SMTP connection (in backend container)
docker-compose exec backend python << EOF
import smtplib
from app.config import get_settings

settings = get_settings()
try:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    print("✓ SMTP connection successful")
except Exception as e:
    print(f"✗ SMTP failed: {e}")
EOF
```

### 7. Slow Performance / Memory Issues

**Problem**: High CPU/memory usage

**Solutions**:
```bash
# Check resource usage
docker stats

# Reduce Redis memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb

# Check database connections
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
SELECT count(*) FROM pg_stat_activity;
EOF

# Clear old sessions
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
DELETE FROM test_sessions WHERE created_at < NOW() - INTERVAL '7 days';
EOF
```

### 8. Database Migration Issues

**Problem**: Tables not created

**Solutions**:
```bash
# Check tables exist
docker-compose exec db psql -U testadmin -d mcq_platform << EOF
\dt
EOF

# Recreate tables (CAREFUL - deletes data)
docker-compose exec backend python << EOF
from app.database import init_db
init_db()
print("✓ Tables created")
EOF
```

### 9. Port Already in Use

**Problem**: `Error: bind: address already in use`

**Solutions**:
```bash
# Find and kill process using port
lsof -i :8000 | grep LISTEN
kill -9 <PID>

# Or change port in docker-compose.yml
# Change: "8000:8000" to "8001:8000"
```

### 10. Clear All Data (Nuclear Option)

```bash
# Stop and remove everything
docker-compose down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Restart fresh
docker-compose up -d
```

---

## Production Deployment

### Before Going Live

1. **Security**:
   - Change all default passwords
   - Use strong SECRET_KEY (min 32 chars)
   - Enable HTTPS/SSL
   - Set DEBUG=false
   - Restrict CORS_ORIGINS

2. **Database**:
   - Enable PostgreSQL backups
   - Use strong database password
   - Set max_connections appropriately

3. **Email**:
   - Use production SMTP service
   - Test email delivery
   - Set up bounce handling

4. **Monitoring**:
   - Set up error logging
   - Monitor disk space
   - Monitor memory usage
   - Set up alerts

### Environment Variables for Production

```env
DEBUG=false
SECRET_KEY=generate_random_32_char_string
DATABASE_URL=postgresql://prod_user:prod_password@prod_host:5432/mcq_platform
REDIS_URL=redis://prod_redis_host:6379
CORS_ORIGINS=["https://yourdomain.com"]
SMTP_HOST=production.smtp.service
```

---

## API Endpoints

### Authentication
- `POST /auth/request-otp` - Request OTP
- `POST /auth/verify-otp` - Verify OTP & get token
- `GET /auth/status` - Check service status

### Test
- `POST /test/start` - Start test
- `GET /test/question/{number}` - Get question
- `GET /test/image/{number}` - Get question image
- `POST /test/submit-answer` - Submit answer
- `GET /test/status` - Get test status
- `POST /test/complete` - Complete test
- `POST /test/proctor-event` - Log proctoring event

### Admin
- `POST /admin/whitelist` - Add user
- `DELETE /admin/whitelist/{email}` - Remove user
- `GET /admin/whitelist` - List users
- `GET /admin/results` - Get all results
- `GET /admin/results/{email}` - Get user result
- `POST /admin/questions` - Add question
- `GET /admin/questions` - List questions
- `PUT /admin/questions/{id}/deactivate` - Deactivate question
- `POST /admin/reset-user/{email}` - Reset user
- `GET /admin/statistics` - Get statistics

---

## File Structure

```
mcq-test-platform/
├── README.md
├── .env
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── redis_client.py
│   │   ├── email_service.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── test.py
│   │       └── admin.py
│   ├── add_users.py
│   ├── upload_questions.py
│   └── bulk_questions.py
├── frontend/
│   ├── Dockerfile
│   ├── .gitignore
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── styles/index.css
│       ├── components/
│       ├── hooks/
│       └── utils/
├── database/
│   ├── init.sql
│   └── seed.sql
└── question_images/
    └── (question PNG files)
```

---

## Support & Issues

For issues, check:
1. Docker logs: `docker-compose logs`
2. Browser console: DevTools F12
3. Backend health: `curl http://localhost:8000/health`
4. Database: `docker-compose exec db psql ...`

---

## License

Proprietary - All Rights Reserved