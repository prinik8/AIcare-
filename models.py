"""
AICare+ Database Models
Defines SQL Alchemy models for the AICare+ application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
# The db will be imported from app.py
from app import db

class Patient(db.Model):
    """Patient model for elderly individuals being monitored"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(200))
    medical_conditions = db.Column(db.Text)
    registered_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    health_data = db.relationship('HealthData', backref='patient', lazy=True)
    safety_alerts = db.relationship('SafetyAlert', backref='patient', lazy=True)
    reminders = db.relationship('Reminder', backref='patient', lazy=True)
    
    def __repr__(self):
        return f'<Patient {self.patient_id}: {self.name}>'


class Caregiver(db.Model):
    """Caregiver model for healthcare providers monitoring elderly individuals"""
    __tablename__ = 'caregivers'
    
    id = db.Column(db.Integer, primary_key=True)
    caregiver_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    patients = db.Column(db.Text)  # Comma-separated list of patient IDs
    registered_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Caregiver {self.caregiver_id}: {self.name}>'


class Event(db.Model):
    """Event model for system events and logs"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(10), default='info')
    
    def __repr__(self):
        return f'<Event {self.id}: {self.source} - {self.event_type}>'


class HealthData(db.Model):
    """Health data model for storing health metrics"""
    __tablename__ = 'health_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    patient_id = db.Column(db.String(20), db.ForeignKey('patients.patient_id'), nullable=False)
    heart_rate = db.Column(db.Integer)
    heart_rate_alert = db.Column(db.Boolean, default=False)
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    blood_pressure_alert = db.Column(db.Boolean, default=False)
    glucose_level = db.Column(db.Integer)
    glucose_level_alert = db.Column(db.Boolean, default=False)
    oxygen_saturation = db.Column(db.Integer)
    oxygen_saturation_alert = db.Column(db.Boolean, default=False)
    alert_triggered = db.Column(db.Boolean, default=False)
    caregiver_notified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<HealthData {self.id}: {self.patient_id} at {self.timestamp}>'


class SafetyAlert(db.Model):
    """Safety alert model for fall detection and unusual behavior"""
    __tablename__ = 'safety_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    patient_id = db.Column(db.String(20), db.ForeignKey('patients.patient_id'), nullable=False)
    movement_activity = db.Column(db.String(50))
    fall_detected = db.Column(db.Boolean, default=False)
    impact_force_level = db.Column(db.String(20))
    post_fall_inactivity = db.Column(db.Integer)  # in seconds
    location = db.Column(db.String(50))
    alert_triggered = db.Column(db.Boolean, default=False)
    caregiver_notified = db.Column(db.Boolean, default=False)
    severity = db.Column(db.String(20))
    resolved = db.Column(db.Boolean, default=False)
    resolved_timestamp = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<SafetyAlert {self.id}: {self.patient_id} at {self.timestamp}>'


class Reminder(db.Model):
    """Reminder model for medication, appointments, etc."""
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    patient_id = db.Column(db.String(20), db.ForeignKey('patients.patient_id'), nullable=False)
    reminder_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    recurrence = db.Column(db.String(50))
    priority = db.Column(db.String(20), default='medium')
    completed = db.Column(db.Boolean, default=False)
    completed_timestamp = db.Column(db.DateTime)
    reminder_sent = db.Column(db.Boolean, default=False)
    acknowledged = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Reminder {self.id}: {self.patient_id} - {self.reminder_type}>'