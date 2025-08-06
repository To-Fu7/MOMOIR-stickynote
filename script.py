import sys
import os
import json
from datetime import date
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QPoint, QDate, QSettings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QFrame, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QDialog, QCalendarWidget,
    QLineEdit, QSizeGrip, QGraphicsDropShadowEffect
)

NOTE_FILE = 'sticky_note.json'
REM_FILE  = 'reminders.json'
SETTINGS_FILE = 'app_settings.json'

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
            'splitter': [350, 350]
        }
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
        print(f"Error loading settings: {e}")
        return {
            'window': {'x': 100, 'y': 100, 'width': 700, 'height': 450},
            'splitter': [350, 350]
        }

def save_settings(settings):
    """Save application settings including window state."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except (IOError, UnicodeEncodeError) as e:
        print(f"Error saving settings: {e}")

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
            QPushButton#ok:hover {
              background: #9d2bc9;
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
        self.restore_window_state()
        
        self.init_ui()

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
              selection-background-color: #8b1fb5;
            }
            QTextEdit:focus {
              border: 1px solid #8b1fb5;
            }
        """)
        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        hdr = QHBoxLayout()
        drag_handle = QLabel("☰")
        drag_handle.setStyleSheet("color: #888; font-size: 16px;")
        drag_handle.setToolTip("Click and drag to move window")
        hdr.addWidget(drag_handle)
        lbl = QLabel("NOTE")
        lbl.setStyleSheet("color:white; font-weight:bold; font-size:20px;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        v.addLayout(hdr)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Type your note here…")
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
              background: #8b1fb5;
              border-top-right-radius: 12px;
              border-bottom-right-radius: 12px;
            }
            QLabel {
              color: white;
              font-size:20px;
              font-weight:bold;
            }
            QPushButton:hover {
              opacity: 0.8;
            }
        """)
        self.rem_frame = f

        v = QVBoxLayout(f)
        v.setContentsMargins(15,15,15,15)

        hdr = QHBoxLayout()
        lbl = QLabel("REMINDER")
        hdr.addWidget(lbl)
        hdr.addStretch()
        
        # Add minimize button
        minimize = QPushButton("─")
        minimize.setFixedSize(24,24)
        minimize.setStyleSheet("background:transparent; color:white; font-weight:bold;")
        minimize.setToolTip("Minimize")
        minimize.clicked.connect(self.showMinimized)
        hdr.addWidget(minimize)
        
        close = QPushButton("✕")
        close.setFixedSize(24,24)
        close.setStyleSheet("background:transparent; color:white; font-weight:bold;")
        close.setToolTip("Close")
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
            QPushButton:hover {
              background:#333;
            }
        """)
        btn.clicked.connect(self.on_add)
        v.addWidget(btn, alignment=Qt.AlignRight)

        # Add resize grip
        self.resizer = QSizeGrip(f)
        self.resizer.setFixedSize(12, 12)
        self.resizer.setStyleSheet("background:rgba(255,255,255,0.3); border-radius:2px;")
        v.addWidget(self.resizer, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.load_reminders()
        return f

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
        h = QHBoxLayout()
        h.setContentsMargins(5, 2, 5, 2)
        
        lbl = QLabel(f"• {rem.get('name', 'Unnamed')}  ({rem.get('date', 'No date')})")
        lbl.setStyleSheet("color:white; font-size:14px; font-weight:normal;")
        lbl.setWordWrap(True)
        h.addWidget(lbl, 1)  # Give label more space
        
        del_btn = QPushButton("×")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("""
            QPushButton {
                background:#B71A1A; 
                color:white; 
                border:none; 
                border-radius:10px;
                font-weight:bold;
            }
            QPushButton:hover {
                background:#D91A1A;
            }
        """)
        del_btn.setToolTip("Delete reminder")
        del_btn.clicked.connect(lambda _, ix=idx: self.delete_reminder(ix))
        h.addWidget(del_btn)
        
        container = QWidget()
        container.setLayout(h)
        self.rem_list.insertWidget(self.rem_list.count()-1, container)

    def delete_reminder(self, index):
        """Delete a reminder with validation."""
        rems = load_rems()
        if 0 <= index < len(rems):
            rems.pop(index)
            save_rems(rems)
            self.load_reminders()
            
    def on_add(self):
        """Handle adding new reminders."""
        self.overlay.setGeometry(self.main_frame.rect())
        self.overlay.show()
        dlg = AddDialog(self)
        dlg.move(self.geometry().center() - dlg.rect().center())
        if dlg.exec_():
            data = dlg.get_data()
            if data['name']:  # Only add if name is not empty
                lst = load_rems()
                lst.append(data)
                save_rems(lst)
                self.load_reminders()
        self.overlay.hide()

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
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Enable high DPI support
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    window = NoteReminderApp()
    window.show()
    sys.exit(app.exec_())
