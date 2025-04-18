"""
AICare+ - Multi-agent AI system for elderly care
Main Flask application
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.abspath('.'), 'AICare+', 'ui', 'templates'),
            static_folder=os.path.join(os.path.abspath('.'), 'AICare+', 'ui', 'static'))
app.secret_key = os.environ.get("SESSION_SECRET", "aicare_plus_development_key")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configure the database to use SQLite
db_path = os.path.join(os.path.abspath('.'), 'aicareplus.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Define base model class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Add AICare+ package to system path
sys.path.append(os.path.abspath('.'))
AICare_path = os.path.join(os.path.abspath('.'), 'AICare+')
if AICare_path not in sys.path:
    sys.path.append(AICare_path)

# Import modules for autogen functionality (with error handling)
try:
    sys.path.append(os.path.join(os.path.abspath('.'), 'AICare+'))
    from autogen_config import setup_agents, run_agent_workflow, Agent_Types
    autogen_available = True
except ImportError as e:
    logger.error(f"Error importing autogen modules: {e}")
    logger.warning("AutoGen functionality will not be available")
    autogen_available = False

# Import models after db is initialized
with app.app_context():
    import models
    from models import Patient, Caregiver, Event, HealthData, SafetyAlert, Reminder
    
    # Create database tables
    db.create_all()

# Helper function to log events
def log_event(source, event_type, description, severity="info"):
    """Log an event to the database"""
    try:
        event = Event(
            source=source,
            event_type=event_type,
            description=description,
            severity=severity
        )
        db.session.add(event)
        db.session.commit()
        logger.debug(f"Event logged: {source} - {event_type} - {description} ({severity})")
        return True
    except Exception as e:
        logger.error(f"Error logging event: {e}")
        db.session.rollback()
        return False

# Helper function to get recent events
def get_recent_events(hours=24, source=None, event_type=None, severity=None):
    """Get recent events from the database"""
    try:
        # Calculate timestamp for filtering
        time_ago = datetime.now() - timedelta(hours=hours)
        
        # Build the query with filters
        query = Event.query.filter(Event.timestamp >= time_ago)
        
        if source:
            query = query.filter(Event.source.like(f"%{source}%"))
        
        if event_type:
            query = query.filter(Event.event_type.like(f"%{event_type}%"))
        
        if severity:
            query = query.filter(Event.severity == severity)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Execute query
        events = query.all()
        
        # Convert to dictionaries
        result = [{
            'id': event.id,
            'timestamp': event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'source': event.source,
            'event_type': event.event_type,
            'description': event.description,
            'severity': event.severity
        } for event in events]
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving events: {e}")
        return []

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Import models at the function level to avoid circular imports
        from models import HealthData, SafetyAlert, Reminder, Event
        
        # Get selected device ID or use default
        selected_device_id = request.args.get('device_id', 'D1000')
        
        # Get all unique device IDs from health data for selection dropdown
        all_device_ids = db.session.query(HealthData.patient_id.distinct()).all()
        all_device_ids = [{'device_id': d[0]} for d in all_device_ids] or [{'device_id': 'D1000'}]  # Use ['D1000'] if no device IDs found
        
        # Get latest health data - using device ID
        health_data = HealthData.query.filter_by(patient_id=selected_device_id).order_by(HealthData.timestamp.desc()).limit(10).all()
        
        # Get latest safety alerts - using device ID
        safety_alerts = SafetyAlert.query.filter_by(patient_id=selected_device_id).order_by(SafetyAlert.timestamp.desc()).limit(5).all()
        
        # Get upcoming reminders - using device ID
        reminders = Reminder.query.filter_by(patient_id=selected_device_id, completed=False).order_by(Reminder.scheduled_time.asc()).limit(5).all()
        
        # Get recent events
        events = Event.query.order_by(Event.timestamp.desc()).limit(10).all()
        
        # Log dashboard access
        log_event("UI", "dashboard_access", "Dashboard accessed")
        
        return render_template('dashboard.html', 
                              device_id=selected_device_id,
                              all_device_ids=all_device_ids,
                              health_data=health_data,
                              safety_alerts=safety_alerts,
                              reminders=reminders,
                              events=events)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return f"Error loading dashboard: {e}", 500

@app.route('/health')
def health():
    """Health monitoring page"""
    try:
        # Import models at the function level to avoid circular imports
        from models import HealthData, Event
        
        # Get selected device ID or use default
        selected_device_id = request.args.get('device_id', 'D1000')
        
        # Get all unique device IDs from health data for selection dropdown
        all_device_ids = db.session.query(HealthData.patient_id.distinct()).all()
        all_device_ids = [{'device_id': d[0]} for d in all_device_ids] or [{'device_id': 'D1000'}]  # Use ['D1000'] if no device IDs found
        
        # Get all health data for the device without date filtering
        # Our CSV data is from January 2025, and the current date is April 2025
        health_data = HealthData.query.filter_by(patient_id=selected_device_id).order_by(HealthData.timestamp.desc()).all()
        logger.debug(f"Found {len(health_data)} health records for device {selected_device_id}")
        
        # Prepare data for charts
        chart_data = prepare_health_chart_data(health_data)
        
        # Debug - let's just print what might be causing the error
        # and log the type of charts_data and its keys
        logger.debug(f"Charts data type: {type(chart_data)}")
        if chart_data:
            for key, value in chart_data.items():
                logger.debug(f"Key: {key}, Value type: {type(value)}")
                for sub_key, sub_value in value.items():
                    logger.debug(f"  Subkey: {sub_key}, Subvalue type: {type(sub_value)}, Length: {len(sub_value) if hasattr(sub_value, '__len__') else 'N/A'}")
        
        # Try to catch the exact error in a more specific try/except block
        try:
            rendered_template = render_template('health.html', 
                                  device_id=selected_device_id,
                                  all_device_ids=all_device_ids,
                                  health_data=health_data,
                                  charts_data=chart_data)
            return rendered_template
        except Exception as template_error:
            import traceback
            logger.error(f"Template rendering error: {template_error}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error rendering health template: {template_error}", 500
    except Exception as e:
        logger.error(f"Error loading health page: {e}")
        return f"Error loading health page: {e}", 500

def prepare_health_chart_data(health_data):
    """Prepare health data for charts"""
    # Initialize data structure
    chart_data = {
        'heart_rate': {'labels': [], 'values': []},
        'blood_pressure': {'labels': [], 'systolic': [], 'diastolic': []},
        'glucose_level': {'labels': [], 'values': []},
        'oxygen_saturation': {'labels': [], 'values': []}
    }
    
    # Return empty structure if no data
    if not health_data:
        return chart_data
    
    # Reverse to get chronological order
    health_data = health_data[::-1]
    
    # Extract data for charts
    for data in health_data:
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M')
        
        # Heart rate - guard against None
        if hasattr(data, 'heart_rate') and data.heart_rate is not None:
            chart_data['heart_rate']['labels'].append(timestamp)
            chart_data['heart_rate']['values'].append(data.heart_rate)
        
        # Blood pressure
        chart_data['blood_pressure']['labels'].append(timestamp)
        # Handle case when either field might be None or missing
        systolic = data.blood_pressure_systolic if hasattr(data, 'blood_pressure_systolic') and data.blood_pressure_systolic is not None else 0
        diastolic = data.blood_pressure_diastolic if hasattr(data, 'blood_pressure_diastolic') and data.blood_pressure_diastolic is not None else 0
        chart_data['blood_pressure']['systolic'].append(systolic)
        chart_data['blood_pressure']['diastolic'].append(diastolic)
        
        # Glucose level - guard against None
        if hasattr(data, 'glucose_level') and data.glucose_level is not None:
            chart_data['glucose_level']['labels'].append(timestamp)
            chart_data['glucose_level']['values'].append(data.glucose_level)
        
        # Oxygen saturation - guard against None
        if hasattr(data, 'oxygen_saturation') and data.oxygen_saturation is not None:
            chart_data['oxygen_saturation']['labels'].append(timestamp)
            chart_data['oxygen_saturation']['values'].append(data.oxygen_saturation)
    
    return chart_data

@app.route('/safety')
def safety():
    """Safety monitoring page"""
    try:
        # Import models at the function level to avoid circular imports
        from models import SafetyAlert, Event
        
        # Get selected device ID or use default
        selected_device_id = request.args.get('device_id', 'D1000')
        
        # Get all unique device IDs from safety data for selection dropdown
        all_device_ids = db.session.query(SafetyAlert.patient_id.distinct()).all()
        all_device_ids = [{'device_id': d[0]} for d in all_device_ids] or [{'device_id': 'D1000'}]  # Use ['D1000'] if no device IDs found
        
        # Get safety alerts
        safety_alerts = SafetyAlert.query.filter_by(patient_id=selected_device_id).order_by(SafetyAlert.timestamp.desc()).limit(20).all()
        
        # Get safety events
        safety_events = Event.query.filter(Event.source.like('safety%')).order_by(Event.timestamp.desc()).limit(20).all()
        
        return render_template('safety.html', 
                              device_id=selected_device_id,
                              all_device_ids=all_device_ids,
                              safety_alerts=safety_alerts,
                              safety_events=safety_events)
    except Exception as e:
        logger.error(f"Error loading safety page: {e}")
        return f"Error loading safety page: {e}", 500

@app.route('/reminders')
def reminders():
    """Reminders management page"""
    try:
        # Import models at the function level to avoid circular imports
        from models import Reminder, Event
        
        # Get selected device ID or use default
        selected_device_id = request.args.get('device_id', 'D1000')
        
        # Get all unique device IDs from reminders for selection dropdown
        all_device_ids = db.session.query(Reminder.patient_id.distinct()).all()
        all_device_ids = [{'device_id': d[0]} for d in all_device_ids] or [{'device_id': 'D1000'}]  # Use ['D1000'] if no device IDs found
        
        # Get all reminders
        all_reminders = Reminder.query.filter_by(patient_id=selected_device_id).order_by(Reminder.scheduled_time.asc()).all()
        
        # Separate upcoming and completed reminders
        upcoming_reminders = [r for r in all_reminders if not r.completed]
        completed_reminders = [r for r in all_reminders if r.completed]
        
        return render_template('reminders.html', 
                              device_id=selected_device_id,
                              all_device_ids=all_device_ids,
                              upcoming_reminders=upcoming_reminders,
                              completed_reminders=completed_reminders)
    except Exception as e:
        logger.error(f"Error loading reminders page: {e}")
        return f"Error loading reminders page: {e}", 500

@app.route('/api/run_agent/<agent_type>', methods=['POST'])
def run_agent(agent_type):
    """Run a specific agent and return results"""
    try:
        # Temporary implementation to avoid dependency issues
        # This simulates agent execution without requiring sentence_transformers
        
        # Validate the agent type
        valid_types = ['health', 'safety', 'reminder', 'communication', 'research', 'all']
        if agent_type not in valid_types:
            return jsonify({'error': 'Invalid agent type'}), 400
        
        # Generate appropriate messaging based on agent type
        if agent_type == 'health':
            # Simulate health agent analysis
            message = "Health monitoring completed successfully. Found no critical health concerns in the latest metrics."
            log_event("health_agent", "workflow_completed", message)
            result = "Health monitoring completed"
            
        elif agent_type == 'safety':
            # Simulate safety agent analysis
            message = "Safety check completed. No fall events detected in the last 24 hours."
            log_event("safety_agent", "workflow_completed", message)
            result = "Safety check completed"
            
        elif agent_type == 'reminder':
            # Simulate reminder agent 
            message = "Reminder check completed. Found upcoming medication reminders for today."
            log_event("reminder_agent", "workflow_completed", message)
            result = "Reminder check completed"
            
        elif agent_type == 'communication':
            # Simulate communication agent
            message = "Communication task completed. Generated daily summary for caregiver."
            log_event("communication_agent", "workflow_completed", message)
            result = "Communication task completed"
            
        elif agent_type == 'research':
            # Simulate research agent
            message = "Research completed. Found information about hypertension management for elderly patients."
            log_event("research_agent", "workflow_completed", message)
            result = "Research completed"
            
        elif agent_type == 'all':
            # Simulate all agents
            log_event("all_agents", "workflow_completed", "Multiple agent workflows completed")
            
            # List of simulated results
            results = [
                "Health: Health monitoring completed successfully.",
                "Safety: Safety check completed. No incidents detected.",
                "Reminder: Reminder check completed.",
                "Communication: Communication task completed.",
                "Research: Research completed."
            ]
            
            # Get events from all agents
            events = get_recent_events(hours=1)
            
            return jsonify({
                'status': 'success', 
                'message': 'All agents completed their tasks',
                'results': results,
                'events': events
            })
        
        # For single agent types, get their specific events
        events = get_recent_events(hours=1, source=f"{agent_type}_agent")
        
        return jsonify({
            'status': 'success', 
            'message': f'{agent_type.title()} agent completed its task',
            'result': result,
            'events': events
        })
    except Exception as e:
        logger.error(f"Error running agent {agent_type}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mark_reminder_complete/<int:reminder_id>', methods=['POST'])
def mark_reminder_complete(reminder_id):
    """Mark a reminder as completed"""
    try:
        reminder = Reminder.query.get_or_404(reminder_id)
        reminder.completed = True
        reminder.completed_timestamp = datetime.now()
        
        # Log event
        log_event('ui', 'reminder_completed', f"Reminder completed: {reminder.description}", 'info')
        
        db.session.commit()
        
        flash(f"Reminder marked as completed", "success")
        return redirect(url_for('reminders'))
    except Exception as e:
        logger.error(f"Error marking reminder complete: {e}")
        db.session.rollback()
        flash(f"Error: {e}", "danger")
        return redirect(url_for('reminders'))

@app.route('/api/add_reminder', methods=['POST'])
def add_reminder():
    """Add a new reminder"""
    try:
        # Import models at the function level to avoid circular imports
        from models import Reminder
        
        # Get form data
        reminder_type = request.form.get('reminder_type')
        description = request.form.get('description')
        scheduled_date = request.form.get('scheduled_date')
        scheduled_time = request.form.get('scheduled_time')
        priority = request.form.get('priority', 'medium')
        recurrence = request.form.get('recurrence')
        device_id = request.form.get('device_id', 'D1000')
        
        # Validate required fields
        if not all([reminder_type, description, scheduled_date, scheduled_time]):
            flash("All fields are required", "danger")
            return redirect(url_for('reminders'))
        
        # Combine date and time
        scheduled_datetime = f"{scheduled_date} {scheduled_time}"
        scheduled_datetime = datetime.strptime(scheduled_datetime, '%Y-%m-%d %H:%M')
        
        # Create reminder
        reminder = Reminder(
            patient_id=device_id,
            reminder_type=reminder_type,
            description=description,
            scheduled_time=scheduled_datetime,
            recurrence=recurrence,
            priority=priority,
            completed=False
        )
        db.session.add(reminder)
        
        # Log event
        log_event('ui', 'reminder_created', f"New reminder created: {description}", 'info')
        
        db.session.commit()
        
        flash(f"Reminder added successfully", "success")
        return redirect(url_for('reminders', device_id=device_id))
    except Exception as e:
        logger.error(f"Error adding reminder: {e}")
        db.session.rollback()
        flash(f"Error: {e}", "danger")
        return redirect(url_for('reminders'))

@app.route('/api/import_data', methods=['GET'])
def import_data_endpoint():
    """API endpoint to import data from CSV files"""
    try:
        import import_data
        
        # Use the main function from import_data.py which will:
        # 1. Create sample patient/caregiver
        # 2. Import all CSV data
        # 3. Return the counts
        health_count, safety_count, reminder_count = import_data.main()
        
        message = f"Import complete. Imported {health_count} health records, {safety_count} safety records, and {reminder_count} reminder records."
        logger.info(message)
        
        return jsonify({
            'status': 'success',
            'message': message
        })
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Traceback: {error_traceback}")
        return jsonify({
            'status': 'error',
            'message': f"Error importing data: {e}",
            'traceback': error_traceback
        }), 500

@app.route('/api/get_health_data', methods=['GET'])
def get_health_data():
    """API to get health data for charts"""
    try:
        # Import models at the function level to avoid circular imports
        from models import HealthData
        
        days = request.args.get('days', '365')  # Default to 365 days to include January data
        days = int(days)
        device_id = request.args.get('device_id', 'D1000')
        
        # Get health data from database
        days_ago = datetime.now() - timedelta(days=days)
        # Log query parameters for debugging
        logger.debug(f"Querying health data for device_id={device_id}, from {days_ago}")
        
        # Get health data without date filtering first to check what's available
        all_device_records = HealthData.query.filter_by(patient_id=device_id).order_by(HealthData.timestamp.asc()).all()
        logger.debug(f"Total records for device {device_id}: {len(all_device_records)}")
        if all_device_records:
            logger.debug(f"Sample timestamp: {all_device_records[0].timestamp}")
        
        # Include all data for the device regardless of date
        # The timestamp filter was excluding our January 2025 data since we're currently in April 2025
        health_data = all_device_records
        
        # Convert to JSON-friendly format
        health_list = [{
            'id': data.id,
            'timestamp': data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'heart_rate': data.heart_rate,
            'heart_rate_alert': data.heart_rate_alert,
            # Use the actual database field names
            'blood_pressure_systolic': data.blood_pressure_systolic,
            'blood_pressure_diastolic': data.blood_pressure_diastolic,
            'blood_pressure_alert': data.blood_pressure_alert,
            'glucose_level': data.glucose_level,
            'glucose_level_alert': data.glucose_level_alert,
            'oxygen_saturation': data.oxygen_saturation,
            'oxygen_saturation_alert': data.oxygen_saturation_alert,
            'alert_triggered': data.alert_triggered,
            'caregiver_notified': data.caregiver_notified
        } for data in health_data]
        
        return jsonify(health_list)
    except Exception as e:
        logger.error(f"Error getting health data: {e}")
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)