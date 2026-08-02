from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import User, Doctor, Appointment, HealthRecord

def get_admin_stats(db: Session):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_doctors = db.query(func.count(Doctor.id)).scalar() or 0
    total_patients = db.query(func.count(User.id)).filter(User.role == 'Patient').scalar() or 0
    total_appointments = db.query(func.count(Appointment.id)).scalar() or 0
    
    status_counts = db.query(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status).all()
    status_dist = {status: count for status, count in status_counts}
    
    return {
        "total_users": total_users,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "status_distribution": status_dist
    }

def get_doctor_stats(db: Session, doctor_user_id: int):
    doc = db.query(Doctor).filter(Doctor.user_id == doctor_user_id).first()
    if not doc:
        return {"total_appointments": 0, "completed_appointments": 0, "active_patients": 0}
        
    total_appts = db.query(func.count(Appointment.id)).filter(Appointment.doctor_id == doc.id).scalar() or 0
    completed_appts = db.query(func.count(Appointment.id)).filter(Appointment.doctor_id == doc.id, Appointment.status == 'Completed').scalar() or 0
    
    active_patients = db.query(func.count(func.distinct(Appointment.patient_id))).filter(Appointment.doctor_id == doc.id).scalar() or 0
    
    return {
        "total_appointments": total_appts,
        "completed_appointments": completed_appts,
        "active_patients": active_patients
    }
