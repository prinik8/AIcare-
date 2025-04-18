"""
Data Import Script for AICare+
Imports CSV data into SQLite database
"""
import os
import sys
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.path.abspath('.'))

# Import app and models
from app import app, db
from models import Patient, Caregiver, HealthData, SafetyAlert, Reminder

def validate_csv_row(row, required_fields=None):
    """
    Validate a CSV row to ensure it has all required fields and isn't a header row
    
    Args:
        row: CSV row dictionary
        required_fields: List of field names that must be present
        
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if required_fields is None:
        required_fields = ['Device-ID/User-ID', 'Timestamp']
    
    # Skip header row if it got included somehow
    if 'Device-ID/User-ID' in row and row['Device-ID/User-ID'] == 'Device-ID/User-ID':
        return False, "Skipping header row that wasn't properly excluded"
    
    # Verify all required fields exist
    for field in required_fields:
        if field not in row or not row[field]:
            return False, f"Missing required field: {field}"
    
    return True, ""

def parse_date(date_str):
    """Parse date string to datetime"""
    try:
        # Format from the CSV files: 1/22/2025 20:42
        return datetime.strptime(date_str, '%m/%d/%Y %H:%M')
    except ValueError:
        try:
            # Alternative format 
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try without seconds
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    # Try with day-first format
                    return datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                except ValueError:
                    logger.warning(f"Could not parse date: {date_str}, using current time")
                    return datetime.now()

def get_device_id(device_id):
    """
    Process the device ID from the CSV file
    
    Args:
        device_id: Device ID from CSV
    
    Returns:
        str: The processed device ID
    """
    # In the problem statement, we use data from wearable devices directly
    # No need to map to patient IDs - we're monitoring the devices themselves
    
    # Just use the device ID as is
    return device_id

def import_health_data(csv_path):
    """Import health monitoring data from CSV"""
    logger.info(f"Importing health data from {csv_path}")
    count = 0
    
    with open(csv_path, 'r') as csvfile:
        # Filter out empty fields from the headers
        headers = [header for header in next(csv.reader(csvfile)) if header.strip()]
        csvfile.seek(0)  # Go back to the beginning of the file
        reader = csv.DictReader(csvfile, fieldnames=headers)
        next(reader)  # Skip the header row
        
        for row in reader:
            try:
                # Get device ID from CSV and use it directly
                device_id = row['Device-ID/User-ID']
                timestamp = parse_date(row['Timestamp'])
                
                # Skip if we have data for this device ID at this timestamp
                existing = HealthData.query.filter_by(
                    patient_id=device_id, 
                    timestamp=timestamp
                ).first()
                
                if existing:
                    logger.info(f"Skipping duplicate record for device {device_id} at {timestamp}")
                    continue
                    
                logger.debug(f"Processing health record for device {device_id} at {timestamp}")
                
                # Parse blood pressure
                bp_parts = row.get('Blood Pressure', '0/0 mmHg').split('/')
                systolic = int(bp_parts[0].strip() if len(bp_parts) > 0 else 0)
                diastolic = int(bp_parts[1].split()[0].strip() if len(bp_parts) > 1 else 0)
                
                # Create new health data record
                health_data = HealthData(
                    patient_id=device_id,  # Use the device ID directly
                    timestamp=timestamp,
                    heart_rate=int(row.get('Heart Rate', 0)),
                    heart_rate_alert=row.get('Heart Rate Below/Above Threshold (Yes/No)', 'No') == 'Yes',
                    blood_pressure_systolic=systolic,
                    blood_pressure_diastolic=diastolic,
                    blood_pressure_alert=row.get('Blood Pressure Below/Above Threshold (Yes/No)', 'No') == 'Yes',
                    glucose_level=int(row.get('Glucose Levels', 0)),
                    glucose_level_alert=row.get('Glucose Levels Below/Above Threshold (Yes/No)', 'No') == 'Yes',
                    oxygen_saturation=int(row.get('Oxygen Saturation (SpO₂%)', 0)),
                    oxygen_saturation_alert=row.get('SpO₂ Below Threshold (Yes/No)', 'No') == 'Yes',
                    alert_triggered=row.get('Alert Triggered (Yes/No)', 'No') == 'Yes',
                    caregiver_notified=row.get('Caregiver Notified (Yes/No)', 'No') == 'Yes'
                )
                
                db.session.add(health_data)
                count += 1
                
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    db.session.commit()
                    logger.info(f"Imported {count} health records so far")
                
            except Exception as e:
                logger.error(f"Error importing row: {e}")
                db.session.rollback()
    
    # Final commit
    db.session.commit()
    logger.info(f"Imported {count} health records")
    return count

def import_safety_data(csv_path):
    """Import safety monitoring data from CSV"""
    logger.info(f"Importing safety data from {csv_path}")
    count = 0
    
    with open(csv_path, 'r') as csvfile:
        # Filter out empty fields from the headers
        headers = [header for header in next(csv.reader(csvfile)) if header.strip()]
        csvfile.seek(0)  # Go back to the beginning of the file
        reader = csv.DictReader(csvfile, fieldnames=headers)
        next(reader)  # Skip the header row
        
        for row in reader:
            try:
                # Get device ID from CSV and use it directly
                device_id = row['Device-ID/User-ID']
                timestamp = parse_date(row['Timestamp'])
                
                # Skip if we have data for this device at this timestamp
                existing = SafetyAlert.query.filter_by(
                    patient_id=device_id, 
                    timestamp=timestamp
                ).first()
                
                if existing:
                    continue
                
                # Get impact force level (handle empty values)
                impact_force = row.get('Impact Force Level', '-')
                if impact_force == '-':
                    impact_force = None
                
                # Parse post-fall inactivity duration
                try:
                    inactivity_duration = int(row.get('Post-Fall Inactivity Duration (Seconds)', '0'))
                except (ValueError, TypeError):
                    inactivity_duration = 0
                
                # Determine severity based on impact force
                severity = None
                if impact_force == 'High':
                    severity = 'critical'
                elif impact_force == 'Medium':
                    severity = 'warning'
                elif impact_force == 'Low':
                    severity = 'info'
                
                # Create new safety alert record
                safety_alert = SafetyAlert(
                    patient_id=device_id,  # Use the device ID directly
                    timestamp=timestamp,
                    movement_activity=row.get('Movement Activity', 'Unknown'),
                    fall_detected=row.get('Fall Detected (Yes/No)', 'No') == 'Yes',
                    impact_force_level=impact_force,
                    post_fall_inactivity=inactivity_duration,
                    location=row.get('Location', 'Unknown'),
                    alert_triggered=row.get('Alert Triggered (Yes/No)', 'No') == 'Yes',
                    caregiver_notified=row.get('Caregiver Notified (Yes/No)', 'No') == 'Yes',
                    severity=severity,
                    resolved=False
                )
                
                db.session.add(safety_alert)
                count += 1
                
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    db.session.commit()
                    logger.info(f"Imported {count} safety records so far")
                
            except Exception as e:
                logger.error(f"Error importing row: {e}")
                db.session.rollback()
    
    # Final commit
    db.session.commit()
    logger.info(f"Imported {count} safety records")
    return count

def import_reminder_data(csv_path):
    """Import reminder data from CSV"""
    logger.info(f"Importing reminder data from {csv_path}")
    count = 0
    
    with open(csv_path, 'r') as csvfile:
        # Filter out empty fields from the headers
        headers = [header for header in next(csv.reader(csvfile)) if header.strip()]
        csvfile.seek(0)  # Go back to the beginning of the file
        reader = csv.DictReader(csvfile, fieldnames=headers)
        next(reader)  # Skip the header row
        
        for row in reader:
            try:
                # Get device ID from CSV and use it directly
                device_id = row['Device-ID/User-ID']
                timestamp = parse_date(row['Timestamp'])
                scheduled_time = row['Scheduled Time']
                
                # Format the scheduled time properly
                date_part = timestamp.strftime('%Y-%m-%d')
                try:
                    # Try to parse with seconds
                    scheduled_datetime = datetime.strptime(f"{date_part} {scheduled_time}", '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # If that fails, try without seconds
                    scheduled_datetime = datetime.strptime(f"{date_part} {scheduled_time}", '%Y-%m-%d %H:%M')
                
                # Skip if we have a reminder for this device at this scheduled time
                existing = Reminder.query.filter_by(
                    patient_id=device_id, 
                    scheduled_time=scheduled_datetime,
                    reminder_type=row.get('Reminder Type', 'Unknown')
                ).first()
                
                if existing:
                    continue
                
                # Determine priority based on reminder type
                priority = 'medium'
                if row.get('Reminder Type') == 'Medication':
                    priority = 'high'
                elif row.get('Reminder Type') == 'Appointment':
                    priority = 'medium'
                else:
                    priority = 'low'
                
                # Create new reminder record
                reminder = Reminder(
                    patient_id=device_id,  # Use the device ID directly
                    timestamp=timestamp,
                    reminder_type=row.get('Reminder Type', 'Unknown'),
                    description=f"{row.get('Reminder Type', 'General')} reminder",
                    scheduled_time=scheduled_datetime,
                    recurrence=None,  # No recurrence data in the CSV
                    priority=priority,
                    completed=False,
                    reminder_sent=row.get('Reminder Sent (Yes/No)', 'No') == 'Yes',
                    acknowledged=row.get('Acknowledged (Yes/No)', 'No') == 'Yes'
                )
                
                db.session.add(reminder)
                count += 1
                
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    db.session.commit()
                    logger.info(f"Imported {count} reminder records so far")
                
            except Exception as e:
                logger.error(f"Error importing row: {e}")
                db.session.rollback()
    
    # Final commit
    db.session.commit()
    logger.info(f"Imported {count} reminder records")
    return count

def create_sample_patient_and_caregiver():
    """Create a sample patient and caregiver for development"""
    # Check if patient already exists
    patient = Patient.query.filter_by(patient_id='P001').first()
    if not patient:
        logger.info("Creating sample patient")
        patient = Patient(
            patient_id='P001',
            name='John Smith',
            age=78,
            gender='Male',
            address='123 Elder St, Caretown',
            phone='555-123-4567',
            emergency_contact='Mary Smith (Daughter): 555-987-6543',
            medical_conditions='Hypertension, Type 2 Diabetes, Mild Arthritis'
        )
        db.session.add(patient)
    
    # Check if caregiver already exists
    caregiver = Caregiver.query.filter_by(caregiver_id='C001').first()
    if not caregiver:
        logger.info("Creating sample caregiver")
        caregiver = Caregiver(
            caregiver_id='C001',
            name='Jane Morgan',
            role='Primary Nurse',
            phone='555-765-4321',
            email='jane.morgan@careservices.com',
            patients='P001,P002,P003'  # Update to include additional patients
        )
        db.session.add(caregiver)
    
    db.session.commit()
    
def create_additional_sample_patients():
    """Create additional sample devices for testing dropdown functionality"""
    # Check if data for these devices exists
    for device_id in ['D2000', 'D3000']:
        # Add sample health data for each device
        existing_health = HealthData.query.filter_by(patient_id=device_id).first()
        if not existing_health:
            logger.info(f"Creating sample health data for device {device_id}")
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
            logger.info(f"Creating sample safety data for device {device_id}")
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
            logger.info(f"Creating sample reminder for device {device_id}")
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

def detect_csv_type(csv_path):
    """
    Detect the type of CSV file based on column headers
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        str: 'health', 'safety', 'reminder', or 'unknown'
    """
    try:
        with open(csv_path, 'r') as csvfile:
            # Read the first row to get headers
            headers = next(csv.reader(csvfile))
            
            # Check for health data indicators
            if any(header in headers for header in ['Heart Rate', 'Blood Pressure', 'Glucose', 'SpO₂']):
                return 'health'
                
            # Check for safety data indicators
            elif any(header in headers for header in ['Fall Detected', 'Movement Activity', 'Impact Force']):
                return 'safety'
                
            # Check for reminder data indicators
            elif any(header in headers for header in ['Reminder Type', 'Scheduled Time']):
                return 'reminder'
                
            # Unknown CSV type
            else:
                return 'unknown'
    except Exception as e:
        logger.error(f"Error detecting CSV type: {e}")
        return 'unknown'

def secure_import_wrapper(import_func, csv_path):
    """A wrapper to add additional safeguards around CSV importing"""
    try:
        # Verify the file exists
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return 0
        
        # Check if the file is empty
        if os.path.getsize(csv_path) == 0:
            logger.error(f"CSV file is empty: {csv_path}")
            return 0
        
        # Detect CSV type
        csv_type = detect_csv_type(csv_path)
        
        # Verify we're using the right import function for this CSV type
        func_name = import_func.__name__
        if csv_type != 'unknown' and not func_name.endswith(f"{csv_type}_data"):
            logger.warning(f"Potential CSV type mismatch. Using {func_name} for a CSV detected as {csv_type}.")
        
        # Call the original import function
        return import_func(csv_path)
    except Exception as e:
        logger.error(f"Error in secure import wrapper: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 0

def main():
    """Main function to import all data"""
    with app.app_context():
        # Create a sample patient and caregiver
        create_sample_patient_and_caregiver()
        
        # Create additional sample patients for dropdown
        create_additional_sample_patients()
        
        # Import health data with additional safeguards
        health_count = secure_import_wrapper(import_health_data, 'attached_assets/health_monitoring.csv')
        
        # Import safety data with additional safeguards
        safety_count = secure_import_wrapper(import_safety_data, 'attached_assets/safety_monitoring.csv')
        
        # Import reminder data with additional safeguards
        reminder_count = secure_import_wrapper(import_reminder_data, 'attached_assets/daily_reminder.csv')
        
        logger.info(f"Import complete. Imported {health_count} health records, {safety_count} safety records, and {reminder_count} reminder records.")
        
        # Return counts for API endpoint
        return health_count, safety_count, reminder_count

if __name__ == "__main__":
    main()