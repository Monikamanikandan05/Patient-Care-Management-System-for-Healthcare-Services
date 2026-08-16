from sqlalchemy import Column, Integer, String, Date, Time, Boolean, Numeric, Text, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('Admin', 'Doctor', 'Patient'), nullable=False)
    gender = Column(String(20))
    dob = Column(Date)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    health_records = relationship("HealthRecord", foreign_keys="[HealthRecord.patient_id]", back_populates="patient")
    appointments = relationship("Appointment", foreign_keys="[Appointment.patient_id]", back_populates="patient")
    chat_messages = relationship("ChatMessage", back_populates="user")

class Specialty(Base):
    __tablename__ = 'specialties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False, unique=True)
    description = Column(String(255))
    icon = Column(String(16))
    
    doctors = relationship("Doctor", back_populates="specialty")

class Doctor(Base):
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    specialty_id = Column(Integer, ForeignKey('specialties.id'))
    bio = Column(Text)
    experience_years = Column(Integer)
    consultation_fee = Column(Numeric(10, 2))
    avatar_url = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    specialty = relationship("Specialty", back_populates="doctors")
    slots = relationship("DoctorSlot", back_populates="doctor")
    appointments = relationship("Appointment", foreign_keys="[Appointment.doctor_id]", back_populates="doctor")
    prescribed_records = relationship("HealthRecord", foreign_keys="[HealthRecord.doctor_id]", back_populates="doctor")

class DoctorSlot(Base):
    __tablename__ = 'doctor_slots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    
    doctor = relationship("Doctor", back_populates="slots")

class Appointment(Base):
    __tablename__ = 'appointments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    status = Column(String(20), default="Scheduled") # Scheduled, Completed, Cancelled
    reason = Column(String(255))
    source = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    
    patient = relationship("User", foreign_keys=[patient_id], back_populates="appointments")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], back_populates="appointments")

class HealthRecord(Base):
    __tablename__ = 'health_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    recorded_at = Column(DateTime, server_default=func.now())
    specialty_type = Column(String(80))  # 'Cardiology', 'Dentistry', 'Ophthalmology', 'Pulmonology', 'Orthopedics'

    # ── Cardiology / Cardiac Surgery fields ───────────────────────────────────
    heart_rate = Column(Integer)
    blood_pressure = Column(String(20))
    troponin = Column(Numeric(6, 3))
    ejection_fraction = Column(Integer)
    cardiac_output = Column(Numeric(5, 2))
    pulse_oximetry = Column(Integer)
    ecg_note = Column(String(120))

    # ── Dentistry fields ───────────────────────────────────────────────────────
    teeth_condition = Column(String(120))      # e.g. Healthy, Cavities, Plaque Build-up
    gum_health = Column(String(80))            # e.g. Healthy, Gingivitis, Periodontitis
    xray_finding = Column(String(255))         # e.g. No abnormalities / Root canal required
    procedure_done = Column(String(120))       # e.g. Scaling, Filling, Root Canal
    next_dental_visit = Column(String(80))     # e.g. 6 months

    # ── Ophthalmology fields ───────────────────────────────────────────────────
    right_eye_vision = Column(String(20))      # e.g. 6/6, 6/12
    left_eye_vision = Column(String(20))
    eye_pressure_iop = Column(String(20))      # Intraocular pressure, e.g. 14 mmHg
    retina_status = Column(String(120))        # e.g. Normal, Diabetic Retinopathy
    eye_condition = Column(String(120))        # e.g. Myopia, Glaucoma, Cataract

    # ── Pulmonology (Chest) fields ─────────────────────────────────────────────
    respiratory_rate = Column(Integer)         # breaths per minute
    oxygen_saturation = Column(Integer)        # SpO2 %
    fev1 = Column(String(20))                  # Forced Expiratory Volume e.g. 82%
    chest_xray_finding = Column(String(255))   # e.g. Clear, Consolidation seen
    lung_condition = Column(String(120))       # e.g. Asthma, COPD, Pneumonia

    # ── Orthopedics (Injury) fields ────────────────────────────────────────────
    injury_location = Column(String(120))      # e.g. Right Knee, Left Ankle
    fracture_type = Column(String(120))        # e.g. Hairline fracture, Compound fracture
    mri_xray_finding = Column(String(255))     # e.g. ACL Tear, No structural damage
    mobility_score = Column(Integer)           # 0-10 scale
    treatment_plan = Column(String(255))       # e.g. Physiotherapy 6 weeks, Cast

    # ── Common fields ──────────────────────────────────────────────────────────
    diagnosis = Column(String(255))
    notes = Column(Text)

    # ── General Health Metrics (for personal health reports) ───────────────────
    weight = Column(Numeric(5, 2))             # kg
    height = Column(Numeric(5, 2))             # cm
    bmi = Column(Numeric(4, 1))
    blood_sugar = Column(Integer)              # mg/dL
    cholesterol = Column(Integer)              # mg/dL
    surgeries = Column(Text)                   # comma-separated or json
    vaccinations = Column(Text)                # comma-separated or json

    patient = relationship("User", foreign_keys=[patient_id], back_populates="health_records")
    doctor = relationship("Doctor", foreign_keys=[doctor_id], back_populates="prescribed_records")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20)) # user, assistant
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="chat_messages")


class PharmacyMedicine(Base):
    __tablename__ = 'pharmacy_medicines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    generic_name = Column(String(120))
    category = Column(String(80))  # e.g. Cardiology, Antibiotic, Cough & Cold
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock_qty = Column(Integer, default=0)
    unit = Column(String(40), default='Tablet')  # Tablet, Capsule, Syrup, etc.
    requires_prescription = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    image_path = Column(String(255))  # relative path under assets/pharmacy/
    color_theme = Column(String(20), default='#a855f7')  # card accent color
    manufacture_date = Column(Date, nullable=True)   # batch manufacture date
    expiry_date = Column(Date, nullable=True)         # batch expiry date
    created_at = Column(DateTime, server_default=func.now())

    order_items = relationship('PharmacyOrderItem', back_populates='medicine')


class PharmacyOrder(Base):
    __tablename__ = 'pharmacy_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), default='Pending')  # Pending, Confirmed, Delivered, Cancelled
    created_at = Column(DateTime, server_default=func.now())

    patient = relationship('User', foreign_keys=[patient_id])
    items = relationship('PharmacyOrderItem', back_populates='order', cascade='all, delete-orphan')


class PharmacyOrderItem(Base):
    __tablename__ = 'pharmacy_order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('pharmacy_orders.id'), nullable=False)
    medicine_id = Column(Integer, ForeignKey('pharmacy_medicines.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    order = relationship('PharmacyOrder', back_populates='items')
    medicine = relationship('PharmacyMedicine', back_populates='order_items')


class OCRDocument(Base):
    __tablename__ = 'ocr_documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50))
    status = Column(String(50), default='Pending') # Pending, Processing, NeedsReview, Approved, Rejected, Error
    document_type = Column(String(50)) # prescription, lab_report, etc
    extracted_data = Column(Text) # JSON string of the structured output
    overall_confidence = Column(Numeric(5, 4))
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    patient = relationship("User", foreign_keys=[patient_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])

