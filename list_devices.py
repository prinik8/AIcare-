"""
List device IDs in database
"""
from app import app, db
from models import HealthData

with app.app_context():
    devices = [h.patient_id for h in HealthData.query.all()]
    print('Available device IDs:', devices)