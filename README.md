# AICare+

An advanced multi-agent AI system for elderly care support, providing intelligent health monitoring and personalized assistance through adaptive technologies.

## Features

- **Multi-agent AI Coordination**: Five specialized agents working together to provide comprehensive care
  - Health Monitoring Agent
  - Safety Monitoring Agent
  - Daily Reminder Agent
  - Communication Agent
  - Research Agent

- **Privacy-focused Interface**: Device-based identification system with anonymized data display

- **Real-time Health Monitoring**: Continuous tracking of vital signs with alert thresholds
  - Heart Rate
  - Blood Pressure
  - Glucose Levels
  - Oxygen Saturation

- **Safety Detection**: Fall detection and unusual behavior monitoring

- **Medication and Appointment Reminders**: Customizable reminder system

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite
- **AI Framework**: AutoGen multi-agent framework
- **LLM Integration**: Ollama (on-premise)
- **Data Visualization**: Chart.js
- **Embedding Model**: sentence-transformers

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- Ollama (for LLM functionality)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/prinik8/AIcare-.git
   cd AIcare-
   ```

2. Install the required dependencies
   ```
   pip install -r requirements.txt
   ```

3. Initialize the database
   ```
   python import_data.py
   ```

4. Add sample device data
   ```
   python add_devices.py
   ```

5. Run the application
   ```
   python main.py
   ```

6. Access the application at `http://localhost:5000`

## Project Structure

- **AICare+/**: Core module containing agent implementations
  - **agents/**: Specialized agent implementations
  - **tools/**: Custom tool implementations
  - **ui/**: Flask templates and static files
  - **db/**: Database management

- **Root Directory**:
  - **app.py**: Main Flask application
  - **models.py**: SQLAlchemy models
  - **import_data.py**: Data import utilities
  - **main.py**: Entry point

## License

This project is licensed under the MIT License - see the LICENSE file for details.