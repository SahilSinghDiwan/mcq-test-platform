#!/usr/bin/env python3
"""
Bulk add users from CSV file
Usage: python add_users.py users.csv
"""
import csv
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import User, UserStatus

def add_users_from_csv(filename):
    """Read CSV file and add users to database"""
    db = SessionLocal()
    
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            added = 0
            skipped = 0
            
            for row in reader:
                email = row.get('email', '').strip()
                
                if not email:
                    print(f"⚠ Skipping empty email")
                    skipped += 1
                    continue
                
                # Check if user exists
                existing = db.query(User).filter(User.email == email).first()
                if existing:
                    print(f"⊘ Already exists: {email}")
                    skipped += 1
                    continue
                
                # Add new user
                user = User(
                    email=email,
                    status=UserStatus.PENDING
                )
                db.add(user)
                added += 1
                print(f"✓ Added: {email}")
            
            db.commit()
            print(f"\n✓ Summary: {added} added, {skipped} skipped")
            
    except FileNotFoundError:
        print(f"✗ File not found: {filename}")
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_users.py <csv_file>")
        print("CSV format: email")
        sys.exit(1)
    
    add_users_from_csv(sys.argv[1])