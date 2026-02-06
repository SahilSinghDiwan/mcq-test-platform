#!/usr/bin/env python3
"""
Bulk upload questions from JSON file
Usage: python upload_questions.py questions.json
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import QuestionBank, QuestionDifficulty
from app.config import get_settings

settings = get_settings()

def upload_questions_from_json(filename):
    """Read JSON file and add questions to database"""
    db = SessionLocal()
    
    try:
        with open(filename, 'r') as f:
            questions = json.load(f)
        
        if not isinstance(questions, list):
            print("✗ JSON must be an array of questions")
            return
        
        added = 0
        skipped = 0
        
        for q in questions:
            try:
                image_path = q.get('image_path', '').strip()
                correct_option = q.get('correct_option', '').upper()
                difficulty = q.get('difficulty', 'MEDIUM').upper()
                topic = q.get('topic', '').strip()
                explanation = q.get('explanation', '').strip()
                
                # Validate required fields
                if not image_path:
                    print(f"⚠ Skipping: missing image_path")
                    skipped += 1
                    continue
                
                if correct_option not in ['A', 'B', 'C', 'D']:
                    print(f"⚠ Skipping {image_path}: invalid correct_option")
                    skipped += 1
                    continue
                
                # Validate image exists
                full_path = os.path.join(settings.QUESTION_IMAGE_DIR, image_path)
                if not os.path.exists(full_path):
                    print(f"⚠ Skipping {image_path}: image file not found")
                    skipped += 1
                    continue
                
                # Validate difficulty
                try:
                    difficulty_enum = QuestionDifficulty[difficulty]
                except KeyError:
                    print(f"⚠ Skipping {image_path}: invalid difficulty")
                    skipped += 1
                    continue
                
                # Check if already exists
                existing = db.query(QuestionBank).filter(
                    QuestionBank.image_path == image_path
                ).first()
                
                if existing:
                    print(f"⊘ Already exists: {image_path}")
                    skipped += 1
                    continue
                
                # Add new question
                question = QuestionBank(
                    image_path=image_path,
                    correct_option=correct_option,
                    difficulty=difficulty_enum,
                    topic=topic,
                    explanation=explanation,
                    is_active=True
                )
                db.add(question)
                added += 1
                print(f"✓ Added: {image_path} (Answer: {correct_option})")
                
            except Exception as e:
                print(f"✗ Error with question: {e}")
                skipped += 1
        
        db.commit()
        print(f"\n✓ Summary: {added} added, {skipped} skipped")
        
    except FileNotFoundError:
        print(f"✗ File not found: {filename}")
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON format")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_questions.py <json_file>")
        print("\nJSON format:")
        print("""[
  {
    "image_path": "question_001.png",
    "correct_option": "A",
    "difficulty": "EASY",
    "topic": "Python",
    "explanation": "Optional explanation"
  }
]""")
        sys.exit(1)
    
    upload_questions_from_json(sys.argv[1])