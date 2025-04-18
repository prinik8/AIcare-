"""
Check device data in database
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.abspath('.'))

# Import app and models
from app import app, db
from models import HealthData, SafetyAlert, Reminder

def check_device_data():
    """Check device data in database"""
    with app.app_context():
        # Get health data for each device
        health_data = HealthData.query.all()
        logger.info(f"Total health records: {len(health_data)}")
        
        # Get unique device IDs
        device_ids = set(h.patient_id for h in health_data)
        logger.info(f"Unique device IDs: {device_ids}")
        
        # Display some health data for each device
        for device_id in device_ids:
            device_health = HealthData.query.filter_by(patient_id=device_id).first()
            if device_health:
                logger.info(f"Device {device_id} - Heart Rate: {device_health.heart_rate}, "
                           f"BP: {device_health.blood_pressure_systolic}/{device_health.blood_pressure_diastolic}, "
                           f"Glucose: {device_health.glucose_level}, "
                           f"O2: {device_health.oxygen_saturation}")
        
        # Check safety alerts
        safety_alerts = SafetyAlert.query.all()
        logger.info(f"Total safety alerts: {len(safety_alerts)}")
        
        # Check reminders
        reminders = Reminder.query.all()
        logger.info(f"Total reminders: {len(reminders)}")

if __name__ == "__main__":
    check_device_data()