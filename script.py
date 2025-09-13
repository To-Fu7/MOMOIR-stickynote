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
    QLineEdit, QSizeGrip, QGraphicsDropShadowEffect, QDateEdit
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

        v.addWidget(self.reminder_content)

        # Add resize grip
        self.resizer = QSizeGrip(f)
        self.resizer.setFixedSize(12, 12)
        self.resizer.setStyleSheet("background:rgba(255,255,255,0.3); border-radius:2px;")
        v.addWidget(self.resizer, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.load_reminders()
        return f

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
                background: #000000;
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
                background: #000000;
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
            self.reminder_content.hide()
            self.minimize_btn.setText("+")
        else:
            self.reminder_content.show()
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
        super().closeEvent(event)

if __name__ == '__main__':
    # Enable high DPI support before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    window = NoteReminderApp()
    window.show()
    sys.exit(app.exec_())
