"""
AICare+ - Multi-agent AI system for elderly care
Main entry point for web application
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.append(os.path.abspath('.'))

# Import our Flask app from app.py
from app import app

# Debug template paths
logger.debug(f"Template folder: {app.template_folder}")
logger.debug(f"Template files: {os.listdir(app.template_folder)}")

# Run the app when using gunicorn
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)