"""
Check if D2000 and D3000 exist in the database
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.abspath('.'))

# Import app and models
from app import app, db
from models import HealthData, SafetyAlert, Reminder

def check_new_devices():
    """Check if D2000 and D3000 exist in the database"""
    with app.app_context():
        # Check for D2000 and D3000 in health data
        for device_id in ['D2000', 'D3000']:
            health = HealthData.query.filter_by(patient_id=device_id).first()
            safety = SafetyAlert.query.filter_by(patient_id=device_id).first()
            reminder = Reminder.query.filter_by(patient_id=device_id).first()
            
            logger.info(f"Device {device_id}")
            logger.info(f"  Health data: {'Found' if health else 'Not found'}")
            logger.info(f"  Safety data: {'Found' if safety else 'Not found'}")
            logger.info(f"  Reminder data: {'Found' if reminder else 'Not found'}")
            
            if health:
                logger.info(f"  Health details: Heart Rate: {health.heart_rate}, BP: {health.blood_pressure_systolic}/{health.blood_pressure_diastolic}")

if __name__ == "__main__":
    check_new_devices()