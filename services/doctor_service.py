from sqlalchemy.orm import Session
from models.models import Doctor, Specialty, DoctorSlot, User

def get_all_doctors(db: Session):
    return db.query(Doctor).join(User).filter(User.is_active == True).all()

def get_doctors_by_specialty(db: Session, specialty_id: int):
    return db.query(Doctor).join(User).filter(Doctor.specialty_id == specialty_id, User.is_active == True).all()

def get_specialties(db: Session):
    return db.query(Specialty).all()

def get_doctor_slots(db: Session, doctor_id: int):
    return db.query(DoctorSlot).filter(DoctorSlot.doctor_id == doctor_id, DoctorSlot.is_active == True).all()

def add_doctor_profile(db: Session, user_id: int, specialty_id: int, bio: str, experience: int, fee: float, avatar_url: str = None):
    existing = db.query(Doctor).filter(Doctor.user_id == user_id).first()
    if existing:
        existing.specialty_id = specialty_id
        existing.bio = bio
        existing.experience_years = experience
        existing.consultation_fee = fee
        if avatar_url:
            existing.avatar_url = avatar_url
        db.commit()
        db.refresh(existing)
        return existing
        
    doc = Doctor(
        user_id=user_id,
        specialty_id=specialty_id,
        bio=bio,
        experience_years=experience,
        consultation_fee=fee,
        avatar_url=avatar_url
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def create_specialty(db: Session, name: str, description: str, icon: str):
    spec = Specialty(name=name, description=description, icon=icon)
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec

def add_doctor_slot(db: Session, doctor_id: int, day_of_week: int, start_time, end_time):
    slot = DoctorSlot(
        doctor_id=doctor_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        is_active=True
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

def remove_doctor_slot(db: Session, slot_id: int):
    slot = db.query(DoctorSlot).filter(DoctorSlot.id == slot_id).first()
    if slot:
        db.delete(slot)
        db.commit()
        return True
    return False
