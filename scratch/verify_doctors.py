from core.database import SessionLocal
from models.models import User, Doctor, Specialty

db = SessionLocal()
try:
    doctors = db.query(Doctor).all()
    print("DOCTORS IN DATABASE:")
    for d in doctors:
        user = db.query(User).filter(User.id == d.user_id).first()
        spec = db.query(Specialty).filter(Specialty.id == d.specialty_id).first()
        print(f"Doctor User ID: {d.user_id}, Name: {user.full_name if user else 'N/A'}, Role: {user.role if user else 'N/A'}, Specialty ID: {d.specialty_id}, Specialty Name: {spec.name if spec else 'N/A'}")
finally:
    db.close()
