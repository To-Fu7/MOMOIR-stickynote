import sys
import os
import json
from datetime import date
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt, QPoint, QDate
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QFrame, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QDialog, QCalendarWidget,
    QLineEdit, QSizeGrip, QGraphicsDropShadowEffect
)

NOTE_FILE = 'sticky_note.json'
REM_FILE  = 'reminders.json'
POS_FILE  = 'window_pos.json'

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

class NoteReminderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memoir")
        self.setWindowIcon(QIcon("./Kazimierz.png"))
        self._offset = None
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(700, 450)

        pos = load_pos()
        if pos:
            self.move(pos['x'], pos['y'])

        self.init_ui()

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

    def closeEvent(self, event):
        save_pos(self.x(), self.y())
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NoteReminderApp()
    window.show()
    sys.exit(app.exec_())
