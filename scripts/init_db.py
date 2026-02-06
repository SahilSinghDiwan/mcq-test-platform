#!/usr/bin/env python3
"""
Initialize database - create all tables
Run this after docker-compose up
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import init_db, SessionLocal
from app.models import User, UserStatus

def initialize_database():
    """Initialize database tables"""
    print("🔄 Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False
    
    return True

def add_sample_users():
    """Add sample users for testing"""
    db = SessionLocal()
    
    sample_users = [
        "wroprojectmedos@gmail.com",
    ]
    
    print("\n🔄 Adding sample users...")
    try:
        for email in sample_users:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                user = User(email=email, status=UserStatus.PENDING)
                db.add(user)
                print(f"  ✓ Added: {email}")
            else:
                print(f"  ⊘ Already exists: {email}")
        
        db.commit()
        print("✓ Sample users added successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error adding users: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MCQ Testing Platform - Database Initialization")
    print("=" * 60)
    
    if not initialize_database():
        sys.exit(1)
    
    if not add_sample_users():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add users: python add_users.py users.csv")
    print("2. Add questions: python upload_questions.py questions.json")
    print("3. Access: http://localhost:3000")