"""
Script to add sample data for devices D2000 and D3000
"""
from app import app, db
from models import HealthData, SafetyAlert, Reminder
from datetime import datetime, timedelta

def add_sample_data():
    """Add sample data for devices D2000 and D3000"""
    print("Adding sample data for devices D2000 and D3000")
    
    with app.app_context():
        # Check if data for these devices exists
        for device_id in ['D2000', 'D3000']:
            # Add sample health data for each device
            existing_health = HealthData.query.filter_by(patient_id=device_id).first()
            if not existing_health:
                print(f"Creating sample health data for device {device_id}")
                # Create a health record with realistic values
                health_data = HealthData(
                    patient_id=device_id,
                    timestamp=datetime.now() - timedelta(days=1),
                    heart_rate=75 if device_id == 'D2000' else 82,
                    heart_rate_alert=False,
                    blood_pressure_systolic=125 if device_id == 'D2000' else 145,
                    blood_pressure_diastolic=85 if device_id == 'D2000' else 90,
                    blood_pressure_alert=False if device_id == 'D2000' else True,
                    glucose_level=110 if device_id == 'D2000' else 130,
                    glucose_level_alert=False,
                    oxygen_saturation=97 if device_id == 'D2000' else 94,
                    oxygen_saturation_alert=False,
                    alert_triggered=False if device_id == 'D2000' else True,
                    caregiver_notified=False if device_id == 'D2000' else True
                )
                db.session.add(health_data)
            
            # Add sample safety data for each device
            existing_safety = SafetyAlert.query.filter_by(patient_id=device_id).first()
            if not existing_safety:
                print(f"Creating sample safety data for device {device_id}")
                # Create a safety record
                safety_data = SafetyAlert(
                    patient_id=device_id,
                    timestamp=datetime.now() - timedelta(days=2),
                    movement_activity='Normal' if device_id == 'D2000' else 'Abnormal',
                    fall_detected=False if device_id == 'D2000' else True,
                    impact_force_level='Low' if device_id == 'D2000' else 'Moderate',
                    post_fall_inactivity=0 if device_id == 'D2000' else 120,
                    location='Living Room',
                    alert_triggered=False if device_id == 'D2000' else True,
                    caregiver_notified=False if device_id == 'D2000' else True,
                    severity='Normal' if device_id == 'D2000' else 'Warning',
                    resolved=True if device_id == 'D2000' else False
                )
                db.session.add(safety_data)
            
            # Add sample reminder for each device
            existing_reminder = Reminder.query.filter_by(patient_id=device_id).first()
            if not existing_reminder:
                print(f"Creating sample reminder for device {device_id}")
                # Create a reminder
                reminder = Reminder(
                    patient_id=device_id,
                    reminder_type='medication' if device_id == 'D2000' else 'appointment',
                    description='Take blood pressure medication' if device_id == 'D2000' else 'Doctor appointment',
                    scheduled_time=datetime.now() + timedelta(hours=3),
                    recurrence='daily' if device_id == 'D2000' else 'weekly',
                    priority='high' if device_id == 'D2000' else 'medium',
                    completed=False,
                    reminder_sent=False,
                    acknowledged=False
                )
                db.session.add(reminder)
        
        db.session.commit()
        print("Sample data added successfully")

if __name__ == "__main__":
    add_sample_data()