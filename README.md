# Memoir - Note and Reminder Application

A modern PyQt5-based application for taking notes and managing reminders with MQTT monitoring capabilities.

## Features

### Core Features
- **Sticky Notes**: Take and save notes with auto-save functionality
- **Reminders**: Create and manage reminders with calendar selection
- **Modern UI**: Dark theme with purple accent colors and smooth animations

### New Features (v2.0)
- **Tab System**: Switch between Reminder and Monitoring sections
- **MQTT Monitoring**: Real-time monitoring of devices/sensors via MQTT
- **Status Indicators**: Visual status dots (red=error, blue=normal, gray=connecting)
- **Error Notifications**: System notifications for monitoring anomalies
- **Badge Alerts**: Tab badges showing error count

## Installation

### Prerequisites
- Python 3.6+
- PyQt5
- paho-mqtt (for MQTT functionality)

### Install Dependencies
```bash
# On Ubuntu/Debian
sudo apt install python3-pyqt5 python3-paho-mqtt

# Or using pip (in virtual environment)
pip install PyQt5 paho-mqtt
```

## Usage

### Running the Application
```bash
python3 script.py
```

### MQTT Monitoring Setup

1. **Start MQTT Broker**: Ensure an MQTT broker is running on localhost:1883
2. **Add Monitoring Items**: 
   - Click on the "MONITORING" tab
   - Click "+ Add Monitoring"
   - Enter a name and topic identifier
3. **Publish Data**: Send JSON messages to topics:
   - Normal status: `/monitoring/{topic}`
   - Error status: `/monitoring/{topic}/error`

### MQTT Message Format

#### Normal Status
```json
{
  "status": "normal",
  "timestamp": 1234567890,
  "value": 25.5
}
```

#### Error Status
```json
{
  "status": "error",
  "error_type": "temperature_high",
  "timestamp": 1234567890
}
```

### Testing MQTT Functionality
```bash
python3 test_mqtt.py
```

## File Structure

- `script.py` - Main application
- `test_mqtt.py` - MQTT testing script
- `sticky_note.json` - Saved notes
- `reminders.json` - Saved reminders
- `monitoring.json` - Monitoring configurations
- `app_settings.json` - Application settings

## Status Indicators

- **Gray Dot**: Connecting or not connected
- **Blue Dot**: Normal operation
- **Red Dot**: Error detected

## Notifications

When an error is detected:
1. Status dot turns red
2. Tab shows error count badge
3. System notification appears with error details
4. Message format: "Detected Anomalies on {name} error detail: {error_type}"

## Window Management

- **Drag**: Click and drag from the top area to move window
- **Resize**: Use the resize grip in the bottom-right corner
- **Minimize**: Click the minimize button (─)
- **Close**: Click the close button (✕)

## Customization

The application uses a purple theme (#8b1fb5) that can be customized by modifying the CSS styles in the code.