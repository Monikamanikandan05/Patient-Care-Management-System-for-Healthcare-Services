import datetime
from core.database import engine, Base, SessionLocal
from core.security import hash_password
from models.models import User, Specialty, Doctor, DoctorSlot, HealthRecord, Appointment

def seed_database():
    # 1. Recreate tables
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Add Specialties (Multi-Specialty Sector Expansion)
        print("Seeding specialties...")
        cardio = Specialty(name="Cardiology", description="Non-invasive cardiovascular diagnostics and disease management", icon="❤️")
        surgery = Specialty(name="Cardiac Surgery", description="Surgical operations on the heart and major blood vessels", icon="🫀")
        dentistry = Specialty(name="Dentistry", description="Comprehensive dental care, orthodontics, oral hygiene, and cosmetic dental treatments", icon="🦷")
        ophthalmology = Specialty(name="Ophthalmology", description="Vision correction, cataract treatments, and diagnostic eye surgeries", icon="👁️")
        pulmonology = Specialty(name="Pulmonology (Chest)", description="Treatment of lung diseases, chronic asthma, COPD, and chest infections", icon="🫁")
        orthopedics = Specialty(name="Orthopedics (Injury)", description="Bone fractures, joint replacements, sports injuries, and leg/muscle trauma rehabilitation", icon="🦵")
        
        db.add_all([cardio, surgery, dentistry, ophthalmology, pulmonology, orthopedics])
        db.commit()
        
        # 3. Add Users
        print("Seeding default users...")
        admin = User(
            full_name="Administrator",
            email="admin@smartcare.com",
            password_hash=hash_password("admin123"),
            role="Admin",
            gender="Female",
            phone="9876543210"
        )
        
        # Cardiology
        doc_user_1 = User(full_name="Dr. Sarah Jenkins", email="doctor@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Female", phone="9123456780")
        doc_user_2 = User(full_name="Dr. Rajesh Malhotra", email="malhotra@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456783")
        
        # Cardiac Surgery
        doc_user_3 = User(full_name="Dr. Michael Chen", email="chen@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456781")
        doc_user_4 = User(full_name="Dr. Sarah Al-Mansoori", email="mansoori@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Female", phone="9123456784")
        
        # Dentistry
        doc_user_5 = User(full_name="Dr. Hermione Granger", email="granger@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Female", phone="9123456786")
        doc_user_6 = User(full_name="Dr. Arthur Dent", email="dent@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456787")
        
        # Ophthalmology
        doc_user_7 = User(full_name="Dr. Scott Summers", email="summers@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456788")
        doc_user_8 = User(full_name="Dr. Geordi La Forge", email="laforge@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456789")
        
        # Pulmonology (Chest)
        doc_user_9 = User(full_name="Dr. John Watson", email="watson@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456790")
        doc_user_10 = User(full_name="Dr. Leonard McCoy", email="mccoy@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456791")
        
        # Orthopedics (Injury)
        doc_user_11 = User(full_name="Dr. Stephen Strange", email="strange@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Male", phone="9123456792")
        doc_user_12 = User(full_name="Dr. Meredith Grey", email="grey@smartcare.com", password_hash=hash_password("doctor123"), role="Doctor", gender="Female", phone="9123456793")
        
        patient_user = User(
            full_name="John Doe",
            email="patient@smartcare.com",
            password_hash=hash_password("patient123"),
            role="Patient",
            gender="Male",
            phone="9812739182",
            dob=datetime.date(1982, 5, 14)
        )
        patient_user_2 = User(
            full_name="Monika",
            email="monikasmartcare@gmail.com",
            password_hash=hash_password("monika123"),
            role="Patient",
            gender="Female",
            phone="9876543211",
            dob=datetime.date(2005, 10, 1)
        )
        
        all_users = [
            admin, patient_user, patient_user_2,
            doc_user_1, doc_user_2, doc_user_3, doc_user_4, doc_user_5, doc_user_6,
            doc_user_7, doc_user_8, doc_user_9, doc_user_10, doc_user_11, doc_user_12
        ]
        db.add_all(all_users)
        db.commit()
        
        # 4. Add Doctor Profiles
        print("Seeding doctor profiles...")
        # Cardiology
        doctor_profile_1 = Doctor(user_id=doc_user_1.id, specialty_id=cardio.id, bio="Lead clinical cardiologist specializing in valvular diseases, heart failure, and preventive care.", experience_years=12, consultation_fee=120.00)
        doctor_profile_2 = Doctor(user_id=doc_user_2.id, specialty_id=cardio.id, bio="Experienced general cardiologist focusing on non-invasive imaging, lipidology, and hypertension management.", experience_years=10, consultation_fee=110.00)
        
        # Surgery
        doctor_profile_3 = Doctor(user_id=doc_user_3.id, specialty_id=surgery.id, bio="Renowned cardiothoracic surgeon expert in coronary artery bypass grafting (CABG) and valve repair surgery.", experience_years=18, consultation_fee=250.00)
        doctor_profile_4 = Doctor(user_id=doc_user_4.id, specialty_id=surgery.id, bio="Specialist in minimally invasive heart surgeries, thoracic aortic aneurysm repair, and heart transplants.", experience_years=15, consultation_fee=275.00)
        
        # Dentistry
        doctor_profile_5 = Doctor(user_id=doc_user_5.id, specialty_id=dentistry.id, bio="Orthodontist and general cosmetic dentist specializing in aesthetic restorations and pediatric dental health.", experience_years=8, consultation_fee=85.00)
        doctor_profile_6 = Doctor(user_id=doc_user_6.id, specialty_id=dentistry.id, bio="Specialist in oral implantology, root canal treatments, and preventative periodontal disease care.", experience_years=11, consultation_fee=80.00)
        
        # Ophthalmology
        doctor_profile_7 = Doctor(user_id=doc_user_7.id, specialty_id=ophthalmology.id, bio="Refractive eye surgeon expert in LASIK surgery, pediatric ophthalmology, and early glaucoma screening.", experience_years=14, consultation_fee=105.00)
        doctor_profile_8 = Doctor(user_id=doc_user_8.id, specialty_id=ophthalmology.id, bio="Ophthalmic surgeon specialized in diabetic retinopathy management, advanced macular degeneration, and premium cataract lens implants.", experience_years=16, consultation_fee=120.00)
        
        # Pulmonology (Chest)
        doctor_profile_9 = Doctor(user_id=doc_user_9.id, specialty_id=pulmonology.id, bio="Pulmonary physician specializing in sleep apnea therapies, lung biopsy interpretations, and chronic asthma care.", experience_years=13, consultation_fee=115.00)
        doctor_profile_10 = Doctor(user_id=doc_user_10.id, specialty_id=pulmonology.id, bio="Chest specialist experienced in critical lung care, post-tuberculosis care, COPD management, and severe lung infections.", experience_years=20, consultation_fee=150.00)
        
        # Orthopedics (Injury)
        doctor_profile_11 = Doctor(user_id=doc_user_11.id, specialty_id=orthopedics.id, bio="Orthopedic surgeon expert in leg reconstruction, major bone fracture alignments, joint replacements, and emergency trauma medicine.", experience_years=22, consultation_fee=220.00)
        doctor_profile_12 = Doctor(user_id=doc_user_12.id, specialty_id=orthopedics.id, bio="Sports medicine specialist focusing on ligament repairs, arthroscopic surgeries, and knee/ankle mobility therapies.", experience_years=9, consultation_fee=135.00)
        
        all_profiles = [
            doctor_profile_1, doctor_profile_2, doctor_profile_3, doctor_profile_4, doctor_profile_5, doctor_profile_6,
            doctor_profile_7, doctor_profile_8, doctor_profile_9, doctor_profile_10, doctor_profile_11, doctor_profile_12
        ]
        db.add_all(all_profiles)
        db.commit()
        
        # 5. Add Doctor Slots
        print("Seeding doctor availability slots...")
        slots = []
        for profile in all_profiles:
            for day in range(0, 5): # Mon to Fri
                slots.append(DoctorSlot(doctor_id=profile.id, day_of_week=day, start_time=datetime.time(9, 0), end_time=datetime.time(9, 30)))
                slots.append(DoctorSlot(doctor_id=profile.id, day_of_week=day, start_time=datetime.time(10, 0), end_time=datetime.time(10, 30)))
                slots.append(DoctorSlot(doctor_id=profile.id, day_of_week=day, start_time=datetime.time(11, 0), end_time=datetime.time(11, 30)))
                slots.append(DoctorSlot(doctor_id=profile.id, day_of_week=day, start_time=datetime.time(14, 0), end_time=datetime.time(14, 30)))
                slots.append(DoctorSlot(doctor_id=profile.id, day_of_week=day, start_time=datetime.time(15, 0), end_time=datetime.time(15, 30)))
        db.add_all(slots)
        
        # 6. Add Health Records
        print("Seeding sample health vitals records...")
        record = HealthRecord(
            patient_id=patient_user.id,
            doctor_id=doctor_profile_1.id,
            specialty_type="Cardiology",
            heart_rate=78,
            blood_pressure="122/80",
            troponin=0.012,
            ejection_fraction=56,
            cardiac_output=5.20,
            pulse_oximetry=98,
            ecg_note="Normal Sinus Rhythm",
            diagnosis="Slightly elevated systolic blood pressure. Cardiac output and cardiac markers are normal.",
            notes="Advised daily cardio walks of 30 minutes. Limit sodium intake to under 1500mg. Re-check vitals in two weeks."
        )
        record_2 = HealthRecord(
            patient_id=patient_user_2.id,
            doctor_id=doctor_profile_1.id,
            specialty_type="Cardiology",
            heart_rate=72,
            blood_pressure="120/80",
            troponin=0.010,
            ejection_fraction=60,
            cardiac_output=5.00,
            pulse_oximetry=99,
            ecg_note="Normal Sinus Rhythm",
            diagnosis="Excellent cardiovascular health and active vitals.",
            notes="Keep maintaining your balanced diet and workout routine."
        )
        record_3 = HealthRecord(
            patient_id=patient_user_2.id,
            doctor_id=doctor_profile_5.id,
            specialty_type="Dentistry",
            teeth_condition="Healthy",
            gum_health="Healthy",
            xray_finding="No cavities detected",
            procedure_done="Scaling & Polishing",
            next_dental_visit="6 months",
            diagnosis="Routine scaling completed. Excellent oral hygiene maintained.",
            notes="Advised to continue brushing twice daily and flossing."
        )
        record_4 = HealthRecord(
            patient_id=patient_user_2.id,
            doctor_id=doctor_profile_7.id,
            specialty_type="Ophthalmology",
            right_eye_vision="6/6",
            left_eye_vision="6/6",
            eye_pressure_iop="14 mmHg",
            retina_status="Normal",
            eye_condition="None",
            diagnosis="Standard optometry scan normal. Perfect 20/20 bilateral vision.",
            notes="No corrective lenses required. Protect eyes from blue screen fatigue."
        )
        record_5 = HealthRecord(
            patient_id=patient_user_2.id,
            doctor_id=doctor_profile_9.id,
            specialty_type="Pulmonology (Chest)",
            respiratory_rate=16,
            oxygen_saturation=98,
            fev1="85%",
            chest_xray_finding="Clear lung fields",
            lung_condition="Healthy",
            diagnosis="Healthy respiration rate. Clear lung inflation, no asthma symptoms.",
            notes="Ensure active hydration and breathing exercises."
        )
        record_6 = HealthRecord(
            patient_id=patient_user_2.id,
            doctor_id=doctor_profile_11.id,
            specialty_type="Orthopedics (Injury)",
            injury_location="Right Knee",
            fracture_type="None",
            mri_xray_finding="No ligament tear / minor tendon strain",
            mobility_score=9,
            treatment_plan="Rest & Observation",
            diagnosis="Mild patellar tendon strain from physical training.",
            notes="Apply ice pack twice daily. Avoid running for 3 days."
        )
        db.add_all([record, record_2, record_3, record_4, record_5, record_6])
        db.commit()
        
        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
