#!/usr/bin/env python3
"""
Puthu Tracker - Advanced Screen Time Tracking Application
Features:
- Application usage tracking
- Browser tab tracking
- Persistent history storage
- Analytics with graphs
- Clean Apple-inspired UI
"""

import sys
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import win32gui
import win32process
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCharts import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.style as mplstyle
from category_manager import CategoryManager

# Set matplotlib style for clean appearance
mplstyle.use('seaborn-v0_8-whitegrid')

class ThemeManager:
    def __init__(self):
        self.dark_mode = False
        self.themes = {
            'light': {
                'background': '#F0F2F5',
                'panel_bg': 'white',
                'text_primary': '#000000',
                'text_secondary': '#1C1C1E',
                'text_muted': '#8E8E93',
                'border': '#E5E5EA',
                'card_bg': 'white',
                'table_bg': 'white',
                'table_hover': '#F8F9FA',
                'button_secondary_bg': '#F2F2F7',
                'button_secondary_text': '#007AFF'
            },
            'dark': {
                'background': '#000000',
                'panel_bg': '#1C1C1E',
                'text_primary': '#FFFFFF',
                'text_secondary': '#FFFFFF',
                'text_muted': '#98989D',
                'border': '#48484A',
                'card_bg': '#1C1C1E',
                'table_bg': '#1C1C1E',
                'table_hover': '#2C2C2E',
                'button_secondary_bg': '#2C2C2E',
                'button_secondary_text': '#0A84FF'
            }
        }
    
    def get_current_theme(self):
        return self.themes['dark' if self.dark_mode else 'light']
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        return self.get_current_theme()

class ThemeToggleButton(QPushButton):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.dark_mode = False
        self.setFixedSize(60, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus outline
        self.update_icon()
        self.clicked.connect(self.toggle_theme)
    
    def update_icon(self):
        if self.dark_mode:
            self.setText("☀️")  # Sun for light mode
            self.setToolTip("Switch to Light Mode")
        else:
            self.setText("🌙")  # Moon for dark mode  
            self.setToolTip("Switch to Dark Mode")
        
        bg_color = "#2C2C2E" if self.dark_mode else "#F2F2F7"
        border_color = "#38383A" if self.dark_mode else "#E5E5EA"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 15px;
                font-size: 16px;
                outline: none;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            QPushButton:focus {{
                outline: none;
                border: 2px solid {border_color};
            }}
        """)
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.update_icon()
        self.main_window.apply_theme(self.dark_mode)

# Check for enhanced features
try:
    from productivity_widget import ProductivityWidget
    from browser_tracker import BrowserTracker, ProductivityAnalyzer
    from goals_limits import GoalsManager, GoalsWidget
    from session_reminders import RemindersWidget
    from advanced_analytics import AdvancedAnalyticsWidget
    from export_backup import ExportBackupWidget
    from toast_notifications import NotificationManager
    ENHANCED_FEATURES = True
    GOALS_FEATURE = True
    REMINDERS_FEATURE = True
    ADVANCED_ANALYTICS = True
    EXPORT_BACKUP_FEATURE = True
    TOAST_NOTIFICATIONS = True
except ImportError as e:
    print(f"Some features not available: {e}")
    ENHANCED_FEATURES = False
    GOALS_FEATURE = False
    REMINDERS_FEATURE = False
    ADVANCED_ANALYTICS = False
    EXPORT_BACKUP_FEATURE = False
    TOAST_NOTIFICATIONS = False
    ProductivityWidget = None
    BrowserTracker = None
    ProductivityAnalyzer = None
    GoalsManager = None
    GoalsWidget = None
    RemindersWidget = None
    AdvancedAnalyticsWidget = None
    ExportBackupWidget = None
    NotificationManager = None

class DatabaseManager:
    def __init__(self, db_path="tracking_data.db"):
        self.db_path = Path(__file__).parent / db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Application tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    date TEXT
                )
            """)
            
            # Browser tab tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS browser_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    browser_name TEXT NOT NULL,
                    tab_title TEXT,
                    url TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER,
                    date TEXT
                )
            """)
            
            # Daily summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    total_time INTEGER,
                    top_app TEXT,
                    top_app_time INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def get_all_apps(self):
        """Get list of all tracked apps"""
        apps = set()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT app_name FROM app_usage")
            for row in cursor.fetchall():
                apps.add(row[0])
        
        return sorted(list(apps))
    
    def save_app_usage(self, app_name, window_title, start_time, end_time, duration):
        """Save application usage data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO app_usage 
                (app_name, window_title, start_time, end_time, duration, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (app_name, window_title, start_time, end_time, duration, date))
            conn.commit()
    
    def save_browser_usage(self, browser_name, tab_title, url, start_time, end_time, duration):
        """Save browser usage data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO browser_usage 
                (browser_name, tab_title, url, start_time, end_time, duration, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (browser_name, tab_title, url, start_time, end_time, duration, date))
            conn.commit()
    
    def get_app_usage_by_date(self, date=None):
        """Get application usage data for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT app_name, SUM(duration) as total_duration
                FROM app_usage 
                WHERE date = ?
                GROUP BY app_name
                ORDER BY total_duration DESC
            """, (date,))
            return cursor.fetchall()
    
    def get_browser_usage_by_date(self, date=None):
        """Get browser usage data for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT browser_name, tab_title, SUM(duration) as total_duration
                FROM browser_usage 
                WHERE date = ?
                GROUP BY browser_name, tab_title
                ORDER BY total_duration DESC
            """, (date,))
            return cursor.fetchall()
    
    def get_weekly_usage(self):
        """Get usage data for the past 7 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, SUM(duration) as total_duration
                FROM app_usage 
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
            """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            return cursor.fetchall()
    
    def get_monthly_usage(self):
        """Get usage data for the past 30 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, SUM(duration) as total_duration
                FROM app_usage 
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
            """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
            return cursor.fetchall()
    
    def clear_all_data(self):
        """Clear all tracking data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_usage")
            cursor.execute("DELETE FROM browser_usage")
            cursor.execute("DELETE FROM daily_summary")
            conn.commit()
    
    def generate_fake_data(self):
        """Generate fake test data for demonstration purposes"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing data first
            cursor.execute("DELETE FROM app_usage")
            cursor.execute("DELETE FROM browser_usage")
            
            fake_apps = [
                ('chrome.exe', 'Google Chrome'),
                ('code.exe', 'Visual Studio Code'),
                ('spotify.exe', 'Spotify'),
                ('discord.exe', 'Discord'),
                ('firefox.exe', 'Mozilla Firefox'),
                ('notepad.exe', 'Notepad'),
                ('explorer.exe', 'File Explorer'),
                ('python.exe', 'Python'),
                ('photoshop.exe', 'Adobe Photoshop'),
                ('slack.exe', 'Slack'),
                ('teams.exe', 'Microsoft Teams'),
                ('zoom.exe', 'Zoom'),
            ]
            
            # Generate data for the last 30 days
            from datetime import datetime, timedelta
            import random
            
            for day_offset in range(30):
                current_date = datetime.now() - timedelta(days=day_offset)
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Generate 5-10 random app usage entries per day
                daily_entries = random.randint(5, 10)
                
                for _ in range(daily_entries):
                    app_name, window_title = random.choice(fake_apps)
                    
                    # Random duration between 5 minutes and 3 hours
                    duration = random.randint(300, 10800)
                    
                    # Random start time during the day
                    start_hour = random.randint(8, 20)
                    start_minute = random.randint(0, 59)
                    start_time = current_date.replace(hour=start_hour, minute=start_minute, second=0)
                    end_time = start_time + timedelta(seconds=duration)
                    
                    cursor.execute("""
                        INSERT INTO app_usage 
                        (app_name, window_title, start_time, end_time, duration, date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (app_name, window_title, start_time.isoformat(), end_time.isoformat(), duration, date_str))
            
            conn.commit()

class ActivityTracker(QObject):
    data_updated = pyqtSignal()
    idle_status_changed = pyqtSignal(bool)  # Signal for idle status changes
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.current_app = None
        self.current_window = None
        self.start_time = None
        self.tracking = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.track_activity)
        
        # Idle detection settings
        self.idle_threshold = 300  # 5 minutes of inactivity (in seconds)
        self.last_input_time = time.time()
        self.is_idle = False
        self.idle_start_time = None
        
        # Initialize browser tracker
        try:
            from browser_tracker import BrowserTracker
            self.browser_tracker = BrowserTracker(db_manager)
            self.browser_tracking_enabled = True
        except Exception as e:
            print(f"Browser tracking not available: {e}")
            self.browser_tracker = None
            self.browser_tracking_enabled = False
    
    def start_tracking(self):
        """Start activity tracking"""
        self.tracking = True
        self.timer.start(1000)  # Update every second
    
    def stop_tracking(self):
        """Stop activity tracking"""
        self.tracking = False
        self.timer.stop()
        self.save_current_session()
    
    def check_idle_status(self):
        """Check if the system is idle based on last input time"""
        try:
            # Get last input info for Windows
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
            
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            
            # Calculate idle time in seconds
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            idle_seconds = millis / 1000.0
            
            # Check if system became idle (no input for idle_threshold seconds)
            if idle_seconds >= self.idle_threshold and not self.is_idle:
                self.is_idle = True
                self.idle_start_time = datetime.now() - timedelta(seconds=idle_seconds)
                # Save current session before going idle
                self.save_current_session()
                print(f"💤 System went idle (inactive for {idle_seconds:.0f}s) - tracking paused")
                # Emit signal for UI update
                self.idle_status_changed.emit(True)
                return True
            
            # Check if system became active again (user returned)
            elif idle_seconds < self.idle_threshold and self.is_idle:
                idle_duration = (datetime.now() - self.idle_start_time).total_seconds()
                print(f"👋 System active again (was idle for {idle_duration:.0f}s) - resuming tracking")
                self.is_idle = False
                self.idle_start_time = None
                # Reset current session to start fresh tracking
                self.current_app = None
                self.current_window = None
                self.start_time = None
                # Emit signal for UI update
                self.idle_status_changed.emit(False)
                return False
            
            return self.is_idle
            
        except Exception as e:
            print(f"❌ Idle check error: {e}")
            return False
    
    def track_activity(self):
        """Track current active window with idle detection"""
        try:
            # Check if system is idle first (detects inactivity or sleep)
            if self.check_idle_status():
                # Don't track while idle - this prevents tracking during:
                # - Computer sleep/hibernation
                # - User inactivity (5+ minutes)
                # - Screen locked
                return
            
            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            if not window_title:
                return
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            app_name = process.name()
            
            # Check if app changed
            if app_name != self.current_app or window_title != self.current_window:
                # Save previous session
                self.save_current_session()
                
                # Start new session
                self.current_app = app_name
                self.current_window = window_title
                self.start_time = datetime.now()
            
        except Exception as e:
            print(f"Tracking error: {e}")
    
    def save_current_session(self):
        """Save current tracking session"""
        if self.current_app and self.start_time:
            end_time = datetime.now()
            duration = int((end_time - self.start_time).total_seconds())
            
            if duration > 0:  # Only save if duration > 0
                # Save app usage
                self.db_manager.save_app_usage(
                    self.current_app,
                    self.current_window,
                    self.start_time.isoformat(),
                    end_time.isoformat(),
                    duration
                )
                
                # Save browser usage if it's a browser
                if self.browser_tracking_enabled and self.browser_tracker:
                    if self.browser_tracker.is_browser(self.current_app):
                        self.browser_tracker.track_browser_session(
                            self.current_app,
                            self.current_window,
                            self.start_time,
                            end_time,
                            duration
                        )
                
                self.data_updated.emit()

class ModernButton(QPushButton):
    def __init__(self, text, primary=False, theme_manager=None):
        super().__init__(text)
        self.primary = primary
        self.theme_manager = theme_manager
        self.setFixedHeight(40)  # Default height
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus outline
        self.apply_style()
    
    def apply_style(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007AFF;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: 700;
                    padding: 0 35px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #0056CC;
                }
                QPushButton:pressed {
                    background-color: #004499;
                }
                QPushButton:focus {
                    outline: none;
                    border: none;
                }
            """)
        else:
            button_bg = theme.get('button_secondary_bg', '#F2F2F7')
            button_text = theme.get('button_secondary_text', '#007AFF')
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_bg};
                    color: {button_text};
                    border: none;
                    border-radius: 12px;
                    font-size: 20px;
                    font-weight: 500;
                    padding: 0 35px;
                    outline: none;
                }}
                QPushButton:hover {{
                    background-color: {button_bg};
                    opacity: 0.8;
                }}
                QPushButton:pressed {{
                    background-color: {button_bg};
                    opacity: 0.6;
                }}
                QPushButton:focus {{
                    outline: none;
                    border: none;
                }}
            """)
    
    def apply_date_label_styling(self):
        """Apply styling to date label"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        
        self.date_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: 700; 
            color: {text_color};
            background-color: transparent;
            margin-right: 15px;
        """)
    
    def apply_date_edit_styling(self):
        """Apply styling to date edit widget"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            bg_color = '#3A3A3C'
            text_color = '#FFFFFF'
            border_color = '#48484A'
            focus_bg = '#2C2C2E'
        else:
            bg_color = '#F8F9FA'
            text_color = '#1C1C1E'
            border_color = '#D1D1D6'
            focus_bg = 'white'
        
        self.date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 12px 18px;
                border: 2px solid {border_color};
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                color: {text_color};
                background-color: {bg_color};
                min-width: 140px;
            }}
            QDateEdit:focus {{
                border-color: #007AFF;
                background-color: {focus_bg};
            }}
            QDateEdit::drop-down {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def update_theme(self):
        """Update button styling when theme changes"""
        self.apply_style()

class StatsCard(QFrame):
    def __init__(self, title, value, icon=None, theme_manager=None, auto_width=False):
        super().__init__()
        self.theme_manager = theme_manager
        self.auto_width = auto_width
        if not auto_width:
            self.setFixedSize(200, 120)
        else:
            self.setMinimumSize(200, 120)
            self.setMaximumHeight(120)
        self.apply_theme_styling()
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel(title)
        self.value_label = QLabel(value)
        
        # Ensure labels are visible
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
        
        # Enable word wrap for auto-width cards to handle long names
        if auto_width:
            self.value_label.setWordWrap(True)
            self.value_label.setMaximumWidth(400)  # Prevent excessive width
        
        self.apply_text_styling()
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        self.setLayout(layout)
    
    def apply_theme_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            self.setStyleSheet("""
                QFrame {
                    background-color: #1C1C1E;
                    border-radius: 12px;
                    border: none;
                }
            """)
        else:
            card_bg = theme.get('card_bg', 'white')
            border_color = theme.get('border', '#E5E5EA')
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_bg};
                    border-radius: 12px;
                    border: none;
                }}
            """)
    
    def apply_text_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_muted = theme.get('text_muted', '#8E8E93')
        text_primary = theme.get('text_primary', '#1C1C1E')
        
        self.title_label.setStyleSheet(f"""
            color: {text_muted};
            font-size: 14px;
            font-weight: 600;
            background-color: transparent;
        """)
        
        # Adjust font size for auto-width cards
        font_size = "22px" if self.auto_width else "28px"
        
        self.value_label.setStyleSheet(f"""
            color: {text_primary};
            font-size: {font_size};
            font-weight: 800;
            background-color: transparent;
            margin-top: 8px;
        """)
    
    def update_theme(self):
        self.apply_theme_styling()
        self.apply_text_styling()
    
    def update_value(self, value):
        """Update the value and adjust width if needed"""
        self.value_label.setText(value)
        if self.auto_width:
            # Adjust width based on text content
            metrics = self.value_label.fontMetrics()
            text_width = metrics.boundingRect(value).width()
            # Add padding for margins and comfortable spacing
            new_width = max(200, text_width + 60)
            self.setMinimumWidth(new_width)
            self.updateGeometry()

class AnalyticsWidget(QWidget):
    def __init__(self, db_manager, theme_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.current_chart_mode = 'weekly'  # 'weekly' or 'monthly'
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Reduced from 20
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with theme support
        self.title = QLabel("Analytics")
        self.apply_title_styling()
        layout.addWidget(self.title)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_time_card = StatsCard("Total Time Today", "0h 0m", theme_manager=self.theme_manager)
        self.apps_used_card = StatsCard("Apps Used", "0", theme_manager=self.theme_manager)
        self.most_used_card = StatsCard("Most Used App", "None", theme_manager=self.theme_manager, auto_width=True)
        
        stats_layout.addWidget(self.total_time_card)
        stats_layout.addWidget(self.apps_used_card)
        stats_layout.addWidget(self.most_used_card)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Chart container with theme support
        self.chart_container = QFrame()
        self.apply_chart_container_styling()
        chart_layout = QVBoxLayout(self.chart_container)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        # Chart header with toggle buttons
        chart_header = QHBoxLayout()
        
        self.chart_title = QLabel("Weekly Usage Trend")
        self.apply_chart_title_styling()
        
        # Chart mode toggle buttons
        button_layout = QHBoxLayout()
        self.weekly_btn = QPushButton("Weekly")
        self.monthly_btn = QPushButton("Monthly")
        
        self.weekly_btn.setFixedHeight(30)
        self.monthly_btn.setFixedHeight(30)
        self.weekly_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent grey focus box
        self.monthly_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent grey focus box
        self.weekly_btn.clicked.connect(self.show_weekly_chart)
        self.monthly_btn.clicked.connect(self.show_monthly_chart)
        
        self.apply_toggle_button_styling()
        
        button_layout.addWidget(self.weekly_btn)
        button_layout.addWidget(self.monthly_btn)
        button_layout.addStretch()
        
        chart_header.addWidget(self.chart_title)
        chart_header.addStretch()
        chart_header.addLayout(button_layout)
        
        chart_layout.addLayout(chart_header)
        
        # Matplotlib chart
        self.figure, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(self.chart_container)
        
        self.setLayout(layout)
        self.update_analytics()
    
    def apply_title_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')  # Use text_primary instead of text_secondary
        self.title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 900;
            color: {text_color};
            background-color: transparent;
            margin-bottom: 20px;
            margin-top: 15px;
        """)
    
    def apply_chart_container_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            self.chart_container.setStyleSheet("""
                QFrame {
                    background-color: #2C2C2E;
                    border: 2px solid #38383A;
                    border-radius: 12px;
                    padding: 20px;
                }
            """)
        else:
            card_bg = theme.get('card_bg', 'white')
            border_color = theme.get('border', '#E5E5EA')
            self.chart_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_bg};
                    border-radius: 12px;
                    border: 1px solid {border_color};
                    padding: 20px;
                }}
            """)
    
    def apply_chart_title_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')  # Use text_primary for better visibility
        self.chart_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {text_color};
            margin-bottom: 15px;
        """)
    
    def apply_toggle_button_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        button_bg = theme.get('button_secondary_bg', '#F2F2F7')
        text_color = theme.get('text_secondary', '#1C1C1E')
        
        active_style = f"""
            QPushButton {{
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                outline: none;
            }}
            QPushButton:focus {{
                outline: none;
                border: none;
            }}
        """
        
        inactive_style = f"""
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: 1px solid {theme.get('border', '#E5E5EA')};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {theme.get('table_hover', '#F8F9FA')};
            }}
            QPushButton:focus {{
                outline: none;
                border: 1px solid {theme.get('border', '#E5E5EA')};
            }}
        """
        
        if self.current_chart_mode == 'weekly':
            self.weekly_btn.setStyleSheet(active_style)
            self.monthly_btn.setStyleSheet(inactive_style)
        else:
            self.weekly_btn.setStyleSheet(inactive_style)
            self.monthly_btn.setStyleSheet(active_style)
    
    def show_weekly_chart(self):
        self.current_chart_mode = 'weekly'
        self.chart_title.setText("Weekly Usage Trend")
        self.apply_toggle_button_styling()
        self.update_chart()
    
    def show_monthly_chart(self):
        self.current_chart_mode = 'monthly'
        self.chart_title.setText("Monthly Usage Trend")
        self.apply_toggle_button_styling()
        self.update_chart()
    
    def update_analytics(self):
        """Update analytics data and charts"""
        # Get today's data
        today_data = self.db_manager.get_app_usage_by_date()
        
        # Calculate stats
        total_seconds = sum(duration for _, duration in today_data)
        total_hours = total_seconds // 3600
        total_minutes = (total_seconds % 3600) // 60
        
        apps_count = len(today_data)
        most_used_app = today_data[0][0] if today_data else "None"
        
        # Update cards
        self.total_time_card.value_label.setText(f"{total_hours}h {total_minutes}m")
        self.apps_used_card.value_label.setText(str(apps_count))
        # Use update_value for auto-width adjustment
        self.most_used_card.update_value(most_used_app)
        
        # Update chart
        self.update_chart()
    
    def update_chart(self):
        """Update the weekly or monthly trend chart with improved styling and better visuals"""
        if self.current_chart_mode == 'weekly':
            data = self.db_manager.get_weekly_usage()
        else:
            data = self.db_manager.get_monthly_usage()
        
        self.ax.clear()
        
        # Set chart background based on theme
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if data:
            dates = [data_point[0] for data_point in data]
            times = [data_point[1] / 3600 for data_point in data]  # Convert to hours
            
            # IMPROVED: Create smoother line with enhanced styling
            self.ax.plot(dates, times, marker='o', linewidth=3.5, markersize=10, 
                        color='#007AFF', markerfacecolor='#007AFF', markeredgecolor='white', 
                        markeredgewidth=2.5, alpha=0.95, linestyle='-', 
                        solid_capstyle='round', solid_joinstyle='round')
            
            # IMPROVED: Enhanced gradient fill with better colors
            self.ax.fill_between(dates, times, alpha=0.25, color='#007AFF', 
                               edgecolor='none', interpolate=True)
            
            # IMPROVED: Add subtle grid for better readability
            grid_color = '#38383A' if is_dark else '#E8E8E8'
            self.ax.grid(True, alpha=0.4, color=grid_color, linewidth=1.2, 
                        linestyle='--', axis='y')
            self.ax.set_axisbelow(True)  # Grid behind the data
            
            # FIXED: Format dates for better readability and prevent overcrowding
            if len(dates) > 0:
                # Only show every nth date label to prevent overcrowding
                step = max(1, len(dates) // 7)  # Show max 7 labels
                tick_positions = range(0, len(dates), step)
                tick_labels = [dates[i] for i in tick_positions]
                
                # Convert dates to datetime for better formatting
                formatted_labels = []
                for date_str in tick_labels:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        formatted_labels.append(date_obj.strftime('%m/%d'))
                    except:
                        formatted_labels.append(date_str[-5:])  # Last 5 chars (MM-DD)
                
                self.ax.set_xticks([i for i in tick_positions])
                self.ax.set_xticklabels(formatted_labels, rotation=0, ha='center', fontsize=11)
        else:
            no_data_color = '#FFFFFF' if is_dark else '#8E8E93'
            self.ax.text(0.5, 0.5, 'No data available\nStart tracking to see trends!', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=16, color=no_data_color,
                        fontweight='600', linespacing=1.5)
        
        # IMPROVED: Enhanced chart styling based on theme with better text visibility
        title_color = '#FFFFFF' if is_dark else '#1C1C1E'
        bg_color = '#2C2C2E' if is_dark else '#FAFAFA'
        border_color = '#48484A' if is_dark else '#E0E0E0'
        
        # IMPROVED: Better title without emoji to avoid font warnings
        self.ax.set_title('Daily Usage (Hours)', fontsize=18, fontweight='bold', 
                         pad=25, color=title_color, loc='left')
        
        # IMPROVED: Enhanced axis labels
        self.ax.set_xlabel('Date', fontsize=13, color=title_color, labelpad=15, fontweight='600')
        self.ax.set_ylabel('Hours', fontsize=13, color=title_color, labelpad=15, fontweight='600')
        
        # IMPROVED: Better tick styling
        self.ax.tick_params(colors=title_color, labelsize=11, width=1.5, length=6, 
                          pad=8, direction='out')
        
        # IMPROVED: Add subtle border around plot area
        for spine in self.ax.spines.values():
            spine.set_edgecolor(border_color)
            spine.set_linewidth(1.5)
        
        # Set background with better aesthetics
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        # IMPROVED: Better layout with more breathing room - wrapped in try-except to suppress warnings
        try:
            self.figure.tight_layout(pad=2.0)
        except:
            pass  # Silently ignore tight_layout warnings
        
        try:
            self.figure.subplots_adjust(bottom=0.15, left=0.13, right=0.95, top=0.88)
        except:
            pass
        
        self.canvas.draw()
    
    def update_theme(self):
        """Update all styling when theme changes"""
        self.apply_title_styling()
        self.apply_chart_container_styling()
        self.apply_chart_title_styling()
        self.apply_toggle_button_styling()
        
        # Update stats cards
        self.total_time_card.update_theme()
        self.apps_used_card.update_theme()
        self.most_used_card.update_theme()
        
        # Update chart
        self.update_chart()

class HistoryWidget(QWidget):
    def __init__(self, db_manager, theme_manager=None, category_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        # Use shared category manager or create new one
        self.category_manager = category_manager if category_manager else CategoryManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)  # Reduced from 20 to 12
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title = QLabel("Usage History")
        self.apply_title_styling()
        
        self.clear_button = ModernButton("🗑️ Clear All Data", theme_manager=self.theme_manager)
        self.clear_button.clicked.connect(self.clear_data)
        
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_button)
        
        layout.addLayout(header_layout)
        
        # Date selector with better container
        self.date_container = QFrame()
        self.apply_date_container_styling()
        date_layout = QHBoxLayout(self.date_container)
        date_layout.setSpacing(15)
        date_layout.setContentsMargins(20, 15, 20, 15)
        date_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.date_label = QLabel("📅 Select Date:")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.apply_date_label_styling()
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(45)  # Match label height
        self.apply_date_edit_styling()
        self.date_edit.dateChanged.connect(self.update_history)
        
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        layout.addWidget(self.date_container)
        
        # Tab widget for Apps and Browser tabs
        self.history_tabs = QTabWidget()
        self.apply_tabs_styling()
        
        # Applications table
        self.history_table = QTableWidget()
        self.apply_table_styling()
        self.history_tabs.addTab(self.history_table, "📱 Applications")
        
        # Browser tabs table
        self.browser_table = QTableWidget()
        self.apply_table_styling_browser()
        self.history_tabs.addTab(self.browser_table, "🌐 Browser Tabs")
        
        layout.addWidget(self.history_tabs)
        self.setLayout(layout)
        self.update_history()
    
    def apply_title_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_secondary', '#1C1C1E')
        self.title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {text_color};
            margin-bottom: 15px;
        """)
    
    def apply_date_container_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            self.date_container.setStyleSheet("""
                QFrame {
                    background-color: #2C2C2E;
                    border: 2px solid #38383A;
                    border-radius: 12px;
                    padding: 15px 20px;
                    margin-bottom: 15px;
                }
            """)
        else:
            card_bg = theme.get('card_bg', 'white')
            border_color = theme.get('border', '#E5E5EA')
            self.date_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {card_bg};
                    border-radius: 12px;
                    border: 1px solid {border_color};
                    padding: 15px 20px;
                    margin-bottom: 15px;
                }}
            """)
    
    def apply_table_styling(self):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            table_bg = '#2C2C2E'
            border_color = '#38383A'
            text_color = '#FFFFFF'
            hover_color = '#3A3A3C'
            header_bg = '#1C1C1E'
        else:
            table_bg = 'white'
            border_color = '#E5E5EA'
            text_color = '#1C1C1E'
            hover_color = '#F8F9FA'
            header_bg = '#F8F8F8'
        
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {table_bg};
                border: 2px solid {border_color};
                border-radius: 10px;
                gridline-color: {border_color};
                font-size: 14px;
                font-weight: 500;
                color: {text_color};
                selection-background-color: transparent;
                selection-color: {text_color};
                alternate-background-color: {hover_color};
            }}
            QTableWidget::item {{
                padding: 12px 18px;
                border-bottom: 1px solid {border_color};
                color: {text_color};
                background-color: {table_bg};
                font-weight: 500;
            }}
            QTableWidget::item:selected {{
                background-color: transparent;
                color: {text_color};
                font-weight: 500;
            }}
            QTableWidget::item:hover {{
                background-color: {hover_color};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                padding: 18px 20px;
                border: none;
                border-bottom: 2px solid {border_color};
                font-weight: 700;
                font-size: 15px;
                color: {text_color};
                text-align: left;
                min-height: 40px;
            }}
            QScrollBar:vertical {{
                background-color: {table_bg};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #007AFF;
            }}
        """)
    
    def apply_table_styling_browser(self):
        """Apply styling to browser table (same as history table)"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            table_bg = '#2C2C2E'
            border_color = '#38383A'
            text_color = '#FFFFFF'
            hover_color = '#3A3A3C'
            header_bg = '#1C1C1E'
        else:
            table_bg = 'white'
            border_color = '#E5E5EA'
            text_color = '#1C1C1E'
            hover_color = '#F8F9FA'
            header_bg = '#F8F8F8'
        
        self.browser_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {table_bg};
                border: 2px solid {border_color};
                border-radius: 10px;
                gridline-color: {border_color};
                font-size: 14px;
                font-weight: 500;
                color: {text_color};
                selection-background-color: transparent;
                selection-color: {text_color};
                alternate-background-color: {hover_color};
            }}
            QTableWidget::item {{
                padding: 12px 18px;
                border-bottom: 1px solid {border_color};
                color: {text_color};
                background-color: {table_bg};
                font-weight: 500;
            }}
            QTableWidget::item:selected {{
                background-color: transparent;
                color: {text_color};
                font-weight: 500;
            }}
            QTableWidget::item:hover {{
                background-color: {hover_color};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                padding: 18px 20px;
                border: none;
                border-bottom: 2px solid {border_color};
                font-weight: 700;
                font-size: 15px;
                color: {text_color};
                text-align: left;
                min-height: 40px;
            }}
            QScrollBar:vertical {{
                background-color: {table_bg};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #007AFF;
            }}
        """)
    
    def apply_tabs_styling(self):
        """Apply styling to the tab widget"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            bg_color = '#000000'
            tab_bg = '#2C2C2E'
            tab_selected_bg = '#1C1C1E'
            tab_text = '#98989D'
            tab_selected_text = '#0A84FF'
            border_color = '#48484A'
        else:
            bg_color = '#F0F2F5'
            tab_bg = '#E5E5EA'
            tab_selected_bg = 'white'
            tab_text = '#1C1C1E'
            tab_selected_text = '#007AFF'
            border_color = '#E5E5EA'
        
        self.history_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {bg_color};
            }}
            QTabBar::tab {{
                background-color: {tab_bg};
                padding: 12px 24px;
                margin-right: 3px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: 600;
                font-size: 14px;
                color: {tab_text};
                border: 1px solid {border_color};
            }}
            QTabBar::tab:selected {{
                background-color: {tab_selected_bg};
                color: {tab_selected_text};
                font-weight: 700;
                border-bottom: 2px solid {tab_selected_text};
            }}
            QTabBar::tab:hover {{
                background-color: {tab_selected_bg};
                opacity: 0.8;
            }}
        """)
    
    def apply_date_label_styling(self):
        """Apply styling to date label"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        self.date_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px; 
                font-weight: 700; 
                color: {text_color};
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """)

    def apply_date_edit_styling(self):
        """Apply styling to date edit widget"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False

        if is_dark:
            bg_color = '#3A3A3C'
            text_color = '#FFFFFF'
            border_color = '#48484A'
            focus_bg = '#2C2C2E'
        else:
            bg_color = '#F8F9FA'
            text_color = '#1C1C1E'
            border_color = '#D1D1D6'
            focus_bg = 'white'

        self.date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 12px 18px;
                border: 2px solid {border_color};
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                color: {text_color};
                background-color: {bg_color};
                min-width: 140px;
            }}
            QDateEdit:focus {{
                border-color: #007AFF;
                background-color: {focus_bg};
            }}
            QDateEdit::drop-down {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def update_theme(self):
        """Update all styling when theme changes"""
        self.apply_title_styling()
        self.apply_date_container_styling()
        self.apply_date_label_styling()
        self.apply_date_edit_styling()
        self.apply_table_styling()
        self.apply_table_styling_browser()
        self.apply_tabs_styling()
        if hasattr(self.clear_button, 'update_theme'):
            self.clear_button.update_theme()
    
    def update_history(self):
        """Update both history tables with selected date data"""
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        
        # Update Applications table
        self.update_apps_table(selected_date)
        
        # Update Browser tabs table
        self.update_browser_table(selected_date)
    
    def update_apps_table(self, selected_date):
        """Update applications table with selected date data"""
        app_data = self.db_manager.get_app_usage_by_date(selected_date)
        
        # Setup table
        self.history_table.setRowCount(len(app_data))
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["📱 Application", "⏱️ Duration", "📊 Percentage", "🏷️ Category"])
        
        # Set table properties for better visibility
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Calculate total time for percentages
        total_time = sum(duration for _, duration in app_data)
        
        # Populate table
        for row, (app_name, duration) in enumerate(app_data):
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            
            # Create items with proper text color
            app_item = QTableWidgetItem(app_name)
            app_item.setForeground(QColor("#1C1C1E"))
            
            duration_item = QTableWidgetItem(time_str)
            duration_item.setForeground(QColor("#1C1C1E"))
            
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setForeground(QColor("#1C1C1E"))
            
            self.history_table.setItem(row, 0, app_item)
            self.history_table.setItem(row, 1, duration_item)
            self.history_table.setItem(row, 2, percentage_item)

            # Category dropdown with auto-save
            def on_category_change(app_name, new_category_text):
                category_lower = new_category_text.lower()
                if category_lower == 'other':
                    category_lower = 'uncategorized'
                self.category_manager.update_app_category(app_name, category_lower)

            theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
            is_dark = self.theme_manager.dark_mode if self.theme_manager else False

            # Category dropdown - properly contained
            category_combo = self.category_manager.create_category_combo(
                app_name, 
                theme, 
                is_dark, 
                on_category_change
            )

            # Container to center the dropdown
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background-color: transparent;")
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)  # Adjust margins to fix alignment
            cell_layout.setSpacing(0)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Ensure proper alignment
            cell_layout.addWidget(category_combo)
            self.history_table.setCellWidget(row, 3, cell_widget)

        # Set specific column widths to prevent text cutoff
        self.history_table.setColumnWidth(0, 250)  # Application name
        self.history_table.setColumnWidth(1, 120)  # Duration
        self.history_table.setColumnWidth(2, 150)  # Percentage
        self.history_table.setColumnWidth(3, 170)  # Category

        # Make sure the table takes full width
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Set row height to accommodate dropdowns
        self.history_table.verticalHeader().setDefaultSectionSize(60)
    
    def update_browser_table(self, selected_date):
        """Update browser tabs table with selected date data"""
        browser_data = self.db_manager.get_browser_usage_by_date(selected_date)
        
        # Setup table
        self.browser_table.setRowCount(len(browser_data))
        self.browser_table.setColumnCount(4)
        self.browser_table.setHorizontalHeaderLabels(["🌐 Browser", "📝 Tab Title", "⏱️ Duration", "📊 Percentage"])
        
        # Set table properties for better visibility
        self.browser_table.setAlternatingRowColors(True)
        self.browser_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Calculate total time for percentages
        total_time = sum(duration for _, _, duration in browser_data)
        
        # Populate table
        for row, (browser_name, tab_title, duration) in enumerate(browser_data):
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            
            # Create items with proper text color
            browser_item = QTableWidgetItem(browser_name)
            browser_item.setForeground(QColor("#1C1C1E"))
            
            # Truncate long tab titles for better display
            display_title = tab_title if len(tab_title) <= 60 else tab_title[:57] + "..."
            tab_item = QTableWidgetItem(display_title)
            tab_item.setForeground(QColor("#1C1C1E"))
            tab_item.setToolTip(tab_title)  # Show full title on hover
            
            duration_item = QTableWidgetItem(time_str)
            duration_item.setForeground(QColor("#1C1C1E"))
            
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setForeground(QColor("#1C1C1E"))
            
            self.browser_table.setItem(row, 0, browser_item)
            self.browser_table.setItem(row, 1, tab_item)
            self.browser_table.setItem(row, 2, duration_item)
            self.browser_table.setItem(row, 3, percentage_item)
        
        # Set specific column widths to prevent text cutoff
        self.browser_table.setColumnWidth(0, 150)  # Browser name
        self.browser_table.setColumnWidth(1, 400)  # Tab title (wider for URLs)
        self.browser_table.setColumnWidth(2, 120)  # Duration
        self.browser_table.setColumnWidth(3, 120)  # Percentage
        
        # Make sure the table takes full width
        header = self.browser_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        # Set row height
        self.browser_table.verticalHeader().setDefaultSectionSize(50)
    
    def clear_data(self):
        """Clear all historical data"""
        reply = QMessageBox.question(
            self, 
            "Clear Data", 
            "Are you sure you want to clear all tracking data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.clear_all_data()
            self.update_history()
            
            # Show success notification
            try:
                main_window = self.window()
                if hasattr(main_window, 'notifier') and main_window.notifier:
                    main_window.notifier.success(
                        "Data Cleared",
                        "All tracking data has been cleared successfully.",
                        duration=4000
                    )
            except:
                pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()  # Initialize theme manager first
        self.db_manager = DatabaseManager()
        self.category_manager = CategoryManager()  # Shared category manager
        
        # Initialize notification manager
        print("Initializing notification manager...")
        if TOAST_NOTIFICATIONS and NotificationManager:
            try:
                self.notifier = NotificationManager(self)
                print(f"✅ NotificationManager created successfully: {self.notifier is not None}")
            except Exception as e:
                print(f"❌ Error creating NotificationManager: {e}")
                self.notifier = None
        else:
            print(f"❌ TOAST_NOTIFICATIONS={TOAST_NOTIFICATIONS}, NotificationManager={NotificationManager}")
            self.notifier = None
        
        # Initialize goals manager
        if GOALS_FEATURE:
            self.goals_manager = GoalsManager()
        else:
            self.goals_manager = None
        
        self.tracker = ActivityTracker(self.db_manager)
        self.init_ui()
        self.setup_connections()
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Goals check timer (check every 1 minute for better responsiveness)
        if self.goals_manager:
            self.goals_timer = QTimer()
            self.goals_timer.timeout.connect(self.check_goals)
            self.goals_timer.start(60000)  # Check every 1 minute
            print("Goals notification system initialized - will check every minute")
            print(f"Notifier initialized: {self.notifier is not None}")
            
            # Test notification on startup
            if self.notifier:
                QTimer.singleShot(2000, self.test_notification)
        
        # Start tracking automatically on launch
        QTimer.singleShot(500, self.start_tracking)  # Delay slightly to ensure UI is ready
        
        # Setup system tray icon for background running
        self.setup_system_tray()
    
    def init_ui(self):
        self.setWindowTitle("Puthu Tracker - Advanced Screen Time Analytics")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Set window icon
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # Apply global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F2F5;
            }
            QTabWidget::pane {
                border: none;
                background-color: #F0F2F5;
            }
            QTabBar::tab {
                background-color: #E5E5EA;
                padding: 15px 28px;
                margin-right: 3px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: 600;
                font-size: 15px;
                color: #1C1C1E;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007AFF;
                font-weight: 700;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(0)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Main tabs
        self.tabs = QTabWidget()
        
        # Analytics tab
        self.analytics_widget = AnalyticsWidget(self.db_manager, theme_manager=self.theme_manager)
        self.tabs.addTab(self.analytics_widget, "📊 Analytics")
        
        # History tab
        self.history_widget = HistoryWidget(self.db_manager, theme_manager=self.theme_manager, category_manager=self.category_manager)
        self.tabs.addTab(self.history_widget, "📋 History")
        
        # Goals & Limits tab
        if GOALS_FEATURE and self.goals_manager:
            try:
                self.goals_widget = GoalsWidget(self.db_manager, self.goals_manager, theme_manager=self.theme_manager, notifier=self.notifier)
                self.tabs.addTab(self.goals_widget, "🎯 Goals && Limits")
                print("Goals widget loaded with notifier")
            except Exception as e:
                print(f"Error loading Goals widget: {e}")
        
        # Productivity tab (if available)
        if ENHANCED_FEATURES and ProductivityWidget:
            try:
                self.productivity_widget = ProductivityWidget(self.db_manager, theme_manager=self.theme_manager, category_manager=self.category_manager)
                self.tabs.addTab(self.productivity_widget, "🎯 Productivity")
                # Connect category changes to productivity update
                self.category_manager.categories_updated.connect(self.productivity_widget.update_productivity_data)
            except Exception as e:
                print(f"Error loading Productivity widget: {e}")
        
        # Session Reminders tab
        if REMINDERS_FEATURE and RemindersWidget:
            try:
                self.reminders_widget = RemindersWidget(theme_manager=self.theme_manager, notifier=self.notifier)
                self.tabs.addTab(self.reminders_widget, "⏰ Reminders")
                print("Reminders widget loaded with notifier")
            except Exception as e:
                print(f"Error loading Reminders widget: {e}")
        
        # Advanced Analytics tab
        if ADVANCED_ANALYTICS and AdvancedAnalyticsWidget:
            try:
                self.advanced_analytics_widget = AdvancedAnalyticsWidget(self.db_manager, theme_manager=self.theme_manager)
                self.tabs.addTab(self.advanced_analytics_widget, "📊 Insights")
            except Exception as e:
                print(f"Error loading Advanced Analytics widget: {e}")
        
        # Export & Backup tab
        if EXPORT_BACKUP_FEATURE and ExportBackupWidget:
            try:
                self.export_backup_widget = ExportBackupWidget(self.db_manager, theme_manager=self.theme_manager)
                self.tabs.addTab(self.export_backup_widget, "📤 Export && Backup")
            except Exception as e:
                print(f"Error loading Export & Backup widget: {e}")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.create_status_bar()
    
    def create_control_panel(self):
        """Create enhanced control panel"""
        self.control_panel = QFrame()
        self.control_panel.setFixedHeight(120)  # Halved from 240 to 120
        self.apply_control_panel_styling()
        panel = self.control_panel
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(30, 25, 30, 25)  # Halved margins
        layout.setSpacing(20)  # Halved spacing between sections
        
        # Status section - simple and clear  
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        self.status_indicator = QLabel("●")
        self.apply_status_indicator_styling()
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.status_indicator.setFixedSize(40, 40)  # Reduced size
        
        self.status_title = QLabel("Tracking Stopped")
        self.apply_status_title_styling()
        self.status_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_title)
        status_layout.addStretch()
        
        # Buttons - align tracking button with theme toggle on the right
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        button_layout.addStretch()  # Push buttons to the right
        
        self.tracking_button = ModernButton("🎬 Start Tracking", primary=True)
        self.tracking_button.setFixedHeight(50)
        self.tracking_button.setMinimumWidth(220)  # Increased width to fit text fully
        self.tracking_button.clicked.connect(self.toggle_tracking)
        
        button_layout.addWidget(self.tracking_button)
        
        # Add theme toggle button
        self.theme_toggle = ThemeToggleButton(self)
        button_layout.addWidget(self.theme_toggle)
        
        layout.addLayout(status_layout)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        return panel
    
    def apply_control_panel_styling(self):
        """Apply control panel styling based on theme"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            self.control_panel.setStyleSheet("""
                QFrame {
                    background-color: #1C1C1E;
                    border: 1px solid #38383A;
                    border-radius: 12px;
                    margin-bottom: 25px;
                }
            """)
        else:
            self.control_panel.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #E5E5EA;
                    border-radius: 12px;
                    margin-bottom: 25px;
                }
            """)
    
    def apply_status_indicator_styling(self):
        """Apply styling to status indicator based on current tracking state"""
        # Use green if tracking, red if stopped
        color = '#34C759' if self.tracker.tracking else '#FF3B30'
        self.status_indicator.setStyleSheet(f"""
            color: {color};
            font-size: 32px;
            background-color: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
    
    def apply_status_title_styling(self):
        """Apply styling to status title"""
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#000000'
        self.status_title.setStyleSheet(f"""
            font-size: 26px;
            font-weight: 900;
            color: {text_color};
            background-color: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
    
    def create_status_bar(self):
        """Create enhanced status bar"""
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #F8F8F8;
                border-top: 1px solid #E5E5EA;
                color: #3C3C43;
                font-size: 12px;
                padding: 5px;
            }
        """)
        
        # Add permanent widgets
        self.session_label = QLabel("Ready to track")
        version_text = "Puthu Tracker v2.0"
        if ENHANCED_FEATURES:
            version_text += " (Enhanced)"
        else:
            version_text += " (Basic)"
        self.version_label = QLabel(version_text)
        
        status_bar.addWidget(self.session_label)
        status_bar.addPermanentWidget(self.version_label)
    
    def apply_theme(self, dark_mode):
        """Apply dark or light theme to the application"""
        # Update theme manager state
        self.theme_manager.dark_mode = dark_mode
        
        if dark_mode:
            # Enhanced Dark theme with true black background
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #000000;
                }
                QTabWidget::pane {
                    border: none;
                    background-color: #000000;
                }
                QTabBar::tab {
                    background-color: #2C2C2E;
                    padding: 15px 28px;
                    margin-right: 3px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    font-weight: 600;
                    font-size: 15px;
                    color: #98989D;
                    border: 1px solid #48484A;
                }
                QTabBar::tab:selected {
                    background-color: #1C1C1E;
                    color: #0A84FF;
                    font-weight: 700;
                    border-bottom: 2px solid #0A84FF;
                }
                QTabBar::tab:hover {
                    background-color: #3A3A3C;
                    color: #FFFFFF;
                }
            """)
            
            # Update status bar for enhanced dark mode
            self.statusBar().setStyleSheet("""
                QStatusBar {
                    background-color: #1C1C1E;
                    border-top: 1px solid #48484A;
                    color: #98989D;
                    font-size: 12px;
                    padding: 5px;
                }
            """)
            
            # Update status title color for dark mode
            self.status_title.setStyleSheet("""
                font-size: 26px; 
                font-weight: 900; 
                color: #FFFFFF;
                background-color: transparent;
                margin: 0px;
                padding: 0px;
                font-family: 'Arial Black', 'Arial', sans-serif;
            """)
        else:
            # Light theme (original)
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F0F2F5;
                }
                QTabWidget::pane {
                    border: none;
                    background-color: #F0F2F5;
                }
                QTabBar::tab {
                    background-color: #E5E5EA;
                    padding: 15px 28px;
                    margin-right: 3px;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    font-weight: 600;
                    font-size: 15px;
                    color: #1C1C1E;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    color: #007AFF;
                    font-weight: 700;
                }
            """)
            
            # Update status bar for light mode
            self.statusBar().setStyleSheet("""
                QStatusBar {
                    background-color: #F8F8F8;
                    border-top: 1px solid #E5E5EA;
                    color: #3C3C43;
                    font-size: 12px;
                    padding: 5px;
                }
            """)
            
            # Update status title color for light mode
            self.status_title.setStyleSheet("""
                font-size: 26px; 
                font-weight: 900; 
                color: #000000;
                background-color: transparent;
                margin: 0px;
                padding: 0px;
                font-family: 'Arial Black', 'Arial', sans-serif;
            """)
        
        # Update analytics widget theme
        if hasattr(self, 'analytics_widget'):
            self.analytics_widget.update_theme()
        
        # Update history widget theme
        if hasattr(self, 'history_widget'):
            self.history_widget.update_theme()
        
        # Update productivity widget theme
        if hasattr(self, 'productivity_widget') and hasattr(self.productivity_widget, 'update_theme'):
            self.productivity_widget.theme_manager = self.theme_manager
            self.productivity_widget.update_theme()
        
        # Update reminders widget theme
        if hasattr(self, 'reminders_widget') and hasattr(self.reminders_widget, 'update_theme'):
            self.reminders_widget.update_theme()
        
        # Update advanced analytics widget theme
        if hasattr(self, 'advanced_analytics_widget') and hasattr(self.advanced_analytics_widget, 'update_theme'):
            self.advanced_analytics_widget.update_theme()
        
        # Update goals widget theme
        if hasattr(self, 'goals_widget') and hasattr(self.goals_widget, 'update_theme'):
            self.goals_widget.update_theme()
        
        # Update export & backup widget theme
        if hasattr(self, 'export_backup_widget') and hasattr(self.export_backup_widget, 'update_theme'):
            self.export_backup_widget.update_theme()
        
        # Update control panel styling
        if hasattr(self, 'control_panel'):
            self.apply_control_panel_styling()
        
        # Update status indicator and title
        if hasattr(self, 'status_indicator'):
            self.apply_status_indicator_styling()
        if hasattr(self, 'status_title'):
            self.apply_status_title_styling()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.tracker.data_updated.connect(self.on_data_updated)
        self.tracker.idle_status_changed.connect(self.on_idle_status_changed)
    
    def toggle_tracking(self):
        """Toggle between start and stop tracking"""
        if self.tracker.tracking:
            self.stop_tracking()
        else:
            self.start_tracking()
    
    def start_tracking(self):
        """Start activity tracking"""
        self.tracker.start_tracking()
        
        # Update button to show Stop state
        self.tracking_button.setText("⏹️ Stop Tracking")
        self.tracking_button.primary = False
        self.tracking_button.apply_style()
        
        # Update status indicator with green color
        self.status_indicator.setStyleSheet("""
            color: #34C759;
            font-size: 32px;
            background-color: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
        self.status_title.setText("Tracking Active")
        
        self.session_label.setText(f"Session started at {datetime.now().strftime('%H:%M')}")
    
    def stop_tracking(self):
        """Stop activity tracking"""
        self.tracker.stop_tracking()
        
        # Update button to show Start state
        self.tracking_button.setText("🎬 Start Tracking")
        self.tracking_button.primary = True
        self.tracking_button.apply_style()
        
        # Update status indicator with red color
        self.status_indicator.setStyleSheet("""
            color: #FF3B30;
            font-size: 32px;
            background-color: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        """)
        self.status_title.setText("Tracking Stopped")
        
        self.session_label.setText(f"Session ended at {datetime.now().strftime('%H:%M')}")
    
    def on_data_updated(self):
        """Handle data updates"""
        self.analytics_widget.update_analytics()
        self.history_widget.update_history()
        
        # Update goals widget if available
        if hasattr(self, 'goals_widget'):
            try:
                self.goals_widget.update_progress()
            except:
                pass
        
        if hasattr(self, 'productivity_widget'):
            try:
                self.productivity_widget.update_productivity_data()
            except:
                pass
    
    def on_idle_status_changed(self, is_idle):
        """Handle idle status changes and update UI"""
        if is_idle:
            # System went idle - update status
            self.status_indicator.setStyleSheet("""
                color: #FF9500;
                font-size: 32px;
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            """)
            self.status_title.setText("Tracking Paused (Idle)")
            self.session_label.setText("System is idle - tracking paused automatically")
            
            # Show notification if notifier is available
            if hasattr(self, 'notifier') and self.notifier:
                self.notifier.info(
                    "Tracking Paused 💤",
                    "System is idle. Tracking will resume when you return.",
                    duration=4000
                )
        else:
            # System became active again - restore tracking status
            if self.tracker.tracking:
                self.status_indicator.setStyleSheet("""
                    color: #34C759;
                    font-size: 32px;
                    background-color: transparent;
                    border: none;
                    margin: 0px;
                    padding: 0px;
                """)
                self.status_title.setText("Tracking Active")
                self.session_label.setText(f"Tracking resumed at {datetime.now().strftime('%H:%M')}")
                
                # Show notification if notifier is available
                if hasattr(self, 'notifier') and self.notifier:
                    self.notifier.success(
                        "Welcome Back! 👋",
                        "Tracking has been resumed automatically.",
                        duration=3000
                    )
    
    def periodic_update(self):
        """Periodic update of analytics"""
        if not self.tracker.tracking:
            return
        
        self.analytics_widget.update_analytics()
        current_time = datetime.now().strftime('%H:%M:%S')
        self.session_label.setText(f"Tracking... (Last update: {current_time})")
    
    def test_notification(self):
        """Test notification system"""
        print("Testing notification system...")
        try:
            if self.notifier:
                self.notifier.info(
                    "Puthu Tracker Started! 🎉",
                    "Notification system is active. You'll receive alerts when limits are reached.",
                    duration=5000
                )
                print("Test notification sent successfully!")
            else:
                print("ERROR: Notifier is None!")
        except Exception as e:
            print(f"ERROR testing notification: {e}")
    
    def check_goals(self):
        """Check goals and show beautiful toast notifications"""
        if not self.goals_manager or not self.goals_manager.goals['notifications_enabled']:
            print("Goals check skipped: manager not available or notifications disabled")
            return
        
        warnings = self.goals_manager.check_limits(self.db_manager)
        print(f"Goals check completed - found {len(warnings)} warnings")
        
        for warning in warnings:
            # Only show each warning once per hour
            warning_id = f"{warning['type']}_{warning.get('app', 'daily')}"
            
            if self.goals_manager.should_notify(warning_id):
                print(f"Showing notification: {warning['type']} - {warning['message']}")
                # Use toast notifications if available
                if self.notifier:
                    if warning['severity'] == 'critical':
                        self.notifier.error(
                            "Limit Exceeded! ⚠️",
                            warning['message'],
                            duration=7000,
                            action_text="View Goals",
                            action_callback=lambda: self.tabs.setCurrentWidget(self.goals_widget) if hasattr(self, 'goals_widget') else None
                        )
                    elif warning['severity'] == 'warning':
                        self.notifier.warning(
                            "Approaching Limit",
                            warning['message'],
                            duration=6000,
                            action_text="View Stats",
                            action_callback=lambda: self.tabs.setCurrentWidget(self.analytics_widget)
                        )
                    else:
                        self.notifier.info(
                            "Usage Update",
                            warning['message'],
                            duration=5000
                        )
                    print("Toast notification sent!")
                else:
                    print("No notifier available - using fallback")
                    # Fallback to old system
                    if warning['severity'] == 'critical':
                        QMessageBox.warning(self, "Limit Exceeded", warning['message'])
                    elif warning['severity'] == 'warning':
                        self.statusBar().showMessage(warning['message'], 10000)
            else:
                print(f"Notification already sent for: {warning_id}")
    
    def setup_system_tray(self):
        """Setup system tray icon for background running"""
        # Create system tray icon
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Puthu Tracker - Running")
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide window action
        show_action = QAction("📊 Show Dashboard", self)
        show_action.triggered.connect(self.show_from_tray)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Start/Stop tracking actions
        self.tray_tracking_action = QAction("⏸️ Pause Tracking", self)
        self.tray_tracking_action.triggered.connect(self.toggle_tracking_from_tray)
        tray_menu.addAction(self.tray_tracking_action)
        
        tray_menu.addSeparator()
        
        # Quick stats action
        stats_action = QAction("📈 Quick Stats", self)
        stats_action.triggered.connect(self.show_tray_stats)
        tray_menu.addAction(stats_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.exit_from_tray)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Double-click to show window
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        print("✅ System tray icon initialized")
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()
    
    def show_from_tray(self):
        """Show the main window from tray"""
        self.show()
        self.activateWindow()
        self.raise_()
        print("Window shown from tray")
    
    def toggle_tracking_from_tray(self):
        """Toggle tracking from tray icon"""
        self.toggle_tracking()
        
        # Update tray icon tooltip and action text
        if self.tracker.tracking:
            self.tray_tracking_action.setText("⏸️ Pause Tracking")
            self.tray_icon.setToolTip("Puthu Tracker - Running")
        else:
            self.tray_tracking_action.setText("▶️ Resume Tracking")
            self.tray_icon.setToolTip("Puthu Tracker - Paused")
    
    def show_tray_stats(self):
        """Show quick statistics in tray notification"""
        # Get today's data
        today_data = self.db_manager.get_app_usage_by_date()
        
        if today_data:
            total_seconds = sum(duration for _, duration in today_data)
            total_hours = total_seconds // 3600
            total_minutes = (total_seconds % 3600) // 60
            
            apps_count = len(today_data)
            most_used_app = today_data[0][0] if today_data else "None"
            
            message = (
                f"📊 Today's Stats:\n\n"
                f"⏱️ Total Time: {total_hours}h {total_minutes}m\n"
                f"📱 Apps Used: {apps_count}\n"
                f"🏆 Most Used: {most_used_app}"
            )
        else:
            message = "No tracking data yet today.\nStart using your computer to see stats!"
        
        # Use toast notification if available
        if self.notifier:
            self.notifier.info(
                "📊 Today's Stats",
                message.replace("\n", " "),
                duration=6000
            )
        else:
            # Fallback to system tray notification
            self.tray_icon.showMessage(
                "Puthu Tracker Stats",
                message,
                QSystemTrayIcon.MessageIcon.Information,
                5000
            )
    
    def exit_from_tray(self):
        """Exit the application from tray"""
        # Stop tracking
        if self.tracker.tracking:
            self.tracker.stop_tracking()
        
        # Hide tray icon
        self.tray_icon.hide()
        
        # Quit application
        QApplication.quit()
    
    def closeEvent(self, event):
        """Handle application close - minimize to tray instead of exiting"""
        # Don't close the app, just minimize to tray
        event.ignore()
        self.hide()
        
        # Show notification that app is still running
        if hasattr(self, 'notifier') and self.notifier:
            self.notifier.info(
                "Still Running 👋",
                "Puthu Tracker is running in the background. Double-click the tray icon to show.",
                duration=4000
            )
        else:
            # Fallback to system tray notification
            self.tray_icon.showMessage(
                "Puthu Tracker",
                "Running in background. Double-click tray icon to show.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        
        print("Window minimized to tray")

def main():
    # Check for required dependencies
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError as e:
        print(f"Required dependency missing: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Puthu Tracker")
    app.setOrganizationName("Puthu Software")
    
    # Set application icon
    app.setWindowIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        # Center window on screen
        screen = app.primaryScreen().geometry()
        window.move((screen.width() - window.width()) // 2, 
                    (screen.height() - window.height()) // 2)
        
        # Show welcome message for first-time users
        db_path = Path(__file__).parent / "tracking_data.db"
        if not db_path.exists():
            # Use toast notification for welcome message
            if hasattr(window, 'notifier') and window.notifier:
                QTimer.singleShot(1000, lambda: window.notifier.success(
                    "Welcome to Puthu Tracker! 🎉",
                    "Click 'Start Tracking' to begin monitoring your screen time!",
                    duration=8000
                ))
            else:
                # Fallback to QMessageBox
                QMessageBox.information(
                    window,
                    "Welcome to Puthu Tracker!",
                    "🎉 Welcome to Puthu Tracker!\n\n"
                    "This application will help you monitor and analyze your screen time.\n\n"
                    "Features:\n"
                    "• Real-time application tracking\n"
                    "• Beautiful analytics dashboard\n"
                    "• Historical data with charts\n"
                    "• Modern Apple-inspired interface\n\n"
                    "Click 'Start Tracking' to begin monitoring your screen time!"
                )
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        QMessageBox.critical(None, "Error", f"Failed to start Puthu Tracker:\n\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
