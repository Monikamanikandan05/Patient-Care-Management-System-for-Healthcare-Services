from sqlalchemy.orm import Session
from models.models import HealthRecord, Doctor, User

def get_health_records(db: Session, patient_id: int):
    return db.query(HealthRecord).filter(HealthRecord.patient_id == patient_id).order_by(HealthRecord.recorded_at.desc()).all()

def add_health_record(db: Session, patient_id: int, doctor_user_id: int, specialty_type: str, diagnosis: str, notes: str, **kwargs):
    """Generic health record creator. All specialty-specific fields are passed via kwargs."""
    doc = db.query(Doctor).filter(Doctor.user_id == doctor_user_id).first()
    doctor_id = doc.id if doc else None
    
    record = HealthRecord(
        patient_id=patient_id,
        doctor_id=doctor_id,
        specialty_type=specialty_type,
        diagnosis=diagnosis,
        notes=notes,
        **kwargs
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
