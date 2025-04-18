"""
Check device IDs in database
"""
import sys
from app import app, db
from models import HealthData, SafetyAlert, Reminder, Patient

print("Script is running...")
sys.stdout.flush()

with app.app_context():
    print("In app context")
    sys.stdout.flush()
    
    # Get all patients
    patients = Patient.query.all()
    print('Patients in database:', [(p.patient_id, p.name) for p in patients])
    sys.stdout.flush()
    
    # Get device IDs from health data
    health_device_ids = [d[0] for d in db.session.query(HealthData.patient_id.distinct()).all()]
    print('Device IDs in health data:', health_device_ids)
    sys.stdout.flush()
    
    # Get device IDs from safety alerts
    safety_device_ids = [d[0] for d in db.session.query(SafetyAlert.patient_id.distinct()).all()]
    print('Device IDs in safety alerts:', safety_device_ids)
    sys.stdout.flush()
    
    # Get device IDs from reminders
    reminder_device_ids = [d[0] for d in db.session.query(Reminder.patient_id.distinct()).all()]
    print('Device IDs in reminders:', reminder_device_ids)
    sys.stdout.flush()