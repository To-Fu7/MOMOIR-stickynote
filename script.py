import sys
import os
import json
from datetime import date
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QPoint, QDate, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QFrame, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QDialog, QCalendarWidget,
    QLineEdit, QSizeGrip, QGraphicsDropShadowEffect,
    QColorDialog, QCheckBox, QSpinBox, QComboBox
)
import paho.mqtt.client as mqtt

NOTE_FILE = 'sticky_note.json'
REM_FILE  = 'reminders.json'
POS_FILE  = 'window_pos.json'
SETTINGS_FILE = 'settings.json'

def load_note():
    if not os.path.exists(NOTE_FILE):
        return ""
    try:
        data = json.load(open(NOTE_FILE, 'r', encoding='utf-8'))
    except Exception:
        return ""
    return data if isinstance(data, str) else ""

def save_note(text):
    with open(NOTE_FILE, 'w', encoding='utf-8') as f:
        json.dump(text, f, ensure_ascii=False, indent=2)

def load_rems():
    if not os.path.exists(REM_FILE):
        return []
    try:
        return json.load(open(REM_FILE, 'r', encoding='utf-8'))
    except Exception:
        return []

def save_rems(lst):
    with open(REM_FILE, 'w', encoding='utf-8') as f:
        json.dump(lst, f, ensure_ascii=False, indent=2)

def load_pos():
    if not os.path.exists(POS_FILE):
        return None
    try:
        return json.load(open(POS_FILE, 'r', encoding='utf-8'))
    except Exception:
        return None

def save_pos(x, y):
    with open(POS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'x': x, 'y': y}, f)

def load_settings():
    default_settings = {
        "status_dot_color": "#00ff00",  # Green
        "trigger_enabled": True,
        "trigger_threshold": 5,  # minutes
        "mqtt_enabled": False,
        "mqtt_broker": "localhost",
        "mqtt_port": 1883,
        "mqtt_username": "",
        "mqtt_password": "",
        "mqtt_topic": "monitoring/status",
        "mqtt_keepalive": 60
    }
    
    if not os.path.exists(SETTINGS_FILE):
        save_settings(default_settings)
        return default_settings
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        # Merge with defaults to ensure all keys exist
        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value
        return settings
    except Exception:
        return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.FramelessWindowHint)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
              background: #2b2b2b;
              border-radius: 10px;
            }
            QLabel, QLineEdit {
              color: white;
              font-size: 14px;
            }
            QPushButton#ok {
              background: #8b1fb5;
              color: white;
              padding: 6px 12px;
              border-radius: 4px;
            }
        """)
        self.resize(360, 400)

        v = QVBoxLayout(self)
        v.setContentsMargins(20,20,20,20)
        title = QLabel("ADD REMINDER")
        title.setStyleSheet("font-size:24px; font-weight:bold;")
        v.addWidget(title, alignment=Qt.AlignCenter)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Reminder name…")
        v.addSpacing(10)
        v.addWidget(QLabel("Name"))
        v.addWidget(self.name_edit)

        v.addSpacing(15)
        self.cal = QCalendarWidget()
        self.cal.setGridVisible(True)
        self.cal.setMinimumDate(QDate.currentDate())
        v.addWidget(self.cal)

        v.addSpacing(10)
        self.summary = QLabel("", alignment=Qt.AlignCenter)
        self.summary.setStyleSheet("color:#ddd;")
        v.addWidget(self.summary)

        v.addStretch()
        ok = QPushButton("Add")
        ok.setObjectName("ok")
        ok.clicked.connect(self.accept)
        v.addWidget(ok, alignment=Qt.AlignCenter)

        self.cal.selectionChanged.connect(self.update_summary)
        self.name_edit.textChanged.connect(self.update_summary)
        self.update_summary()

    def update_summary(self):
        days = (self.cal.selectedDate().toPyDate() - date.today()).days
        self.summary.setText(
            f"Reminds in {days} day{'s' if days!=1 else ''}\non {self.cal.selectedDate().toString('dd MMM yyyy')}"
        )

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "date": self.cal.selectedDate().toString("yyyy-MM-dd")
        }

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, flags=Qt.FramelessWindowHint)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
              background: #2b2b2b;
              border-radius: 10px;
            }
            QLabel, QLineEdit, QSpinBox, QComboBox {
              color: white;
              font-size: 14px;
            }
            QPushButton#ok, QPushButton#cancel {
              background: #8b1fb5;
              color: white;
              padding: 6px 12px;
              border-radius: 4px;
              margin: 2px;
            }
            QPushButton#ok:hover, QPushButton#cancel:hover {
              background: #a52cd6;
            }
            QCheckBox {
              color: white;
              font-size: 14px;
            }
            QCheckBox::indicator {
              width: 18px;
              height: 18px;
            }
            QCheckBox::indicator:unchecked {
              border: 2px solid #ccc;
              background: transparent;
              border-radius: 3px;
            }
            QCheckBox::indicator:checked {
              border: 2px solid #8b1fb5;
              background: #8b1fb5;
              border-radius: 3px;
            }
        """)
        self.resize(500, 600)
        self.settings = load_settings()
        self.init_ui()

    def init_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("MONITORING SETTINGS")
        title.setStyleSheet("font-size:24px; font-weight:bold; color: white;")
        v.addWidget(title, alignment=Qt.AlignCenter)
        v.addSpacing(20)

        # Status Dot Color Section
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Status Dot Color:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 30)
        self.color_button.setStyleSheet(f"background-color: {self.settings['status_dot_color']}; border: 2px solid #ccc; border-radius: 4px;")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        v.addLayout(color_layout)
        v.addSpacing(15)

        # Trigger Settings Section
        trigger_label = QLabel("Trigger Settings")
        trigger_label.setStyleSheet("font-size:18px; font-weight:bold; color: #8b1fb5;")
        v.addWidget(trigger_label)
        
        self.trigger_enabled = QCheckBox("Enable Trigger Monitoring")
        self.trigger_enabled.setChecked(self.settings['trigger_enabled'])
        v.addWidget(self.trigger_enabled)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Threshold (minutes):"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 60)
        self.threshold_spin.setValue(self.settings['trigger_threshold'])
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        v.addLayout(threshold_layout)
        v.addSpacing(20)

        # MQTT Settings Section
        mqtt_label = QLabel("MQTT Connection Settings")
        mqtt_label.setStyleSheet("font-size:18px; font-weight:bold; color: #8b1fb5;")
        v.addWidget(mqtt_label)
        
        self.mqtt_enabled = QCheckBox("Enable MQTT")
        self.mqtt_enabled.setChecked(self.settings['mqtt_enabled'])
        v.addWidget(self.mqtt_enabled)
        
        # MQTT Broker
        broker_layout = QHBoxLayout()
        broker_layout.addWidget(QLabel("Broker:"))
        self.broker_edit = QLineEdit(self.settings['mqtt_broker'])
        broker_layout.addWidget(self.broker_edit)
        v.addLayout(broker_layout)
        
        # MQTT Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(self.settings['mqtt_port'])
        port_layout.addWidget(self.port_spin)
        port_layout.addStretch()
        v.addLayout(port_layout)
        
        # MQTT Username
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit(self.settings['mqtt_username'])
        user_layout.addWidget(self.username_edit)
        v.addLayout(user_layout)
        
        # MQTT Password
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit(self.settings['mqtt_password'])
        self.password_edit.setEchoMode(QLineEdit.Password)
        pass_layout.addWidget(self.password_edit)
        v.addLayout(pass_layout)
        
        # MQTT Topic
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("Topic:"))
        self.topic_edit = QLineEdit(self.settings['mqtt_topic'])
        topic_layout.addWidget(self.topic_edit)
        v.addLayout(topic_layout)
        
        # MQTT Keepalive
        keepalive_layout = QHBoxLayout()
        keepalive_layout.addWidget(QLabel("Keepalive (seconds):"))
        self.keepalive_spin = QSpinBox()
        self.keepalive_spin.setRange(10, 300)
        self.keepalive_spin.setValue(self.settings['mqtt_keepalive'])
        keepalive_layout.addWidget(self.keepalive_spin)
        keepalive_layout.addStretch()
        v.addLayout(keepalive_layout)
        
        v.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Save")
        ok_btn.setObjectName("ok")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        v.addLayout(button_layout)

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.settings['status_dot_color']), self, "Choose Status Dot Color")
        if color.isValid():
            self.settings['status_dot_color'] = color.name()
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 2px solid #ccc; border-radius: 4px;")

    def get_settings(self):
        return {
            "status_dot_color": self.settings['status_dot_color'],
            "trigger_enabled": self.trigger_enabled.isChecked(),
            "trigger_threshold": self.threshold_spin.value(),
            "mqtt_enabled": self.mqtt_enabled.isChecked(),
            "mqtt_broker": self.broker_edit.text().strip(),
            "mqtt_port": self.port_spin.value(),
            "mqtt_username": self.username_edit.text().strip(),
            "mqtt_password": self.password_edit.text().strip(),
            "mqtt_topic": self.topic_edit.text().strip(),
            "mqtt_keepalive": self.keepalive_spin.value()
        }

class NoteReminderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memoir")
        self.setWindowIcon(QIcon("./Kazimierz.png"))
        self._offset = None
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(700, 450)

        # Load settings and initialize monitoring
        self.settings = load_settings()
        self.mqtt_client = None
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.check_monitoring_status)
        self.last_activity = None

        pos = load_pos()
        if pos:
            self.move(pos['x'], pos['y'])

        self.init_ui()
        self.setup_mqtt()
        self.start_monitoring()

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

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.build_notes_panel())
        splitter.addWidget(self.build_reminders_panel())
        splitter.setSizes([350,350])

        mf_layout = QHBoxLayout(self.main_frame)
        mf_layout.setContentsMargins(0,0,0,0)
        mf_layout.addWidget(splitter)

        self.overlay = QWidget(self.main_frame)
        self.overlay.setStyleSheet("background: rgba(0,0,0,0.5);")
        self.overlay.hide()

    def build_notes_panel(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
              background: #2b2b2b;
              border-top-left-radius: 12px;
              border-bottom-left-radius: 12px;
            }
            QTextEdit {
              background: #3a3a3a;
              color: white;
              border-radius:6px;
              font-size:14px;
            }
        """)
        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("☰"))
        lbl = QLabel("NOTE")
        lbl.setStyleSheet("color:white; font-weight:bold; font-size:20px;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        
        # Status dot
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {self.settings['status_dot_color']}; font-size: 16px;")
        self.status_dot.setToolTip("Monitoring Status")
        hdr.addWidget(self.status_dot)
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(24, 24)
        settings_btn.setStyleSheet("background:transparent; color:white; font-size:16px;")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self.open_settings)
        hdr.addWidget(settings_btn)
        
        v.addLayout(hdr)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Type your note here…")
        self.note_edit.setText(load_note())
        self.note_edit.textChanged.connect(lambda: save_note(self.note_edit.toPlainText()))
        v.addWidget(self.note_edit)
        return f

    def build_reminders_panel(self):
        f = QFrame()
        f.setStyleSheet("""
            QFrame {
              background: #8b1fb5;
              border-top-right-radius: 12px;
              border-bottom-right-radius: 12px;
            }
            QLabel {
              color: white;
              font-size:20px;
              font-weight:bold;
            }
        """)
        self.rem_frame = f

        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        hdr = QHBoxLayout()
        lbl = QLabel("REMINDER")
        hdr.addWidget(lbl)
        hdr.addStretch()
        close = QPushButton("✕")
        close.setFixedSize(24,24)
        close.setStyleSheet("background:transparent; color:white;")
        close.clicked.connect(self.close)
        hdr.addWidget(close)
        v.addLayout(hdr)

        self.rem_list = QVBoxLayout()
        self.rem_list.setSpacing(8)
        self.rem_list.addStretch()
        v.addLayout(self.rem_list)

        btn = QPushButton("+ Add Reminder")
        btn.setStyleSheet("""
            QPushButton {
              background:black; color:white; padding:6px 12px;
              border-radius:4px;
            }
        """)
        btn.clicked.connect(self.on_add)
        v.addWidget(btn, alignment=Qt.AlignRight)

        self.resizer = QSizeGrip(f)
        self.resizer.setFixedSize(10, 10)
        self.resizer.setStyleSheet("background:white; border:2px solid #ccc;")
        v.addWidget(self.resizer, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.load_reminders()
        return f

    def load_reminders(self):
        for i in reversed(range(self.rem_list.count()-1)):
            w = self.rem_list.itemAt(i).widget()
            if w: w.deleteLater()

        for idx, rem in enumerate(load_rems()):
            h = QHBoxLayout()
            lbl = QLabel(f"• {rem['name']}  ({rem['date']})")
            lbl.setStyleSheet("color:white; font-size:14px;")
            h.addWidget(lbl)
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("background:#B71A1A; color:white; padding:2px 2px; border:none; border-radius:4px;")
            del_btn.clicked.connect(lambda _, ix=idx: self.delete_reminder(ix))
            h.addWidget(del_btn)
            container = QWidget()
            container.setLayout(h)
            self.rem_list.insertWidget(self.rem_list.count()-1, container)

    def delete_reminder(self, index):
        rems = load_rems()
        if 0 <= index < len(rems):
            rems.pop(index)
            save_rems(rems)
            self.load_reminders()
            
    def on_add(self):
        self.overlay.setGeometry(self.main_frame.rect())
        self.overlay.show()
        dlg = AddDialog(self)
        dlg.move(self.geometry().center() - dlg.rect().center())
        if dlg.exec_():
            lst = load_rems()
            lst.append(dlg.get_data())
            save_rems(lst)
            self.load_reminders()
        self.overlay.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 50:
            self._offset = event.globalPos() - self.pos()
        else:
            self._offset = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._offset and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._offset = None
        super().mouseReleaseEvent(event)

    def open_settings(self):
        self.overlay.setGeometry(self.main_frame.rect())
        self.overlay.show()
        dlg = SettingsDialog(self)
        dlg.move(self.geometry().center() - dlg.rect().center())
        if dlg.exec_():
            self.settings = dlg.get_settings()
            save_settings(self.settings)
            self.update_status_dot()
            self.setup_mqtt()
        self.overlay.hide()

    def update_status_dot(self):
        self.status_dot.setStyleSheet(f"color: {self.settings['status_dot_color']}; font-size: 16px;")

    def setup_mqtt(self):
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            self.mqtt_client = None

        if self.settings['mqtt_enabled']:
            try:
                self.mqtt_client = mqtt.Client()
                if self.settings['mqtt_username']:
                    self.mqtt_client.username_pw_set(
                        self.settings['mqtt_username'], 
                        self.settings['mqtt_password']
                    )
                
                self.mqtt_client.on_connect = self.on_mqtt_connect
                self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
                
                self.mqtt_client.connect(
                    self.settings['mqtt_broker'],
                    self.settings['mqtt_port'],
                    self.settings['mqtt_keepalive']
                )
                self.mqtt_client.loop_start()
            except Exception as e:
                print(f"MQTT connection failed: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT Connected successfully")
            self.publish_status("connected")
        else:
            print(f"MQTT Connection failed with code {rc}")

    def on_mqtt_disconnect(self, client, userdata, rc):
        print("MQTT Disconnected")

    def publish_status(self, status):
        if self.mqtt_client and self.settings['mqtt_enabled']:
            try:
                self.mqtt_client.publish(self.settings['mqtt_topic'], status)
            except Exception as e:
                print(f"Failed to publish MQTT message: {e}")

    def start_monitoring(self):
        if self.settings['trigger_enabled']:
            # Check every minute
            self.monitoring_timer.start(60000)  # 60 seconds
            self.last_activity = date.today()

    def check_monitoring_status(self):
        if not self.settings['trigger_enabled']:
            return

        current_date = date.today()
        if self.last_activity != current_date:
            # Activity detected
            self.last_activity = current_date
            self.publish_status("active")
            print("Activity detected - monitoring active")
        else:
            # Check if threshold exceeded
            # This is a simplified check - in a real implementation you'd track actual activity
            self.publish_status("monitoring")

    def closeEvent(self, event):
        if self.mqtt_client:
            self.publish_status("disconnected")
            self.mqtt_client.disconnect()
        save_pos(self.x(), self.y())
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NoteReminderApp()
    window.show()
    sys.exit(app.exec_())
