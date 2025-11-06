from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime
import os

# Relative imports within backend package
from . import schemas
from .database import SessionLocal
from .crud import (
    patients,
    doctors,
    appointments,
    admins,
    patient_dashboard_header,
    patient_profiles,
    patient_medical_history,
    patient_dashboard,
    admin_dashboard_header,
    admin_dashboard,
    admin_doctors,
    admin_patients,
    admin_appointments,
    doctor_dashboard_header,
    doctor_dashboard,
    doctor_profiles,
    doctor_appointments,
    doctor_patients,
    patient_detail,
    medical_sessions,
)
from .schemas import AdminAppointmentResponse, AppointmentCreate, AppointmentUpdate

app = FastAPI()

# Mount static files
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/assets", StaticFiles(directory=os.path.join(base_dir, "assets")), name="assets")
app.mount("/pages", StaticFiles(directory=os.path.join(base_dir, "pages")), name="pages")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return credentials.credentials
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
@app.get("/")
def root():
    return FileResponse(os.path.join(base_dir, "index.html"))

@app.get("/api")
def api_root():
    return {"message": "CuraNet API is running"}

@app.post("/patients/register", response_model=schemas.PatientResponse)
def register_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    if patients.get_patient_by_email(db, patient.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if patients.get_patient_by_phone(db, patient.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    return patients.create_patient(db, patient)

@app.post("/doctors/register", response_model=schemas.DoctorResponse)
def register_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    if doctors.get_doctor_by_email(db, doctor.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if doctors.get_doctor_by_phone(db, doctor.phone):
        raise HTTPException(status_code=400, detail="Phone number already registered")
    return doctors.create_doctor(db, doctor)

@app.post("/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    if user.user_type == "patient":
        db_user = patients.verify_patient(db, user.identifier, user.password)
    elif user.user_type == "doctor":
        db_user = doctors.verify_doctor(db, user.identifier, user.password)
    elif user.user_type == "admin":
        db_user = admins.verify_admin(db, user.identifier, user.password)
    else:
        raise HTTPException(status_code=400, detail="Invalid user type. Must be 'patient', 'doctor', or 'admin'")

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "type": user.user_type,
            "department": getattr(db_user, "department", None),
        },
    }

@app.get("/doctor/dashboard-info/{username}", response_model=schemas.DoctorHeaderResponse)
def get_doctor_dashboard_info(username: str, db: Session = Depends(get_db)):
    doctor = doctor_dashboard_header.get_doctor_dashboard_info(db, username)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.get("/doctor/appointments/{username}", response_model=schemas.DoctorDashboardResponse)
def get_doctor_appointments(username: str, db: Session = Depends(get_db)):
    doctor = doctor_dashboard.get_doctor_by_name(db, username)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    appointments = doctor_dashboard.get_doctor_appointments(db, doctor.id)
    return doctor_dashboard.format_dashboard_response(appointments)

@app.put("/doctor/appointment/{appointment_id}")
def update_doctor_appointment(
    appointment_id: int, 
    update_data: schemas.AppointmentUpdate, 
    db: Session = Depends(get_db)
):
    try:
        new_datetime = datetime.strptime(update_data.appointment_time, "%Y-%m-%d %H:%M:%S") if update_data.appointment_time else None
        
        result = doctor_dashboard.update_appointment(
            db, 
            appointment_id, 
            new_datetime=new_datetime,
            new_status=update_data.status
        )
        if not result:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return {"status": "success", "message": "Appointment updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/doctor/profile/{username}")
def get_doctor_profile(username: str, db: Session = Depends(get_db)):
    doctor = doctor_profiles.get_doctor_profile(db, username)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor_profiles.format_profile_response(doctor)

@app.get("/doctor/all-appointments/{username}")
def get_all_doctor_appointments(username: str, db: Session = Depends(get_db)):
    doctor = doctor_appointments.get_doctor_by_name(db, username)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    appointments = doctor_appointments.get_all_doctor_appointments(db, doctor.id)
    return doctor_appointments.format_appointments_response(appointments)

@app.get("/doctor/patients/{username}")
def get_doctor_patients(username: str, db: Session = Depends(get_db)):
    doctor = doctor_patients.get_doctor_by_name(db, username)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    patients = doctor_patients.get_doctor_patients(db, doctor.id)
    return doctor_patients.format_patients_response(patients)

@app.get("/api/patient/{patient_id}")
def get_patient_detail(patient_id: int, db: Session = Depends(get_db)):
    patient_data = patient_detail.get_patient_detail(db, patient_id)
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient_data

# Medical Session Endpoints
@app.post("/appointments/{appointment_id}/start-session")
def start_medical_session(appointment_id: int, db: Session = Depends(get_db)):
    from . import models
    appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    existing_session = db.query(models.MedicalSession).filter(
        models.MedicalSession.appointment_id == appointment_id
    ).first()
    
    if existing_session:
        return {"session_id": existing_session.session_id, "message": "Session already exists"}
    
    session_data = schemas.MedicalSessionCreate(appointment_id=appointment_id)
    session = medical_sessions.create_medical_session(
        db, session_data, appointment.patient_id, appointment.doctor_id
    )
    
    appointment.status = "in_progress"
    db.commit()
    
    return {"session_id": session.session_id, "message": "Medical session started"}

@app.get("/medical-sessions/{session_id}")
def get_medical_session(session_id: int, db: Session = Depends(get_db)):
    session = medical_sessions.get_medical_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Medical session not found")
    return medical_sessions.format_medical_session_response(session, db)

@app.post("/medical-sessions/{session_id}/vital-signs")
def add_vital_signs(
    session_id: int,
    vital_data: schemas.VitalSignCreate,
    db: Session = Depends(get_db)
):
    vital = medical_sessions.add_vital_signs(db, session_id, vital_data)
    return {"message": "Vital signs added", "vital_id": vital.vital_id}

@app.post("/medical-sessions/{session_id}/prescriptions")
def add_prescription(
    session_id: int,
    prescription_data: schemas.PrescriptionCreate,
    db: Session = Depends(get_db)
):
    prescription = medical_sessions.add_prescription(db, session_id, prescription_data)
    return {"message": "Prescription added", "prescription_id": prescription.prescription_id}

@app.post("/medical-sessions/{session_id}/symptoms")
def add_symptom(
    session_id: int,
    symptom_data: schemas.SymptomCreate,
    db: Session = Depends(get_db)
):
    symptom = medical_sessions.add_symptom(db, session_id, symptom_data)
    return {"message": "Symptom added", "symptom_id": symptom.symptom_id}

@app.get("/doctor/{doctor_id}/active-sessions")
def get_doctor_active_sessions(doctor_id: int, db: Session = Depends(get_db)):
    sessions = medical_sessions.get_active_sessions_by_doctor(db, doctor_id)
    return [
        medical_sessions.format_medical_session_response(session, db)
        for session in sessions
    ]

# Patient appointment booking endpoints
@app.get("/patient/available-doctors")
def get_available_doctors_for_patient(db: Session = Depends(get_db)):
    from . import models
    doctors = db.query(models.Doctor).all()
    return [{
        "id": doctor.id,
        "name": doctor.name,
        "department": doctor.department,
        "email": doctor.email
    } for doctor in doctors]

@app.get("/patient/available-slots/{doctor_id}")
def get_available_time_slots(doctor_id: int, date: str, db: Session = Depends(get_db)):
    from . import models
    from datetime import datetime, timedelta
    
    # Parse the date
    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get existing appointments for the doctor on that date
    existing_appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.appointment_time >= selected_date,
        models.Appointment.appointment_time < selected_date + timedelta(days=1)
    ).all()
    
    # Generate available time slots (9 AM to 5 PM, 1-hour intervals)
    available_slots = []
    start_hour = 9
    end_hour = 17
    
    for hour in range(start_hour, end_hour):
        slot_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour))
        
        # Check if this slot is already booked
        is_booked = any(
            appointment.appointment_time.replace(second=0, microsecond=0) == slot_time
            for appointment in existing_appointments
        )
        
        if not is_booked:
            available_slots.append({
                "time": slot_time.strftime("%H:%M"),
                "datetime": slot_time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return available_slots

@app.post("/patient/book-appointment")
def book_patient_appointment(appointment_data: dict, db: Session = Depends(get_db)):
    from . import models
    
    try:
        appointment = models.Appointment(
            patient_id=appointment_data["patient_id"],
            doctor_id=appointment_data["doctor_id"],
            appointment_time=datetime.strptime(appointment_data["appointment_time"], "%Y-%m-%d %H:%M:%S"),
            status="pending"
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return {"message": "Appointment booked successfully", "appointment_id": appointment.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))