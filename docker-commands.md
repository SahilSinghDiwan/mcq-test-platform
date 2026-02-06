To restart Docker Compose:

```bash
docker compose down
docker compose up --build -d
```

---

To whitelist an email:

```bash
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"email":"wroprojectmedos@gmail.com"}'
```

---

To upload questions from `questions.json`:

```bash
docker-compose exec backend python -c "
import json
from app.database import SessionLocal
from app.models import QuestionBank, QuestionDifficulty

with open('scripts/questions.json') as f:
    questions = json.load(f)

db = SessionLocal()

for q in questions:
    existing = db.query(QuestionBank).filter(QuestionBank.image_path == q['image_path']).first()
    if not existing:
        question = QuestionBank(
            image_path=q['image_path'],
            correct_option=q['correct_option'],
            difficulty=QuestionDifficulty[q['difficulty']],
            topic=q.get('topic', ''),
            explanation=q.get('explanation', ''),
            is_active=True
        )
        db.add(question)
        print(f'✓ Added: {q[\"image_path\"]}')
    else:
        print(f'⊘ Already exists: {q[\"image_path\"]}')

db.commit()
db.close()
print(f'✓ Total questions: {len(questions)}')
"
```

---

To count users and questions in the database:

```bash
docker-compose exec db psql -U testadmin -d mcq_platform -c "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as questions FROM question_bank;"
```