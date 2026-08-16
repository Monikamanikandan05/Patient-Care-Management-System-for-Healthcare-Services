import sys
sys.path.insert(0, r"c:\Users\monik\OneDrive\Desktop\integrated_patient_care_management_system")

from sqlalchemy.orm import Session
from database.db_config import SessionLocal
from models.models import ChatMessage

def clean_db():
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).all()
        updated = 0
        for msg in messages:
            if not msg.content:
                continue
            new_content = (msg.content.replace("<br>", "\n")
                           .replace("<br/>", "\n")
                           .replace("<br />", "\n")
                           .replace("<b>", "**")
                           .replace("</b>", "**"))
            if new_content != msg.content:
                msg.content = new_content
                updated += 1
        db.commit()
        print(f"Updated {updated} chat messages in the database!")
    finally:
        db.close()

if __name__ == "__main__":
    clean_db()
