# Sticky Notes Application with Monitoring

A modern sticky notes application with reminder functionality and MQTT monitoring capabilities.

## Features

- **Note Taking**: Rich text area for taking notes
- **Reminders**: Add and manage reminders with dates
- **Monitoring**: Real-time MQTT monitoring with status indicators
- **Notifications**: Alert system for monitoring anomalies
- **Purple Theme**: Consistent purple color scheme throughout

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

## MQTT Monitoring

The monitoring feature connects to a local MQTT broker and subscribes to topics in the format:
- `/monitoring/{topic}` - Main monitoring data
- `/monitoring/{topic}/error` - Error notifications

### Adding Monitoring Nodes

1. Switch to the "MONITORING" tab
2. Click "Add Monitoring"
3. Enter a name and topic identifier
4. The system will automatically connect and monitor the specified topic

### Status Indicators

- 🔴 **Red**: Error state
- 🔵 **Blue**: Normal operation
- ⚪ **Gray**: Connecting or disconnected

### Error Notifications

When an error is detected, the system will:
- Show a notification badge on the monitoring tab
- Display a popup alert with error details
- Update the status indicator to red

## MQTT Message Format

### Normal Status
```json
{
  "status": "normal",
  "data": "any data"
}
```

### Error Status
```json
{
  "status": "error",
  "error_type": "connection_lost"
}
```

## Development

The application is built with:
- React 18
- TypeScript
- Tailwind CSS
- MQTT.js for real-time monitoring
- Lucide React for icons

## License

MIT License