#!/usr/bin/env python3
"""Session Reminders - Pomodoro & Health Reminders for Puthu Tracker"""
import json, os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class ToggleSwitch(QWidget):
    """Custom toggle switch with ON/OFF text"""
    toggled = pyqtSignal(bool)
    
    def __init__(self, checked=False, is_dark=False):
        super().__init__()
        self.checked = checked
        self.is_dark = is_dark
        self.setFixedSize(70, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.animating = False
        self.animation_progress = 1.0 if checked else 0.0
        
        # Set size policy to prevent resizing
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
    
    def sizeHint(self):
        return QSize(70, 32)
    
    def minimumSizeHint(self):
        return QSize(70, 32)
    
    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.start_animation()
        self.toggled.emit(self.checked)
    
    def start_animation(self):
        if not self.animating:
            self.animating = True
            self.animation_timer.start(16)  # ~60 FPS
    
    def animate(self):
        target = 1.0 if self.checked else 0.0
        step = 0.12  # Slightly slower for smoother animation
        
        if abs(self.animation_progress - target) < 0.02:  # Increased threshold
            self.animation_progress = target
            self.animating = False
            self.animation_timer.stop()
        else:
            if self.animation_progress < target:
                self.animation_progress = min(target, self.animation_progress + step)
            else:
                self.animation_progress = max(target, self.animation_progress - step)
        
        self.update()
    
    def setChecked(self, checked):
        self.checked = checked
        self.animation_progress = 1.0 if checked else 0.0
        self.update()
    
    def isChecked(self):
        return self.checked
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors based on theme
        if self.is_dark:
            bg_off = QColor("#48484A")
            bg_on = QColor("#34C759")
            knob_color = QColor("#FFFFFF")
            text_on_color = QColor("#FFFFFF")
            text_off_color = QColor("#98989D")
        else:
            bg_off = QColor("#D1D1D6")  # Darker gray for better visibility
            bg_on = QColor("#34C759")
            knob_color = QColor("#FFFFFF")
            text_on_color = QColor("#FFFFFF")
            text_off_color = QColor("#8E8E93")  # Darker text when off
        
        # Interpolate background color
        progress = self.animation_progress
        bg_r = int(bg_off.red() + (bg_on.red() - bg_off.red()) * progress)
        bg_g = int(bg_off.green() + (bg_on.green() - bg_off.green()) * progress)
        bg_b = int(bg_off.blue() + (bg_on.blue() - bg_off.blue()) * progress)
        bg_color = QColor(bg_r, bg_g, bg_b)
        
        # Draw background
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 70, 32, 16, 16)
        
        # Draw text with appropriate color
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        if self.checked:
            painter.setPen(text_on_color)
            painter.drawText(QRect(8, 0, 30, 32), Qt.AlignmentFlag.AlignCenter, "ON")
        else:
            painter.setPen(text_off_color)
            painter.drawText(QRect(32, 0, 30, 32), Qt.AlignmentFlag.AlignCenter, "OFF")
        
        # Draw knob
        knob_x = int(6 + (70 - 28 - 6) * progress)
        painter.setBrush(knob_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(knob_x, 4, 24, 24)

class RemindersManager:
    def __init__(self):
        self.settings_file = os.path.join(os.path.dirname(__file__), 'reminders_settings.json')
        self.settings = self.load_settings()
        self.last_reminders = {}
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except: pass
        return self.get_default_settings()
    
    def get_default_settings(self):
        return {
            'pomodoro_enabled': True, 'pomodoro_work_minutes': 25,
            'pomodoro_break_minutes': 5, 'pomodoro_long_break_minutes': 15,
            'pomodoro_sessions_before_long_break': 4,
            'hourly_break_enabled': True, 'hourly_break_interval': 60,
            'eye_strain_enabled': True, 'eye_strain_interval': 20,
            'hydration_enabled': True, 'hydration_interval': 30,
            'posture_enabled': True, 'posture_interval': 45,
            'notifications_enabled': True
        }
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except: return False
    
    def should_remind(self, reminder_type, interval_minutes):
        """Check if enough time has passed for this reminder"""
        now = datetime.now()
        
        # First time this reminder is checked
        if reminder_type not in self.last_reminders:
            self.last_reminders[reminder_type] = now
            return False  # Don't show immediately on first check
        
        # Calculate time since last reminder
        time_since = (now - self.last_reminders[reminder_type]).total_seconds() / 60
        
        # Check if interval has passed
        if time_since >= interval_minutes:
            self.last_reminders[reminder_type] = now
            return True
        
        return False

class PomodoroTimer(QWidget):
    timer_finished = pyqtSignal(str)
    
    def __init__(self, manager, theme_manager=None):
        super().__init__()
        self.manager, self.theme = manager, theme_manager
        self.timer, self.time_left = QTimer(), 0
        self.is_work, self.session_count, self.is_running = True, 0, False
        self.timer.timeout.connect(self.update_timer)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("Work Session")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_label = QLabel("Session 0/4")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFixedHeight(44)
        self.start_btn.clicked.connect(self.toggle_timer)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.reset_btn = QPushButton("↻ Reset")
        self.reset_btn.setFixedHeight(44)
        self.reset_btn.clicked.connect(self.reset_timer)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        
        for w in [self.time_label, self.status_label, self.session_label]:
            layout.addWidget(w)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.apply_styling()
        self.reset_timer()
    
    def apply_styling(self):
        theme = self.theme.get_current_theme() if self.theme else {}
        is_dark = self.theme.dark_mode if self.theme else False
        tc = theme.get('text_primary', '#FFFFFF' if is_dark else '#1C1C1E')
        tm = theme.get('text_muted', '#98989D' if is_dark else '#8E8E93')
        
        self.time_label.setStyleSheet(f"font-size:48px;font-weight:800;color:{tc};background:transparent")
        self.status_label.setStyleSheet(f"font-size:18px;font-weight:600;color:{tc};background:transparent")
        self.session_label.setStyleSheet(f"font-size:14px;color:{tm};background:transparent")
        self.start_btn.setStyleSheet("QPushButton{background:#34C759;color:white;border:none;border-radius:8px;font-weight:600;padding:10px 20px;font-size:15px}QPushButton:hover{background:#28A745}")
        
        if is_dark:
            self.reset_btn.setStyleSheet("QPushButton{background:#2C2C2E;color:#007AFF;border:none;border-radius:8px;font-weight:600;padding:10px 20px;font-size:15px}QPushButton:hover{background:#3A3A3C}")
        else:
            self.reset_btn.setStyleSheet("QPushButton{background:#F2F2F7;color:#007AFF;border:none;border-radius:8px;font-weight:600;padding:10px 20px;font-size:15px}QPushButton:hover{background:#E5E5EA}")
    
    def toggle_timer(self):
        if self.is_running: self.pause_timer()
        else: self.start_timer()
    
    def start_timer(self):
        self.is_running = True
        self.timer.start(1000)
        self.start_btn.setText("⏸ Pause")
    
    def pause_timer(self):
        self.is_running = False
        self.timer.stop()
        self.start_btn.setText("▶ Resume")
    
    def reset_timer(self):
        self.is_running, self.is_work, self.session_count = False, True, 0
        self.timer.stop()
        self.time_left = self.manager.settings['pomodoro_work_minutes'] * 60
        self.update_display()
        self.start_btn.setText("▶ Start")
        self.status_label.setText("Work Session")
        self.session_label.setText("Session 0/4")
    
    def update_timer(self):
        self.time_left -= 1
        if self.time_left <= 0: self.timer_complete()
        self.update_display()
    
    def timer_complete(self):
        self.timer.stop()
        self.is_running = False
        if self.is_work:
            self.session_count += 1
            sbf = self.manager.settings['pomodoro_sessions_before_long_break']
            if self.session_count >= sbf:
                self.time_left = self.manager.settings['pomodoro_long_break_minutes'] * 60
                self.status_label.setText("Long Break!")
                self.timer_finished.emit('long_break')
            else:
                self.time_left = self.manager.settings['pomodoro_break_minutes'] * 60
                self.status_label.setText("Short Break")
                self.timer_finished.emit('break')
            self.is_work = False
        else:
            self.time_left = self.manager.settings['pomodoro_work_minutes'] * 60
            self.is_work = True
            self.status_label.setText("Work Session")
            self.timer_finished.emit('work')
        self.session_label.setText(f"Session {self.session_count}/4")
        self.start_btn.setText("▶ Start")
        self.update_display()
    
    def update_display(self):
        m, s = self.time_left // 60, self.time_left % 60
        self.time_label.setText(f"{m:02d}:{s:02d}")

class RemindersWidget(QWidget):
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme = theme_manager
        self.manager = RemindersManager()
        self.init_timers()
        self.init_ui()
    
    def init_timers(self):
        """Initialize reminder timers - check every minute"""
        # Main timer that checks all reminders every minute
        self.reminder_check_timer = QTimer()
        self.reminder_check_timer.timeout.connect(self.check_all_reminders)
        self.reminder_check_timer.start(60000)  # Check every 60 seconds
    
    def check_all_reminders(self):
        """Check all enabled reminders"""
        if self.manager.settings['hourly_break_enabled']:
            self.check_reminder('hourly_break', "☕ Hourly Break", "Time to take a break! Stand up and stretch.")
        
        if self.manager.settings['eye_strain_enabled']:
            self.check_reminder('eye_strain', "👁️ Eye Strain Prevention", "Look at something 20 feet away for 20 seconds (20-20-20 rule).")
        
        if self.manager.settings['hydration_enabled']:
            self.check_reminder('hydration', "💧 Hydration Reminder", "Time to drink some water! Stay hydrated.")
        
        if self.manager.settings['posture_enabled']:
            self.check_reminder('posture', "🪑 Posture Check", "Check your posture! Sit up straight and relax your shoulders.")
    
    def init_ui(self):
        theme = self.theme.get_current_theme() if self.theme else {}
        is_dark = self.theme.dark_mode if self.theme else False
        tc = theme.get('text_primary', '#FFFFFF' if is_dark else '#1C1C1E')
        tm = theme.get('text_muted', '#98989D' if is_dark else '#8E8E93')
        bg = theme.get('card_bg', '#1C1C1E' if is_dark else '#FFFFFF')
        border = theme.get('border', '#48484A' if is_dark else '#E5E5EA')
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        if is_dark:
            scroll.setStyleSheet("""
                QScrollArea {background-color: transparent; border: none;}
                QScrollBar:vertical {background-color: #1C1C1E; width: 12px; border-radius: 6px;}
                QScrollBar::handle:vertical {background-color: #48484A; border-radius: 6px; min-height: 30px;}
                QScrollBar::handle:vertical:hover {background-color: #007AFF;}
            """)
        else:
            scroll.setStyleSheet("""
                QScrollArea {background-color: transparent; border: none;}
                QScrollBar:vertical {background-color: #F0F2F5; width: 12px; border-radius: 6px;}
                QScrollBar::handle:vertical {background-color: #D1D1D6; border-radius: 6px; min-height: 30px;}
                QScrollBar::handle:vertical:hover {background-color: #007AFF;}
            """)
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(0,0,15,0)
        
        title = QLabel("⏰ Session Reminders")
        title.setStyleSheet(f"font-size:28px;font-weight:700;color:{tc};background-color:transparent;margin-bottom:10px")
        layout.addWidget(title)
        
        # Pomodoro card
        pom_card = QFrame()
        pom_card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        pom_layout = QVBoxLayout(pom_card)
        pom_layout.setContentsMargins(30,24,30,24)
        pom_layout.setSpacing(18)
        
        pom_header = QLabel("🍅  Pomodoro Timer")
        pom_header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        pom_layout.addWidget(pom_header)
        
        pom_desc = QLabel("25 minutes work, 5 minutes break")
        pom_desc.setStyleSheet(f"font-size:13px;color:{tm};background-color:transparent")
        pom_layout.addWidget(pom_desc)
        
        self.pomodoro = PomodoroTimer(self.manager, self.theme)
        self.pomodoro.timer_finished.connect(self.on_pomodoro)
        pom_layout.addWidget(self.pomodoro)
        layout.addWidget(pom_card)
        
        # Settings card
        set_card = QFrame()
        set_card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        set_layout = QVBoxLayout(set_card)
        set_layout.setContentsMargins(30,24,30,24)
        set_layout.setSpacing(20)
        
        # Header
        set_header = QLabel("⚙️  Reminder Settings")
        set_header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        set_layout.addWidget(set_header)
        
        for title_text, desc, key, interval in [
            ("☕ Hourly Break", "Break every hour", 'hourly_break_enabled', 'hourly_break_interval'),
            ("👁️ Eye Strain", "20-20-20 rule", 'eye_strain_enabled', 'eye_strain_interval'),
            ("💧 Hydration", "Drink water", 'hydration_enabled', 'hydration_interval'),
            ("🪑 Posture", "Check posture", 'posture_enabled', 'posture_interval')
        ]:
            set_layout.addLayout(self.create_setting(title_text, desc, key, interval, tc, tm, border, is_dark))
        
        layout.addWidget(set_card)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
    
    def create_setting(self, title, desc, key, interval, tc, tm, border, is_dark):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        row = QHBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size:16px;font-weight:600;color:{tc};background:transparent")
        
        # Use custom toggle switch with ON/OFF text
        toggle = ToggleSwitch(checked=self.manager.settings[key], is_dark=is_dark)
        toggle.toggled.connect(lambda checked, k=key: self.toggle(k, Qt.CheckState.Checked.value if checked else Qt.CheckState.Unchecked.value))
        
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(toggle)
        layout.addLayout(row)
        
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"font-size:13px;color:{tm};background:transparent")
        layout.addWidget(desc_lbl)
        
        int_row = QHBoxLayout()
        int_lbl = QLabel("Interval:")
        int_lbl.setStyleSheet(f"font-size:14px;color:{tc};background:transparent")
        
        spin = QSpinBox()
        spin.setRange(5,120)
        spin.setValue(self.manager.settings[interval])
        spin.setSuffix(" min")
        spin.setFixedWidth(150)
        spin.setFixedHeight(38)
        spin.valueChanged.connect(lambda v,k=interval: self.update_interval(k,v))
        
        if is_dark:
            spin.setStyleSheet(f"QSpinBox{{background:#2C2C2E;border:none;border-radius:8px;padding:8px 12px;font-size:14px;font-weight:600;color:{tc}}}")
        else:
            spin.setStyleSheet(f"QSpinBox{{background:#F8F9FA;border:none;border-radius:8px;padding:8px 12px;font-size:14px;font-weight:600;color:{tc}}}")
        
        int_row.addWidget(int_lbl)
        int_row.addWidget(spin)
        int_row.addStretch()
        layout.addLayout(int_row)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{border};max-height:1px")
        layout.addWidget(sep)
        
        return layout
    
    def toggle(self, key, state):
        self.manager.settings[key] = (state == Qt.CheckState.Checked.value)
        self.manager.save_settings()
    
    def update_interval(self, key, val):
        self.manager.settings[key] = val
        self.manager.save_settings()
    
    def check_reminder(self, key, title, msg):
        """Check if a reminder should be shown"""
        # Check if this specific reminder is enabled
        if not self.manager.settings.get(f'{key}_enabled', False):
            return
        
        # Get the interval for this reminder
        interval = self.manager.settings.get(f'{key}_interval', 60)
        
        # Check if enough time has passed
        if self.manager.should_remind(key, interval):
            self.show_notif(title, msg)
    
    def on_pomodoro(self, t):
        if not self.manager.settings['pomodoro_enabled']: return
        msgs = {'break': "Time for break!", 'long_break': "Long break time!", 'work': "Back to work!"}
        self.show_notif("🍅 Pomodoro", msgs.get(t, ''))
    
    def show_notif(self, title, msg):
        if self.manager.settings['notifications_enabled']:
            QMessageBox.information(self, title, msg)
    
    def update_theme(self):
        """Update theme without recreating the entire UI"""
        theme = self.theme.get_current_theme() if self.theme else {}
        is_dark = self.theme.dark_mode if self.theme else False
        tc = theme.get('text_primary', '#FFFFFF' if is_dark else '#1C1C1E')
        tm = theme.get('text_muted', '#98989D' if is_dark else '#8E8E93')
        bg = theme.get('card_bg', '#1C1C1E' if is_dark else '#FFFFFF')
        border = theme.get('border', '#48484A' if is_dark else '#E5E5EA')
        
        # Clear and rebuild the UI
        if self.layout():
            QWidget().setLayout(self.layout())
        self.init_ui()

__all__ = ['RemindersManager', 'RemindersWidget']
