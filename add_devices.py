"""
Quick script to add device data for D2000 and D3000
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.abspath('.'))

# Import app and models
from app import app, db
from models import HealthData, SafetyAlert, Reminder

def add_device_data():
    """Add device data for D2000 and D3000"""
    with app.app_context():
        # Add device data for D2000 and D3000
        for device_id in ['D2000', 'D3000']:
            logger.info(f"Adding data for device {device_id}")
            
            # Create a health record
            health = HealthData(
                patient_id=device_id,
                timestamp=datetime.now() - timedelta(hours=2),
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
            db.session.add(health)
            
            # Create a safety record
            safety = SafetyAlert(
                patient_id=device_id,
                timestamp=datetime.now() - timedelta(hours=3),
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
            db.session.add(safety)
            
            # Create a reminder
            reminder = Reminder(
                patient_id=device_id,
                timestamp=datetime.now(),
                reminder_type='Medication' if device_id == 'D2000' else 'Appointment',
                description='Take blood pressure medication' if device_id == 'D2000' else 'Doctor appointment',
                scheduled_time=datetime.now() + timedelta(hours=3),
                recurrence='daily' if device_id == 'D2000' else 'weekly',
                priority='high' if device_id == 'D2000' else 'medium',
                completed=False,
                reminder_sent=False,
                acknowledged=False
            )
            db.session.add(reminder)
            
        # Commit changes
        db.session.commit()
        logger.info("Successfully added device data for D2000 and D3000")

if __name__ == "__main__":
    add_device_data()