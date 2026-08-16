from sqlalchemy.orm import Session
from models.models import Appointment, User, Doctor, Specialty
import datetime

def book_appointment(db: Session, patient_id: int, doctor_id: int, date: datetime.date, start_time: datetime.time, reason: str, source: str = "Streamlit"):
    # Check slot availability/conflicts
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.scheduled_date == date,
        Appointment.start_time == start_time,
        Appointment.status != 'Cancelled'
    ).first()
    
    if conflict:
        raise ValueError("This time slot is already booked for this doctor.")
        
    # Calculate end_time (approx 30 mins slot)
    dummy_dt = datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(minutes=30)
    end_time = dummy_dt.time()
    
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        scheduled_date=date,
        start_time=start_time,
        end_time=end_time,
        status="Scheduled",
        reason=reason,
        source=source
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment

def get_appointments_for_user(db: Session, user_id: int, role: str):
    from sqlalchemy.orm import joinedload
    query = db.query(Appointment).options(
        joinedload(Appointment.doctor).joinedload(Doctor.user),
        joinedload(Appointment.doctor).joinedload(Doctor.specialty),
        joinedload(Appointment.patient)
    )
    if role == "Admin":
        return query.order_by(Appointment.scheduled_date.desc(), Appointment.start_time.desc()).all()
    elif role == "Doctor":
        doc = db.query(Doctor).filter(Doctor.user_id == user_id).first()
        if not doc:
            return []
        return query.filter(Appointment.doctor_id == doc.id).order_by(Appointment.scheduled_date.desc(), Appointment.start_time.desc()).all()
    else:
        return query.filter(Appointment.patient_id == user_id).order_by(Appointment.scheduled_date.desc(), Appointment.start_time.desc()).all()

def cancel_appointment(db: Session, appointment_id: int):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appt:
        appt.status = "Cancelled"
        db.commit()
        db.refresh(appt)
    return appt
