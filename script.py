import sys
import os
import json
import threading
import time
from datetime import date
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QPoint, QDate, QSettings, QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QFrame, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QDialog, QCalendarWidget,
    QLineEdit, QSizeGrip, QGraphicsDropShadowEffect, QDateEdit,
    QTabWidget, QSystemTrayIcon, QMessageBox, QMenu, QAction,
    QDialogButtonBox, QFormLayout, QComboBox, QSpinBox, QCheckBox,
    QColorDialog, QGroupBox, QScrollArea
)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("Warning: paho-mqtt not available. MQTT functionality will be disabled.")

NOTE_FILE = 'sticky_note.json'
REM_FILE  = 'reminders.json'
SETTINGS_FILE = 'app_settings.json'
MONITORING_FILE = 'monitoring.json'
MONITORING_SETTINGS_FILE = 'monitoring_settings.json'

class MQTTSignal(QObject):
    """Signal class for MQTT communication with GUI thread."""
    data_received = pyqtSignal(str, str)  # topic, message
    status_changed = pyqtSignal(str, str)  # topic, status
    error_received = pyqtSignal(str, str, str)  # topic, error_type, message

def load_note():
    """Load note content from file with proper error handling."""
    if not os.path.exists(NOTE_FILE):
        return ""
    try:
        with open(NOTE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, str) else ""
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading note: {e}")
        return ""

def save_note(text):
    """Save note content to file with proper error handling."""
    try:
        with open(NOTE_FILE, 'w', encoding='utf-8') as f:
            json.dump(text, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving note: {e}")

def load_rems():
    """Load reminders from file with proper error handling."""
    if not os.path.exists(REM_FILE):
        return []
    try:
        with open(REM_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading reminders: {e}")
        return []

def save_rems(lst):
    """Save reminders to file with proper error handling."""
    try:
        with open(REM_FILE, 'w', encoding='utf-8') as f:
            json.dump(lst, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving reminders: {e}")

def load_settings():
    """Load application settings including window state."""
    if not os.path.exists(SETTINGS_FILE):
        return {
            'window': {'x': 100, 'y': 100, 'width': 700, 'height': 450},
            'splitter': [350, 350],
            'notifications_enabled': True
        }
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Ensure notifications_enabled exists
        if 'notifications_enabled' not in data:
            data['notifications_enabled'] = True
        return data
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading settings: {e}")
        return {
            'window': {'x': 100, 'y': 100, 'width': 700, 'height': 450},
            'splitter': [350, 350],
            'notifications_enabled': True
        }

def save_settings(settings):
    """Save application settings including window state."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving settings: {e}")

def load_monitoring():
    """Load monitoring configurations from file with proper error handling."""
    if not os.path.exists(MONITORING_FILE):
        return []
    try:
        with open(MONITORING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading monitoring: {e}")
        return []

def save_monitoring(lst):
    """Save monitoring configurations to file with proper error handling."""
    try:
        with open(MONITORING_FILE, 'w', encoding='utf-8') as f:
            json.dump(lst, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving monitoring: {e}")

def load_monitoring_settings():
    """Load monitoring settings from file with proper error handling."""
    if not os.path.exists(MONITORING_SETTINGS_FILE):
        return {
            'status_colors': {
                'normal': '#10B981',      # Green
                'warning': '#F59E0B',     # Amber
                'error': '#EF4444',       # Red
                'unknown': '#6B7280'      # Gray
            },
            'triggers': {
                'enable_alerts': True,
                'alert_threshold': 3,     # Number of consecutive errors before alert
                'cooldown_period': 300,   # Seconds between alerts for same node
                'enable_sound': False,
                'enable_notification': True
            },
            'mqtt': {
                'broker_host': '10.11.0.34',
                'broker_port': 1883,
                'username': '',
                'password': '',
                'keepalive': 60,
                'enable_ssl': False,
                'enable_auth': False
            },
            'appearance': {
                'status_dot_size': 12,
                'show_timestamps': True,
                'auto_refresh_interval': 5  # Seconds
            }
        }
    try:
        with open(MONITORING_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Ensure all required keys exist with defaults
        default_settings = load_monitoring_settings()
        for key, value in default_settings.items():
            if key not in data:
                data[key] = value
        return data
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading monitoring settings: {e}")
        return load_monitoring_settings()

def save_monitoring_settings(settings):
    """Save monitoring settings to file with proper error handling."""
    try:
        with open(MONITORING_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving monitoring settings: {e}")


class MonitoringSettingsDialog(QDialog):
    """Dialog for configuring monitoring settings."""
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.current_settings = current_settings or load_monitoring_settings()
        self.setWindowTitle("Monitoring Settings")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background: #1f2937;
                color: #f9fafb;
            }
            QTabWidget::pane {
                border: 1px solid #374151;
                background: #1f2937;
            }
            QTabBar::tab {
                background: #374151;
                color: #d1d5db;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #6b46c1;
                color: white;
            }
            QTabBar::tab:hover {
                background: #4b5563;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #374151;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background: #374151;
                color: #f9fafb;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #8b5cf6;
            }
            QCheckBox {
                color: #f9fafb;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4b5563;
                background: #374151;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #8b5cf6;
                background: #8b5cf6;
                border-radius: 3px;
            }
            QPushButton {
                background: #6b46c1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
            QPushButton:pressed {
                background: #5b21b6;
            }
            QDialogButtonBox QPushButton {
                background: #374151;
                color: #f9fafb;
                border: 1px solid #4b5563;
            }
            QDialogButtonBox QPushButton:hover {
                background: #4b5563;
            }
        """)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Status Colors Tab
        status_tab = self.create_status_colors_tab()
        tab_widget.addTab(status_tab, "Status Colors")
        
        # Triggers Tab
        triggers_tab = self.create_triggers_tab()
        tab_widget.addTab(triggers_tab, "Triggers")
        
        # MQTT Tab
        mqtt_tab = self.create_mqtt_tab()
        tab_widget.addTab(mqtt_tab, "MQTT")
        
        # Appearance Tab
        appearance_tab = self.create_appearance_tab()
        tab_widget.addTab(appearance_tab, "Appearance")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_status_colors_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Status Colors Group
        colors_group = QGroupBox("Status Dot Colors")
        colors_layout = QFormLayout(colors_group)
        
        # Normal status color
        self.normal_color_btn = QPushButton("Choose Color")
        self.normal_color_btn.clicked.connect(lambda: self.choose_color('normal'))
        colors_layout.addRow("Normal:", self.normal_color_btn)
        
        # Warning status color
        self.warning_color_btn = QPushButton("Choose Color")
        self.warning_color_btn.clicked.connect(lambda: self.choose_color('warning'))
        colors_layout.addRow("Warning:", self.warning_color_btn)
        
        # Error status color
        self.error_color_btn = QPushButton("Choose Color")
        self.error_color_btn.clicked.connect(lambda: self.choose_color('error'))
        colors_layout.addRow("Error:", self.error_color_btn)
        
        # Unknown status color
        self.unknown_color_btn = QPushButton("Choose Color")
        self.unknown_color_btn.clicked.connect(lambda: self.choose_color('unknown'))
        colors_layout.addRow("Unknown:", self.unknown_color_btn)
        
        layout.addWidget(colors_group)
        layout.addStretch()
        
        return tab
    
    def create_triggers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Alert Settings Group
        alerts_group = QGroupBox("Alert Settings")
        alerts_layout = QFormLayout(alerts_group)
        
        self.enable_alerts_cb = QCheckBox()
        alerts_layout.addRow("Enable Alerts:", self.enable_alerts_cb)
        
        self.alert_threshold_spin = QSpinBox()
        self.alert_threshold_spin.setRange(1, 10)
        self.alert_threshold_spin.setSuffix(" consecutive errors")
        alerts_layout.addRow("Alert Threshold:", self.alert_threshold_spin)
        
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(60, 3600)
        self.cooldown_spin.setSuffix(" seconds")
        alerts_layout.addRow("Cooldown Period:", self.cooldown_spin)
        
        self.enable_sound_cb = QCheckBox()
        alerts_layout.addRow("Enable Sound:", self.enable_sound_cb)
        
        self.enable_notification_cb = QCheckBox()
        alerts_layout.addRow("Enable Notifications:", self.enable_notification_cb)
        
        layout.addWidget(alerts_group)
        layout.addStretch()
        
        return tab
    
    def create_mqtt_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # MQTT Connection Group
        mqtt_group = QGroupBox("MQTT Connection")
        mqtt_layout = QFormLayout(mqtt_group)
        
        self.mqtt_host_edit = QLineEdit()
        mqtt_layout.addRow("Broker Host:", self.mqtt_host_edit)
        
        self.mqtt_port_spin = QSpinBox()
        self.mqtt_port_spin.setRange(1, 65535)
        mqtt_layout.addRow("Port:", self.mqtt_port_spin)
        
        self.mqtt_keepalive_spin = QSpinBox()
        self.mqtt_keepalive_spin.setRange(10, 300)
        self.mqtt_keepalive_spin.setSuffix(" seconds")
        mqtt_layout.addRow("Keep Alive:", self.mqtt_keepalive_spin)
        
        self.enable_ssl_cb = QCheckBox()
        mqtt_layout.addRow("Enable SSL:", self.enable_ssl_cb)
        
        # Authentication Group
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout(auth_group)
        
        self.enable_auth_cb = QCheckBox()
        auth_layout.addRow("Enable Authentication:", self.enable_auth_cb)
        
        self.mqtt_username_edit = QLineEdit()
        self.mqtt_username_edit.setEnabled(False)
        auth_layout.addRow("Username:", self.mqtt_username_edit)
        
        self.mqtt_password_edit = QLineEdit()
        self.mqtt_password_edit.setEchoMode(QLineEdit.Password)
        self.mqtt_password_edit.setEnabled(False)
        auth_layout.addRow("Password:", self.mqtt_password_edit)
        
        # Connect auth checkbox to enable/disable fields
        self.enable_auth_cb.toggled.connect(self.toggle_auth_fields)
        
        layout.addWidget(mqtt_group)
        layout.addWidget(auth_group)
        layout.addStretch()
        
        return tab
    
    def create_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance Settings Group
        appearance_group = QGroupBox("Appearance Settings")
        appearance_layout = QFormLayout(appearance_group)
        
        self.status_dot_size_spin = QSpinBox()
        self.status_dot_size_spin.setRange(8, 24)
        self.status_dot_size_spin.setSuffix(" px")
        appearance_layout.addRow("Status Dot Size:", self.status_dot_size_spin)
        
        self.show_timestamps_cb = QCheckBox()
        appearance_layout.addRow("Show Timestamps:", self.show_timestamps_cb)
        
        self.auto_refresh_spin = QSpinBox()
        self.auto_refresh_spin.setRange(1, 60)
        self.auto_refresh_spin.setSuffix(" seconds")
        appearance_layout.addRow("Auto Refresh Interval:", self.auto_refresh_spin)
        
        layout.addWidget(appearance_group)
        layout.addStretch()
        
        return tab
    
    def choose_color(self, status_type):
        """Open color dialog for choosing status color."""
        current_color = QColor(self.current_settings['status_colors'][status_type])
        color = QColorDialog.getColor(current_color, self, f"Choose {status_type.title()} Color")
        if color.isValid():
            self.current_settings['status_colors'][status_type] = color.name()
            # Update button text to show current color
            button = getattr(self, f"{status_type}_color_btn")
            button.setText(f"Color: {color.name()}")
            button.setStyleSheet(f"QPushButton {{ background: {color.name()}; color: white; }}")
    
    def toggle_auth_fields(self, enabled):
        """Enable/disable authentication fields based on checkbox."""
        self.mqtt_username_edit.setEnabled(enabled)
        self.mqtt_password_edit.setEnabled(enabled)
    
    def load_settings(self):
        """Load current settings into the dialog."""
        settings = self.current_settings
        
        # Status colors
        for status_type in ['normal', 'warning', 'error', 'unknown']:
            color = settings['status_colors'][status_type]
            button = getattr(self, f"{status_type}_color_btn")
            button.setText(f"Color: {color}")
            button.setStyleSheet(f"QPushButton {{ background: {color}; color: white; }}")
        
        # Triggers
        self.enable_alerts_cb.setChecked(settings['triggers']['enable_alerts'])
        self.alert_threshold_spin.setValue(settings['triggers']['alert_threshold'])
        self.cooldown_spin.setValue(settings['triggers']['cooldown_period'])
        self.enable_sound_cb.setChecked(settings['triggers']['enable_sound'])
        self.enable_notification_cb.setChecked(settings['triggers']['enable_notification'])
        
        # MQTT
        self.mqtt_host_edit.setText(settings['mqtt']['broker_host'])
        self.mqtt_port_spin.setValue(settings['mqtt']['broker_port'])
        self.mqtt_keepalive_spin.setValue(settings['mqtt']['keepalive'])
        self.enable_ssl_cb.setChecked(settings['mqtt']['enable_ssl'])
        self.enable_auth_cb.setChecked(settings['mqtt']['enable_auth'])
        self.mqtt_username_edit.setText(settings['mqtt']['username'])
        self.mqtt_password_edit.setText(settings['mqtt']['password'])
        
        # Appearance
        self.status_dot_size_spin.setValue(settings['appearance']['status_dot_size'])
        self.show_timestamps_cb.setChecked(settings['appearance']['show_timestamps'])
        self.auto_refresh_spin.setValue(settings['appearance']['auto_refresh_interval'])
        
        # Enable/disable auth fields based on current setting
        self.toggle_auth_fields(settings['mqtt']['enable_auth'])
    
    def get_settings(self):
        """Get the current settings from the dialog."""
        return {
            'status_colors': self.current_settings['status_colors'],
            'triggers': {
                'enable_alerts': self.enable_alerts_cb.isChecked(),
                'alert_threshold': self.alert_threshold_spin.value(),
                'cooldown_period': self.cooldown_spin.value(),
                'enable_sound': self.enable_sound_cb.isChecked(),
                'enable_notification': self.enable_notification_cb.isChecked()
            },
            'mqtt': {
                'broker_host': self.mqtt_host_edit.text(),
                'broker_port': self.mqtt_port_spin.value(),
                'username': self.mqtt_username_edit.text(),
                'password': self.mqtt_password_edit.text(),
                'keepalive': self.mqtt_keepalive_spin.value(),
                'enable_ssl': self.enable_ssl_cb.isChecked(),
                'enable_auth': self.enable_auth_cb.isChecked()
            },
            'appearance': {
                'status_dot_size': self.status_dot_size_spin.value(),
                'show_timestamps': self.show_timestamps_cb.isChecked(),
                'auto_refresh_interval': self.auto_refresh_spin.value()
            }
        }


class NoteReminderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memoir")
        self.setWindowIcon(QIcon("./Kazimierz.png"))
        self._offset = None
        self._resizing = False
        
        # Enable window features
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set minimum and maximum size constraints
        self.setMinimumSize(500, 300)
        self.setMaximumSize(1400, 900)
        
        # Load settings and restore window state
        self.settings = load_settings()
        self.monitoring_settings = load_monitoring_settings()
        self.restore_window_state()
        
        # Initialize MQTT
        self.mqtt_signal = MQTTSignal()
        self.mqtt_client = None
        self.monitoring_status = {}  # Store status for each monitoring node
        self.notification_count = 0
        self.error_counts = {}  # Track consecutive errors for each node
        self.last_alert_time = {}  # Track last alert time for cooldown
        
        # Initialize system tray for notifications
        self.init_system_tray()
        
        self.init_ui()

    def init_system_tray(self):
        """Initialize system tray for notifications with enhanced functionality."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Set icon - fallback to default if custom icon not found
            try:
                if os.path.exists("./Kazimierz.png"):
                    self.tray_icon.setIcon(QIcon("./Kazimierz.png"))
                else:
                    # Create a simple colored icon as fallback
                    from PyQt5.QtGui import QPixmap, QPainter
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(Qt.blue)
                    self.tray_icon.setIcon(QIcon(pixmap))
            except Exception as e:
                print(f"Warning: Could not set tray icon: {e}")
                
            self.tray_icon.setToolTip("Memoir - Monitoring System")
            
            # Create context menu for tray icon
            tray_menu = QMenu()
            
            show_action = QAction("Show Memoir", self)
            show_action.triggered.connect(self.show_and_raise)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            # Notifications toggle
            self.notifications_action = QAction("Enable Notifications", self)
            self.notifications_action.setCheckable(True)
            self.notifications_action.setChecked(self.settings.get('notifications_enabled', True))
            self.notifications_action.triggered.connect(self.toggle_notifications)
            tray_menu.addAction(self.notifications_action)
            
            # Monitoring settings
            settings_action = QAction("Monitoring Settings", self)
            settings_action.triggered.connect(self.show_monitoring_settings)
            tray_menu.addAction(settings_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            
            # Connect tray icon activation
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            # Show tray icon
            self.tray_icon.show()
            
            print("System tray initialized successfully")
        else:
            print("Warning: System tray not available")
            self.tray_icon = None

    def show_and_raise(self):
        """Show and raise the main window."""
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_and_raise()

    def toggle_notifications(self):
        """Toggle notification system on/off."""
        self.settings['notifications_enabled'] = self.notifications_action.isChecked()
        save_settings(self.settings)
        
        status = "enabled" if self.settings['notifications_enabled'] else "disabled"
        print(f"Notifications {status}")

    def show_monitoring_settings(self):
        """Show the monitoring settings dialog."""
        dialog = MonitoringSettingsDialog(self, self.monitoring_settings)
        if dialog.exec_() == QDialog.Accepted:
            # Save the new settings
            new_settings = dialog.get_settings()
            save_monitoring_settings(new_settings)
            self.monitoring_settings = new_settings
            
            # Reconnect MQTT with new settings if needed
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.init_mqtt()
            
            # Update monitoring widgets with new settings
            self.update_monitoring_widgets_settings()
            
            print("Monitoring settings updated successfully")

    def update_monitoring_widgets_settings(self):
        """Update monitoring widgets with new settings."""
        if hasattr(self, 'monitoring_widgets'):
            for node_name, widget in self.monitoring_widgets.items():
                status_dot = widget.findChild(QLabel, "status_dot")
                if status_dot:
                    # Update size
                    dot_size = self.monitoring_settings['appearance']['status_dot_size']
                    status_dot.setFixedSize(dot_size, dot_size)
                    
                    # Update current status color
                    current_status = self.monitoring_status.get(node_name, 'unknown')
                    self.update_monitoring_status(node_name, current_status)

    def quit_application(self):
        """Properly quit the application."""
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        self.close()

    def init_mqtt(self):
        """Initialize MQTT client if available."""
        if not MQTT_AVAILABLE:
            print("MQTT not available - monitoring features disabled")
            return
            
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        # Connect MQTT signals
        self.mqtt_signal.data_received.connect(self.handle_mqtt_data)
        self.mqtt_signal.status_changed.connect(self.handle_status_change)
        self.mqtt_signal.error_received.connect(self.handle_error_notification)
        
        # Start MQTT connection in a separate thread
        mqtt_thread = threading.Thread(target=self.connect_mqtt, daemon=True)
        mqtt_thread.start()

    def connect_mqtt(self):
        """Connect to MQTT broker in a separate thread."""
        try:
            mqtt_settings = self.monitoring_settings['mqtt']
            host = mqtt_settings['broker_host']
            port = mqtt_settings['broker_port']
            keepalive = mqtt_settings['keepalive']
            
            print(f"Attempting to connect to MQTT broker at {host}:{port}...")
            
            # Set up authentication if enabled
            if mqtt_settings['enable_auth']:
                username = mqtt_settings['username']
                password = mqtt_settings['password']
                if username and password:
                    self.mqtt_client.username_pw_set(username, password)
                    print(f"Using MQTT authentication for user: {username}")
            
            # Set up SSL if enabled
            if mqtt_settings['enable_ssl']:
                self.mqtt_client.tls_set()
                print("SSL/TLS enabled for MQTT connection")
            
            self.mqtt_client.connect(host, port, keepalive)
            self.mqtt_client.loop_forever()
        except Exception as e:
            print(f"MQTT connection error: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            print("Connected to MQTT broker")
            # Subscribe to all monitoring topics
            client.subscribe("/monitoring/+")
            client.subscribe("/monitoring/+/error")
        else:
            print(f"Failed to connect to MQTT broker: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        topic = msg.topic
        message = msg.payload.decode('utf-8')
        self.mqtt_signal.data_received.emit(topic, message)

    def on_mqtt_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        print("Disconnected from MQTT broker")

    def handle_mqtt_data(self, topic, message):
        """Handle MQTT data in GUI thread."""
        try:
            data = json.loads(message)
            status = data.get('status', 'unknown')
            
            # Extract monitoring node name from topic
            if topic.startswith('/monitoring/'):
                if topic.endswith('/error'):
                    node_name = topic.split('/')[2]  # Get node name from /monitoring/node/error
                    # Handle error message
                    error_type = data.get('error_type', 'unknown')
                    self.mqtt_signal.error_received.emit(node_name, error_type, message)
                else:
                    node_name = topic.split('/')[2]  # Get node name from /monitoring/node
                    # Handle normal status
                    self.mqtt_signal.status_changed.emit(node_name, status)
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON received on topic {topic}: {message}")
        except IndexError:
            print(f"Invalid topic format: {topic}")

    def handle_status_change(self, node_name, status):
        """Handle status changes for monitoring nodes."""
        self.monitoring_status[node_name] = status
        
        # Reset error count if status is normal
        if status == 'normal':
            self.error_counts[node_name] = 0
        elif status == 'error':
            # Increment error count
            self.error_counts[node_name] = self.error_counts.get(node_name, 0) + 1
            
            # Check if we should trigger an alert
            self.check_alert_trigger(node_name, status)
        
        # Update UI if monitoring tab is active
        if hasattr(self, 'monitoring_widgets'):
            self.update_monitoring_status(node_name, status)
    
    def check_alert_trigger(self, node_name, status):
        """Check if alert should be triggered based on settings."""
        if not self.monitoring_settings['triggers']['enable_alerts']:
            return
        
        # Check if we've reached the alert threshold
        error_count = self.error_counts.get(node_name, 0)
        threshold = self.monitoring_settings['triggers']['alert_threshold']
        
        if error_count >= threshold:
            # Check cooldown period
            current_time = time.time()
            last_alert = self.last_alert_time.get(node_name, 0)
            cooldown = self.monitoring_settings['triggers']['cooldown_period']
            
            if current_time - last_alert >= cooldown:
                self.trigger_alert(node_name, status)
                self.last_alert_time[node_name] = current_time
    
    def trigger_alert(self, node_name, status):
        """Trigger an alert for a monitoring node."""
        print(f"Alert triggered for {node_name}: {status}")
        
        # Show notification if enabled
        if self.monitoring_settings['triggers']['enable_notification']:
            notification_msg = f"Alert: {node_name} has {self.error_counts[node_name]} consecutive errors"
            self.show_notification("Monitoring Alert", notification_msg)
        
        # Play sound if enabled
        if self.monitoring_settings['triggers']['enable_sound']:
            # Simple beep sound (you can enhance this with actual audio files)
            print("\a")  # ASCII bell character

    def handle_error_notification(self, node_name, error_type, message):
        """Handle error notifications."""
        self.monitoring_status[node_name] = 'error'
        self.notification_count += 1
        
        # Update UI
        if hasattr(self, 'monitoring_widgets'):
            self.update_monitoring_status(node_name, 'error')
            self.update_notification_badge()
        
        # Show system notification if enabled
        if self.settings.get('notifications_enabled', True):
            notification_msg = f"Detected Anomalies on {node_name}\nError type: {error_type}"
            self.show_notification("Memoir Alert", notification_msg)

    def show_notification(self, title, message):
        """Show system notification with enhanced error handling."""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                # Show system tray notification
                self.tray_icon.showMessage(
                    title, 
                    message, 
                    QSystemTrayIcon.Warning, 
                    5000  # 5 seconds
                )
                print(f"Notification sent: {title} - {message}")
                return True
            else:
                # Fallback: Show message box if tray not available
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.show()
                print(f"Fallback notification shown: {title} - {message}")
                return True
        except Exception as e:
            print(f"Error showing notification: {e}")
            return False

    def update_monitoring_status(self, node_name, status):
        """Update monitoring status in UI."""
        if hasattr(self, 'monitoring_widgets') and node_name in self.monitoring_widgets:
            widget = self.monitoring_widgets[node_name]
            status_dot = widget.findChild(QLabel, "status_dot")
            if status_dot:
                # Get color from settings
                colors = self.monitoring_settings['status_colors']
                color = colors.get(status, colors['unknown'])
                
                # Get dot size from settings
                dot_size = self.monitoring_settings['appearance']['status_dot_size']
                radius = dot_size // 2
                
                status_dot.setStyleSheet(f"background: {color}; border-radius: {radius}px;")
                print(f"Status dot updated to {color} for {node_name} ({status})")

    def update_notification_badge(self):
        """Update notification badge on monitoring tab."""
        if hasattr(self, 'tab_widget') and hasattr(self, 'monitoring_tab_index') and self.notification_count > 0:
            # Update the tab text using the tab widget and index
            self.tab_widget.setTabText(self.monitoring_tab_index, f"Monitoring ({self.notification_count})")
        elif hasattr(self, 'tab_widget') and hasattr(self, 'monitoring_tab_index'):
            # Reset to normal text when no notifications
            self.tab_widget.setTabText(self.monitoring_tab_index, "Monitoring")

    def on_tab_changed(self, index):
        """Handle tab change events to clear notifications when monitoring tab is viewed."""
        if hasattr(self, 'monitoring_tab_index') and index == self.monitoring_tab_index:
            # User switched to monitoring tab, clear notification count
            if self.notification_count > 0:
                self.notification_count = 0
                self.update_notification_badge()

    def restore_window_state(self):
        """Restore window position and size from settings."""
        window_settings = self.settings.get('window', {})
        
        x = window_settings.get('x', 100)
        y = window_settings.get('y', 100)
        width = window_settings.get('width', 700)
        height = window_settings.get('height', 450)
        
        # Ensure the window is within screen bounds
        screen = QApplication.desktop().screenGeometry()
        if x < 0 or x + width > screen.width():
            x = max(0, (screen.width() - width) // 2)
        if y < 0 or y + height > screen.height():
            y = max(0, (screen.height() - height) // 2)
        
        self.setGeometry(x, y, width, height)

    def save_window_state(self):
        """Save current window position and size to settings."""
        self.settings['window'] = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }
        
        # Save splitter state if available
        if hasattr(self, 'splitter'):
            self.settings['splitter'] = self.splitter.sizes()
        
        save_settings(self.settings)

    def init_ui(self):
        central = QWidget(self)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        self.setCentralWidget(central)

        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            background: transparent;
            border-radius: 12px;
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0,0,0,180))
        self.main_frame.setGraphicsEffect(shadow)
        layout.addWidget(self.main_frame)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.build_notes_panel())
        self.splitter.addWidget(self.build_reminders_panel())
        
        # Restore splitter state
        splitter_sizes = self.settings.get('splitter', [350, 350])
        self.splitter.setSizes(splitter_sizes)

        mf_layout = QHBoxLayout(self.main_frame)
        mf_layout.setContentsMargins(0,0,0,0)
        mf_layout.addWidget(self.splitter)
        
        # Initialize MQTT after UI is ready
        self.init_mqtt()

    def build_notes_panel(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
              background: #121212;
              border-top-left-radius: 12px;
              border-bottom-left-radius: 12px;
            }
            QTextEdit {
              background: #121212;
              color: #FDE047;
              border: none;
              font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
              font-size: 14px;
              selection-background-color: #8b1fb5;
              padding: 8px;
            }
            QTextEdit:focus {
              border: none;
            }
            QLabel {
              color: white;
            }
        """)
        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        # Header with hamburger menu and NOTE title
        hdr = QHBoxLayout()
        
        # Hamburger menu icon
        hamburger = QLabel()
        hamburger.setFixedSize(16, 12)
        hamburger.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #9CA3AF;
            }
        """)
        hamburger.setText("☰")
        hamburger.setAlignment(Qt.AlignCenter)
        hdr.addWidget(hamburger)
        
        hdr.addSpacing(8)
        
        lbl = QLabel("NOTE")
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 16px; font-family: sans-serif;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        v.addLayout(hdr)

        # Add border separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("border: 1px solid #374151; margin: 8px 0px;")
        v.addWidget(separator)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Enter your notes here...")
        self.note_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #FDE047;
                border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit::placeholder {
                color: #6B7280;
            }
        """)
        note_content = load_note()
        if note_content:
            self.note_edit.setText(note_content)
        
        # Debounced save to avoid excessive file I/O
        self._save_timer = None
        self.note_edit.textChanged.connect(self.on_note_changed)
        v.addWidget(self.note_edit)
        return f

    def on_note_changed(self):
        """Handle note text changes with debounced saving."""
        if hasattr(self, '_save_timer') and self._save_timer:
            self._save_timer.stop()
        
        from PyQt5.QtCore import QTimer
        self._save_timer = QTimer()
        self._save_timer.timeout.connect(lambda: save_note(self.note_edit.toPlainText()))
        self._save_timer.setSingleShot(True)
        self._save_timer.start(500)  # 500ms delay

    def build_reminders_panel(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
              background: #2a1f3d;
              border-top-right-radius: 12px;
              border-bottom-right-radius: 12px;
            }
            QLabel {
              color: white;
              font-size: 16px;
              font-weight: bold;
            }
            QPushButton:hover {
              opacity: 0.8;
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #3d324a;
                color: #D1D5DB;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #6b46c1;
                color: white;
            }
            QTabBar::tab:hover {
                background: #5a3a8a;
            }
        """)
        self.rem_frame = f
        self.reminder_minimized = False
        self.show_add_form = False

        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        # Header with title and control buttons
        hdr = QHBoxLayout()
        lbl = QLabel("REMINDER")
        lbl.setStyleSheet("color: #F3F4F6; font-weight: bold; font-size: 16px; font-family: sans-serif;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        
        # Add minimize button
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(24,24)
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background: transparent; 
                color: #D1D5DB; 
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(107, 114, 128, 0.3);
                color: white;
            }
        """)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.toggle_reminder_minimize)
        hdr.addWidget(self.minimize_btn)
        
        close = QPushButton("✕")
        close.setFixedSize(24,24)
        close.setStyleSheet("""
            QPushButton {
                background: transparent; 
                color: #D1D5DB; 
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(107, 114, 128, 0.3);
                color: white;
            }
        """)
        close.setToolTip("Close")
        close.clicked.connect(self.close)
        hdr.addWidget(close)
        v.addLayout(hdr)

        # Add border separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("border: 1px solid #4A3A5C; margin: 8px 0px;")
        v.addWidget(separator)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #3d324a;
                color: #D1D5DB;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #6b46c1;
                color: white;
            }
            QTabBar::tab:hover {
                background: #5a3a8a;
            }
        """)

        # Create reminder tab
        self.reminder_tab = self.build_reminder_tab()
        self.tab_widget.addTab(self.reminder_tab, "Reminder")

        # Create monitoring tab - FIXED: Store index instead of widget
        self.monitoring_tab_widget = self.build_monitoring_tab()
        self.monitoring_tab_index = self.tab_widget.addTab(self.monitoring_tab_widget, "Monitoring")

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        v.addWidget(self.tab_widget)

        # Add resize grip
        self.resizer = QSizeGrip(f)
        self.resizer.setFixedSize(12, 12)
        self.resizer.setStyleSheet("background:rgba(255,255,255,0.3); border-radius:2px;")
        v.addWidget(self.resizer, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.load_reminders()
        return f

    def build_reminder_tab(self):
        """Build the reminder tab content."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        # Create reminder content widget
        self.reminder_content = QWidget()
        reminder_content_layout = QVBoxLayout(self.reminder_content)
        reminder_content_layout.setContentsMargins(0, 0, 0, 0)

        self.rem_list = QVBoxLayout()
        self.rem_list.setSpacing(8)
        self.rem_list.addStretch()
        reminder_content_layout.addLayout(self.rem_list)

        # Create inline add form
        self.create_add_form()
        reminder_content_layout.addWidget(self.add_form_widget)

        # Add reminder button (initially visible)
        self.create_add_button()
        reminder_content_layout.addWidget(self.add_button_widget)

        tab_layout.addWidget(self.reminder_content)
        return tab_widget

    def build_monitoring_tab(self):
        """Build the monitoring tab content."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        # Create monitoring content widget
        self.monitoring_content = QWidget()
        monitoring_content_layout = QVBoxLayout(self.monitoring_content)
        monitoring_content_layout.setContentsMargins(0, 0, 0, 0)

        self.monitoring_list = QVBoxLayout()
        self.monitoring_list.setSpacing(8)
        self.monitoring_list.addStretch()
        monitoring_content_layout.addLayout(self.monitoring_list)

        # Create inline add monitoring form
        self.create_add_monitoring_form()
        monitoring_content_layout.addWidget(self.add_monitoring_form_widget)

        # Add monitoring button (initially visible)
        self.create_add_monitoring_button()
        monitoring_content_layout.addWidget(self.add_monitoring_button_widget)

        tab_layout.addWidget(self.monitoring_content)
        
        # Initialize monitoring widgets dictionary
        self.monitoring_widgets = {}
        
        # Load existing monitoring configurations
        self.load_monitoring_configs()
        
        return tab_widget

    def create_add_form(self):
        """Create the inline add reminder form."""
        self.add_form_widget = QWidget()
        self.add_form_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top: 1px solid #4A3A5C;
                padding: 8px 0px;
            }
        """)
        
        form_layout = QVBoxLayout(self.add_form_widget)
        form_layout.setContentsMargins(0, 16, 0, 0)
        form_layout.setSpacing(8)

        # Reminder text input
        self.reminder_text_input = QLineEdit()
        self.reminder_text_input.setPlaceholderText("Reminder text")
        self.reminder_text_input.setStyleSheet("""
            QLineEdit {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8b5cf6;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        form_layout.addWidget(self.reminder_text_input)

        # Date input
        self.reminder_date_input = QDateEdit()
        self.reminder_date_input.setCalendarPopup(True)
        self.reminder_date_input.setDate(QDate.currentDate())
        self.reminder_date_input.setStyleSheet("""
            QDateEdit {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QDateEdit:focus {
                border-color: #8b5cf6;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #5a4d66;
                background: #3d324a;
            }
            QDateEdit::down-arrow {
                image: none;
                border: 2px solid #F3F4F6;
                border-top: none;
                border-right: none;
                width: 6px;
                height: 6px;
                margin-right: 3px;
            }
            QCalendarWidget {
                background: #2a1f3d;
                color: #F3F4F6;
                border: 1px solid #4a3a5c;
                border-radius: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #3d324a;
                color: #F3F4F6;
            }
            QCalendarWidget QToolButton {
                background: #3d324a;
                color: #F3F4F6;
                border: none;
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background: #8b5cf6;
            }
            QCalendarWidget QToolButton:pressed {
                background: #6b46c1;
            }
            QCalendarWidget QMenu {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
            }
            QCalendarWidget QSpinBox {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 2px;
            }
            QCalendarWidget QTableView {
                background: #2a1f3d;
                color: #F3F4F6;
                selection-background-color: #8b5cf6;
                selection-color: white;
                gridline-color: #4a3a5c;
            }
            QCalendarWidget QTableView::item {
                padding: 4px;
            }
            QCalendarWidget QTableView::item:selected {
                background: #8b5cf6;
                color: white;
            }
            QCalendarWidget QTableView::item:hover {
                background: #6b46c1;
            }
            QCalendarWidget QHeaderView::section {
                background: #3d324a;
                color: #F3F4F6;
                border: none;
                padding: 4px;
                font-weight: bold;
            }
        """)
        form_layout.addWidget(self.reminder_date_input)

        # Add keyboard shortcuts
        self.reminder_text_input.returnPressed.connect(self.confirm_add_reminder)
        # Note: QDateEdit doesn't have returnPressed, so we'll handle it differently
        
        # Reset styling when user changes date
        self.reminder_date_input.dateChanged.connect(self.reset_date_input_style)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Add button
        self.add_confirm_btn = QPushButton("Add")
        self.add_confirm_btn.setStyleSheet("""
            QPushButton {
                background: #6b46c1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        self.add_confirm_btn.clicked.connect(self.confirm_add_reminder)
        buttons_layout.addWidget(self.add_confirm_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #D1D5DB;
                border: 1px solid #5a4d66;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: white;
                background: rgba(107, 114, 128, 0.3);
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_add_reminder)
        buttons_layout.addWidget(self.cancel_btn)

        form_layout.addLayout(buttons_layout)
        
        # Initially hide the form
        self.add_form_widget.hide()

    def create_add_button(self):
        """Create the add reminder button."""
        self.add_button_widget = QWidget()
        self.add_button_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top: 1px solid #4A3A5C;
                padding: 8px 0px;
            }
        """)
        
        button_layout = QVBoxLayout(self.add_button_widget)
        button_layout.setContentsMargins(0, 16, 0, 0)

        self.add_btn = QPushButton("+ Add Reminder")
        self.add_btn.setStyleSheet("""
            QPushButton {
              background: #6b46c1; 
              color: white; 
              padding: 8px 16px;
              border: none;
              border-radius: 4px;
              font-weight: bold;
            }
            QPushButton:hover {
              background: #7c3aed;
            }
        """)
        self.add_btn.clicked.connect(self.show_add_form_inline)
        button_layout.addWidget(self.add_btn, alignment=Qt.AlignCenter)

    def create_add_monitoring_form(self):
        """Create the inline add monitoring form."""
        self.add_monitoring_form_widget = QWidget()
        self.add_monitoring_form_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top: 1px solid #4A3A5C;
                padding: 8px 0px;
            }
        """)
        
        form_layout = QVBoxLayout(self.add_monitoring_form_widget)
        form_layout.setContentsMargins(0, 16, 0, 0)
        form_layout.setSpacing(8)

        # Monitoring name input
        self.monitoring_name_input = QLineEdit()
        self.monitoring_name_input.setPlaceholderText("Monitoring name")
        self.monitoring_name_input.setStyleSheet("""
            QLineEdit {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8b5cf6;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        form_layout.addWidget(self.monitoring_name_input)

        # Topic input
        self.monitoring_topic_input = QLineEdit()
        self.monitoring_topic_input.setPlaceholderText("Topic (e.g., sensor1, camera1)")
        self.monitoring_topic_input.setStyleSheet("""
            QLineEdit {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8b5cf6;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        form_layout.addWidget(self.monitoring_topic_input)

        # Add keyboard shortcuts
        self.monitoring_name_input.returnPressed.connect(self.confirm_add_monitoring)
        self.monitoring_topic_input.returnPressed.connect(self.confirm_add_monitoring)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Add button
        self.add_monitoring_confirm_btn = QPushButton("Add")
        self.add_monitoring_confirm_btn.setStyleSheet("""
            QPushButton {
                background: #6b46c1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        self.add_monitoring_confirm_btn.clicked.connect(self.confirm_add_monitoring)
        buttons_layout.addWidget(self.add_monitoring_confirm_btn)

        # Cancel button
        self.cancel_monitoring_btn = QPushButton("Cancel")
        self.cancel_monitoring_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #D1D5DB;
                border: 1px solid #5a4d66;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: white;
                background: rgba(107, 114, 128, 0.3);
            }
        """)
        self.cancel_monitoring_btn.clicked.connect(self.cancel_add_monitoring)
        buttons_layout.addWidget(self.cancel_monitoring_btn)

        form_layout.addLayout(buttons_layout)
        
        # Initially hide the form
        self.add_monitoring_form_widget.hide()

    def create_add_monitoring_button(self):
        """Create the add monitoring button."""
        self.add_monitoring_button_widget = QWidget()
        self.add_monitoring_button_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-top: 1px solid #4A3A5C;
                padding: 8px 0px;
            }
        """)
        
        button_layout = QVBoxLayout(self.add_monitoring_button_widget)
        button_layout.setContentsMargins(0, 16, 0, 0)

        self.add_monitoring_btn = QPushButton("+ Add Monitoring")
        self.add_monitoring_btn.setStyleSheet("""
            QPushButton {
              background: #6b46c1; 
              color: white; 
              padding: 8px 16px;
              border: none;
              border-radius: 4px;
              font-weight: bold;
            }
            QPushButton:hover {
              background: #7c3aed;
            }
        """)
        self.add_monitoring_btn.clicked.connect(self.show_add_monitoring_form_inline)
        button_layout.addWidget(self.add_monitoring_btn, alignment=Qt.AlignCenter)

    def show_add_monitoring_form_inline(self):
        """Show the inline add monitoring form and hide the add button."""
        self.add_monitoring_button_widget.hide()
        self.add_monitoring_form_widget.show()
        self.monitoring_name_input.setFocus()
        self.monitoring_name_input.clear()
        self.monitoring_topic_input.clear()

    def cancel_add_monitoring(self):
        """Cancel adding monitoring and show the add button."""
        self.add_monitoring_form_widget.hide()
        self.add_monitoring_button_widget.show()
        self.monitoring_name_input.clear()
        self.monitoring_topic_input.clear()

    def confirm_add_monitoring(self):
        """Add the monitoring configuration and hide the form."""
        name = self.monitoring_name_input.text().strip()
        topic = self.monitoring_topic_input.text().strip()
        
        if name and topic:
            # Add the monitoring configuration
            configs = load_monitoring()
            configs.append({"name": name, "topic": topic})
            save_monitoring(configs)
            self.load_monitoring_configs()
            
            # Hide form and show button
            self.cancel_add_monitoring()

    def load_monitoring_configs(self):
        """Load and display monitoring configurations."""
        # Clear existing widgets more efficiently
        while self.monitoring_list.count() > 1:  # Keep the stretch
            item = self.monitoring_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.monitoring_widgets.clear()
        configs = load_monitoring()
        for idx, config in enumerate(configs):
            self.create_monitoring_widget(idx, config)

    def create_monitoring_widget(self, idx, config):
        """Create a single monitoring widget."""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #3d324a;
                border-radius: 4px;
                padding: 2px;
            }
            QWidget:hover {
                background: rgba(107, 114, 128, 0.2);
            }
        """)
        
        h = QHBoxLayout(container)
        h.setContentsMargins(12, 8, 8, 8)
        
        # Get monitoring name and topic
        monitoring_name = config.get('name', 'Unnamed')
        monitoring_topic = config.get('topic', 'No topic')
        
        # Create the label with bullet point, name, and topic
        lbl = QLabel(f"• {monitoring_name} ({monitoring_topic})")
        lbl.setStyleSheet("""
            QLabel {
                color: #FDE68A; 
                font-size: 14px; 
                font-weight: normal;
                background: transparent;
                padding: 0px;
            }
        """)
        lbl.setWordWrap(True)
        h.addWidget(lbl, 1)  # Give label more space
        
        # Status dot
        status_dot = QLabel()
        dot_size = self.monitoring_settings['appearance']['status_dot_size']
        status_dot.setFixedSize(dot_size, dot_size)
        status_dot.setObjectName("status_dot")
        # Use configurable color for unknown status
        unknown_color = self.monitoring_settings['status_colors']['unknown']
        radius = dot_size // 2
        status_dot.setStyleSheet(f"background: {unknown_color}; border-radius: {radius}px;")
        h.addWidget(status_dot)
        
        del_btn = QPushButton("×")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444; 
                color: white; 
                border: none; 
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        del_btn.setToolTip("Delete monitoring")
        del_btn.clicked.connect(lambda _, ix=idx: self.delete_monitoring(ix))
        h.addWidget(del_btn)
        
        self.monitoring_list.insertWidget(self.monitoring_list.count()-1, container)
        
        # Store widget reference for status updates
        self.monitoring_widgets[monitoring_topic] = container

    def delete_monitoring(self, index):
        """Delete a monitoring configuration with validation."""
        configs = load_monitoring()
        if 0 <= index < len(configs):
            configs.pop(index)
            save_monitoring(configs)
            self.load_monitoring_configs()

    def show_add_form_inline(self):
        """Show the inline add form and hide the add button."""
        self.show_add_form = True
        self.add_button_widget.hide()
        self.add_form_widget.show()
        self.reminder_text_input.setFocus()
        self.reminder_text_input.clear()

    def cancel_add_reminder(self):
        """Cancel adding reminder and show the add button."""
        self.show_add_form = False
        self.add_form_widget.hide()
        self.add_button_widget.show()
        self.reminder_text_input.clear()
        self.reset_date_input_style()

    def reset_date_input_style(self):
        """Reset the date input styling to normal."""
        self.reminder_date_input.setStyleSheet("""
            QDateEdit {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QDateEdit:focus {
                border-color: #8b5cf6;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #5a4d66;
                background: #3d324a;
            }
            QDateEdit::down-arrow {
                image: none;
                border: 2px solid #F3F4F6;
                border-top: none;
                border-right: none;
                width: 6px;
                height: 6px;
                margin-right: 3px;
            }
            QCalendarWidget {
                background: #2a1f3d;
                color: #F3F4F6;
                border: 1px solid #4a3a5c;
                border-radius: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #3d324a;
                color: #F3F4F6;
            }
            QCalendarWidget QToolButton {
                background: #3d324a;
                color: #F3F4F6;
                border: none;
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background: #8b5cf6;
            }
            QCalendarWidget QToolButton:pressed {
                background: #6b46c1;
            }
            QCalendarWidget QMenu {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
            }
            QCalendarWidget QSpinBox {
                background: #3d324a;
                color: #F3F4F6;
                border: 1px solid #5a4d66;
                border-radius: 2px;
            }
            QCalendarWidget QTableView {
                background: #2a1f3d;
                color: #F3F4F6;
                selection-background-color: #8b5cf6;
                selection-color: white;
                gridline-color: #4a3a5c;
            }
            QCalendarWidget QTableView::item {
                padding: 4px;
            }
            QCalendarWidget QTableView::item:selected {
                background: #8b5cf6;
                color: white;
            }
            QCalendarWidget QTableView::item:hover {
                background: #6b46c1;
            }
            QCalendarWidget QHeaderView::section {
                background: #3d324a;
                color: #F3F4F6;
                border: none;
                padding: 4px;
                font-weight: bold;
            }
        """)

    def confirm_add_reminder(self):
        """Add the reminder and hide the form."""
        text = self.reminder_text_input.text().strip()
        date = self.reminder_date_input.date().toString("yyyy-MM-dd")
        
        if text:  # Only check if text is provided, date is always valid from QDateEdit
            # Add the reminder
            lst = load_rems()
            lst.append({"name": text, "date": date})
            save_rems(lst)
            self.load_reminders()
            
            # Hide form and show button
            self.cancel_add_reminder()

    def toggle_reminder_minimize(self):
        """Toggle the reminder panel minimize state."""
        self.reminder_minimized = not self.reminder_minimized
        if self.reminder_minimized:
            self.tab_widget.hide()
            self.minimize_btn.setText("+")
        else:
            self.tab_widget.show()
            self.minimize_btn.setText("─")

    def load_reminders(self):
        """Load and display reminders with improved performance."""
        # Clear existing widgets more efficiently
        while self.rem_list.count() > 1:  # Keep the stretch
            item = self.rem_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        reminders = load_rems()
        for idx, rem in enumerate(reminders):
            self.create_reminder_widget(idx, rem)

    def create_reminder_widget(self, idx, rem):
        """Create a single reminder widget."""
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #3d324a;
                border-radius: 4px;
                padding: 2px;
            }
            QWidget:hover {
                background: rgba(107, 114, 128, 0.2);
            }
        """)
        
        h = QHBoxLayout(container)
        h.setContentsMargins(12, 8, 8, 8)
        
        # Format the date to match reference: (YYYY-MM-DD)
        reminder_text = rem.get('name', 'Unnamed')
        reminder_date = rem.get('date', 'No date')
        formatted_date = f"({reminder_date})"
        
        # Create the label with bullet point, text, and date
        lbl = QLabel(f"• {reminder_text} {formatted_date}")
        lbl.setStyleSheet("""
            QLabel {
                color: #FDE68A; 
                font-size: 14px; 
                font-weight: normal;
                background: transparent;
                padding: 0px;
            }
        """)
        lbl.setWordWrap(True)
        h.addWidget(lbl, 1)  # Give label more space
        
        del_btn = QPushButton("×")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444; 
                color: white; 
                border: none; 
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        del_btn.setToolTip("Delete reminder")
        del_btn.clicked.connect(lambda _, ix=idx: self.delete_reminder(ix))
        h.addWidget(del_btn)
        
        self.rem_list.insertWidget(self.rem_list.count()-1, container)

    def delete_reminder(self, index):
        """Delete a reminder with validation."""
        rems = load_rems()
        if 0 <= index < len(rems):
            rems.pop(index)
            save_rems(rems)
            self.load_reminders()

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            # Allow dragging from the top area or drag handle area
            if (event.pos().y() < 50 or 
                (event.pos().x() < 100 and event.pos().y() < 100)):
                self._offset = event.globalPos() - self.pos()
                self._resizing = False
            else:
                self._offset = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if (self._offset and 
            (event.buttons() & Qt.LeftButton) and 
            not self._resizing):
            new_pos = event.globalPos() - self._offset
            
            # Keep window within screen bounds
            screen = QApplication.desktop().screenGeometry()
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))
            
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release and save position."""
        if self._offset:
            self.save_window_state()
        self._offset = None
        self._resizing = False
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        """Handle window resize and save state."""
        super().resizeEvent(event)
        # Delay saving to avoid excessive I/O during resize
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        
        from PyQt5.QtCore import QTimer
        self._resize_timer = QTimer()
        self._resize_timer.timeout.connect(self.save_window_state)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.start(200)  # 200ms delay

    def closeEvent(self, event):
        """Handle application close and save final state."""
        # Force save any pending note changes
        if hasattr(self, '_save_timer') and self._save_timer:
            self._save_timer.stop()
            save_note(self.note_edit.toPlainText())
        
        self.save_window_state()
        
        # Hide tray icon if it exists
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
            
        super().closeEvent(event)


if __name__ == '__main__':
    # Enable high DPI support before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Prevent application from quitting when main window is hidden
    app.setQuitOnLastWindowClosed(False)
    
    window = NoteReminderApp()
    window.show()
    sys.exit(app.exec_())