#!/usr/bin/env python3
"""
Goals and Limits Module for Puthu Tracker
Features:
- Daily screen time goals
- App-specific time limits
- Visual progress tracking
- Notifications when approaching limits
"""

import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class GoalsManager:
    """Manages user goals and limits"""
    
    def __init__(self):
        self.goals_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'goals_settings.json')
        self.goals = self.load_goals()
        self.notifications_sent = set()  # Track sent notifications
    
    def load_goals(self):
        """Load goals from JSON file"""
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return self.get_default_goals()
    
    def get_default_goals(self):
        """Return default goals"""
        return {
            'daily_screen_time_goal': 8 * 3600,  # 8 hours in seconds
            'daily_screen_time_enabled': True,
            'daily_productive_time_goal': 4 * 3600,  # 4 hours in seconds
            'daily_productive_time_enabled': False,
            'app_limits': {},  # {'app_name': limit_in_seconds}
            'app_limits_enabled': True,
            'notification_threshold': 0.8,  # Notify at 80% of limit
            'notifications_enabled': True
        }
    
    def save_goals(self):
        """Save goals to JSON file"""
        try:
            with open(self.goals_file, 'w') as f:
                json.dump(self.goals, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving goals: {e}")
            return False
    
    def set_daily_screen_time_goal(self, hours):
        """Set daily screen time goal in hours"""
        self.goals['daily_screen_time_goal'] = int(hours * 3600)
        self.save_goals()
    
    def set_app_limit(self, app_name, hours):
        """Set time limit for specific app"""
        self.goals['app_limits'][app_name] = int(hours * 3600)
        self.save_goals()
    
    def remove_app_limit(self, app_name):
        """Remove time limit for specific app"""
        if app_name in self.goals['app_limits']:
            del self.goals['app_limits'][app_name]
            self.save_goals()
    
    def check_limits(self, db_manager, date=None):
        """Check if any limits are being approached or exceeded"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        warnings = []
        
        # Check daily screen time
        if self.goals['daily_screen_time_enabled']:
            app_data = db_manager.get_app_usage_by_date(date)
            total_time = sum(duration for _, duration in app_data)
            limit = self.goals['daily_screen_time_goal']
            
            progress = total_time / limit if limit > 0 else 0
            
            if progress >= 1.0:
                warnings.append({
                    'type': 'daily_limit_exceeded',
                    'message': f'Daily screen time limit exceeded! ({self._format_time(total_time)} / {self._format_time(limit)})',
                    'severity': 'critical',
                    'progress': progress
                })
            elif progress >= self.goals['notification_threshold']:
                warnings.append({
                    'type': 'daily_limit_warning',
                    'message': f'Approaching daily screen time limit ({int(progress*100)}% used)',
                    'severity': 'warning',
                    'progress': progress
                })
        
        # Check app-specific limits
        if self.goals['app_limits_enabled']:
            app_data = db_manager.get_app_usage_by_date(date)
            for app_name, duration in app_data:
                if app_name in self.goals['app_limits']:
                    limit = self.goals['app_limits'][app_name]
                    progress = duration / limit if limit > 0 else 0
                    
                    if progress >= 1.0:
                        warnings.append({
                            'type': 'app_limit_exceeded',
                            'app': app_name,
                            'message': f'{app_name}: Time limit exceeded! ({self._format_time(duration)} / {self._format_time(limit)})',
                            'severity': 'critical',
                            'progress': progress
                        })
                    elif progress >= self.goals['notification_threshold']:
                        warnings.append({
                            'type': 'app_limit_warning',
                            'app': app_name,
                            'message': f'{app_name}: Approaching time limit ({int(progress*100)}% used)',
                            'severity': 'warning',
                            'progress': progress
                        })
        
        return warnings
    
    def _format_time(self, seconds):
        """Format seconds to readable time"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def should_notify(self, warning_id):
        """Check if notification should be sent (avoid spam)"""
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        notification_key = f"{warning_id}_{current_hour}"
        
        if notification_key in self.notifications_sent:
            return False
        
        self.notifications_sent.add(notification_key)
        return True
    
    def reset_notifications(self):
        """Reset notification tracking (call daily)"""
        self.notifications_sent.clear()

class GoalsWidget(QWidget):
    """Widget for Goals and Limits settings"""
    
    def __init__(self, db_manager, goals_manager, theme_manager=None, notifier=None):
        super().__init__()
        self.db_manager = db_manager
        self.goals_manager = goals_manager
        self.theme_manager = theme_manager
        self.notifier = notifier  # Store notifier reference
        self.init_ui()
        print(f"GoalsWidget initialized with notifier: {self.notifier is not None}")
    
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Apply scroll area styling
        self.apply_scroll_styling(scroll)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 15, 0)  # Right margin for scrollbar
        
        # Title
        self.title_label = QLabel("🎯 Goals & Limits")
        self.apply_title_styling()
        layout.addWidget(self.title_label)
        
        # Daily screen time goal section
        self.daily_goal_card = self.create_daily_goal_card()
        layout.addWidget(self.daily_goal_card)
        
        # App-specific limits section
        self.app_limits_card = self.create_app_limits_card()
        layout.addWidget(self.app_limits_card)
        
        # Progress overview
        self.progress_card = self.create_progress_card()
        layout.addWidget(self.progress_card)
        
        layout.addStretch()
        
        # Set content widget to scroll area
        scroll.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
    
    def apply_title_styling(self):
        """Apply theme-aware title styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = theme.get('text_primary', '#1C1C1E')
        
        self.title_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {text_color};
            background-color: transparent;
            margin-bottom: 10px;
        """)
    
    def apply_scroll_styling(self, scroll):
        """Apply scroll area styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #1C1C1E;
                    width: 12px;
                    border-radius: 6px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #48484A;
                    border-radius: 6px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #007AFF;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """)
        else:
            scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #F0F2F5;
                    width: 12px;
                    border-radius: 6px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #D1D1D6;
                    border-radius: 6px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #007AFF;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """)
    
    def apply_card_styling(self, card):
        """Apply theme-aware card styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        # Use proper dark theme background
        bg_color = '#1C1C1E' if is_dark else '#FFFFFF'
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: none;
                border-radius: 12px;
            }}
        """)
    
    def apply_header_label_styling(self, label):
        """Apply header label styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {text_color};
            background-color: transparent;
        """)
    
    def apply_description_styling(self, label):
        """Apply description label styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_muted', '#8E8E93')
        label.setStyleSheet(f"""
            color: {text_color};
            font-size: 13px;
            background-color: transparent;
        """)
    
    def apply_toggle_styling(self, toggle):
        """Apply toggle switch styling"""
        toggle.setStyleSheet("""
            QCheckBox::indicator {
                width: 50px;
                height: 28px;
                border-radius: 14px;
                background-color: #E5E5EA;
            }
            QCheckBox::indicator:checked {
                background-color: #34C759;
            }
        """)
    
    def apply_spinbox_styling(self, spinbox):
        """Apply spinbox styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #2C2C2E;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 15px;
                    font-weight: 600;
                    color: white;
                }
                QDoubleSpinBox:focus {
                    border: 2px solid #007AFF;
                }
            """)
        else:
            spinbox.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #F8F9FA;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 15px;
                    font-weight: 600;
                    color: #1C1C1E;
                }
                QDoubleSpinBox:focus {
                    border: 2px solid #007AFF;
                }
            """)
    
    def apply_primary_button_styling(self, button):
        """Apply primary button styling"""
        button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
    
    def apply_success_button_styling(self, button):
        """Apply success/green button styling"""
        button.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #28A745;
            }
            QPushButton:pressed {
                background-color: #208B3A;
            }
        """)
    
    def apply_secondary_button_styling(self, button):
        """Apply secondary button styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2C2C2E;
                    color: #007AFF;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #3A3A3C;
                }
                QPushButton:pressed {
                    background-color: #48484A;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #F2F2F7;
                    color: #007AFF;
                    border: none;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #E5E5EA;
                }
                QPushButton:pressed {
                    background-color: #D1D1D6;
                }
            """)
    
    def apply_combobox_styling(self, combobox):
        """Apply combobox styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            combobox.setStyleSheet("""
                QComboBox {
                    background-color: #2C2C2E;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 15px;
                    color: white;
                }
                QComboBox:focus {
                    border: 2px solid #007AFF;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }
                QComboBox::down-arrow {
                    width: 0;
                    height: 0;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 6px solid #8E8E93;
                }
                QComboBox QAbstractItemView {
                    background-color: #2C2C2E;
                    color: white;
                    border: 1px solid #48484A;
                    border-radius: 8px;
                    selection-background-color: #007AFF;
                    outline: none;
                }
            """)
        else:
            combobox.setStyleSheet("""
                QComboBox {
                    background-color: #F8F9FA;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 15px;
                    color: #1C1C1E;
                }
                QComboBox:focus {
                    border: 2px solid #007AFF;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }
                QComboBox::down-arrow {
                    width: 0;
                    height: 0;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 6px solid #8E8E93;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #1C1C1E;
                    border: 1px solid #E5E5EA;
                    border-radius: 8px;
                    selection-background-color: #007AFF;
                    outline: none;
                }
            """)
    
    def apply_section_label_styling(self, label):
        """Apply section label styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {text_color};
            margin-top: 10px;
            background-color: transparent;
        """)
    
    def apply_list_styling(self, list_widget):
        """Apply list widget styling"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            list_widget.setStyleSheet("""
                QListWidget {
                    background-color: #2C2C2E;
                    border: none;
                    border-radius: 8px;
                    padding: 8px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-radius: 6px;
                    margin: 2px 0;
                }
                QListWidget::item:hover {
                    background-color: #3A3A3C;
                }
            """)
        else:
            list_widget.setStyleSheet("""
                QListWidget {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 0;
                }
                QListWidget::item {
                    padding: 8px;
                    border-radius: 6px;
                    margin: 2px 0;
                    background-color: #F8F9FA;
                }
                QListWidget::item:hover {
                    background-color: #E5E5EA;
                }
            """)
    
    def create_daily_goal_card(self):
        """Create daily screen time goal card"""
        card = QFrame()
        self.apply_card_styling(card)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(18)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)
        
        # Header only (no toggle)
        self.daily_goal_header = QLabel("⏰  Daily Screen Time Goal")
        self.apply_header_label_styling(self.daily_goal_header)
        layout.addWidget(self.daily_goal_header)
        
        # Store toggle state but don't show it (always enabled)
        self.goals_manager.goals['daily_screen_time_enabled'] = True
        self.goals_manager.save_goals()
        
        # Input section with better alignment
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        
        self.daily_goal_spinbox = QDoubleSpinBox()
        self.daily_goal_spinbox.setRange(0.5, 24.0)
        self.daily_goal_spinbox.setSingleStep(0.5)
        self.daily_goal_spinbox.setValue(self.goals_manager.goals['daily_screen_time_goal'] / 3600)
        self.daily_goal_spinbox.setSuffix(" hours")
        self.daily_goal_spinbox.setFixedWidth(180)
        self.daily_goal_spinbox.setFixedHeight(44)
        self.apply_spinbox_styling(self.daily_goal_spinbox)
        
        save_btn = QPushButton("Save Goal")
        save_btn.setFixedHeight(44)
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self.save_daily_goal)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_primary_button_styling(save_btn)
        
        input_layout.addWidget(self.daily_goal_spinbox)
        input_layout.addWidget(save_btn)
        input_layout.addStretch()
        
        layout.addLayout(input_layout)
        
        card.adjustSize()
        return card
    
    def create_app_limits_card(self):
        """Create app-specific limits card"""
        card = QFrame()
        self.apply_card_styling(card)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(18)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)
        
        # Header only (no toggle)
        self.app_limits_header = QLabel("📱  App-Specific Limits")
        self.apply_header_label_styling(self.app_limits_header)
        layout.addWidget(self.app_limits_header)
        
        # Store toggle state but don't show it (always enabled)
        self.goals_manager.goals['app_limits_enabled'] = True
        self.goals_manager.save_goals()
        
        # Add new limit section
        add_layout = QHBoxLayout()
        add_layout.setSpacing(12)
        
        self.app_combo = QComboBox()
        self.app_combo.setFixedWidth(200)
        self.app_combo.setFixedHeight(44)
        self.populate_app_combo()
        self.apply_combobox_styling(self.app_combo)
        
        self.app_limit_spinbox = QDoubleSpinBox()
        self.app_limit_spinbox.setRange(0.1, 12.0)
        self.app_limit_spinbox.setSingleStep(0.5)
        self.app_limit_spinbox.setValue(2.0)
        self.app_limit_spinbox.setSuffix(" hours")
        self.app_limit_spinbox.setFixedWidth(180)
        self.app_limit_spinbox.setFixedHeight(44)
        self.apply_spinbox_styling(self.app_limit_spinbox)
        
        add_btn = QPushButton("+ Add Limit")
        add_btn.setFixedHeight(44)
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self.add_app_limit)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_success_button_styling(add_btn)
        
        add_layout.addWidget(self.app_combo)
        add_layout.addWidget(self.app_limit_spinbox)
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        
        layout.addLayout(add_layout)
        
        # Current limits list - always add but may be hidden
        limits_label = QLabel("Current Limits:")
        self.apply_section_label_styling(limits_label)
        self.limits_label = limits_label  # Store reference
        
        self.limits_list_widget = QListWidget()
        self.limits_list_widget.setMinimumHeight(0)
        self.limits_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.apply_list_styling(self.limits_list_widget)
        
        # Add both to layout
        layout.addWidget(limits_label)
        layout.addWidget(self.limits_list_widget)
        
        # Update to show/hide based on content
        self.update_limits_list()
        
        card.adjustSize()
        return card
    
    def create_progress_card(self):
        """Create progress overview card"""
        card = QFrame()
        self.apply_card_styling(card)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(18)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        self.progress_header = QLabel("📊  Today's Progress")
        self.apply_header_label_styling(self.progress_header)
        
        header_layout.addWidget(self.progress_header)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.update_progress)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_secondary_button_styling(refresh_btn)
        
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        # Progress containers
        self.daily_progress_layout = QVBoxLayout()
        self.daily_progress_layout.setSpacing(12)
        layout.addLayout(self.daily_progress_layout)
        
        self.app_progress_layout = QVBoxLayout()
        self.app_progress_layout.setSpacing(12)
        layout.addLayout(self.app_progress_layout)
        
        self.update_progress()
        
        card.adjustSize()
        return card
    
    def populate_app_combo(self):
        """Populate app dropdown with tracked apps"""
        apps = self.db_manager.get_all_apps()
        self.app_combo.clear()
        self.app_combo.addItems(apps)
    
    def toggle_daily_goal(self, state):
        """Toggle daily goal on/off"""
        self.goals_manager.goals['daily_screen_time_enabled'] = (state == Qt.CheckState.Checked.value)
        self.goals_manager.save_goals()
    
    def toggle_app_limits(self, state):
        """Toggle app limits on/off"""
        self.goals_manager.goals['app_limits_enabled'] = (state == Qt.CheckState.Checked.value)
        self.goals_manager.save_goals()
    
    def update_daily_goal(self, value):
        """Update daily goal value"""
        pass  # Updated when save button is clicked
    
    def save_daily_goal(self):
        """Save daily goal"""
        hours = self.daily_goal_spinbox.value()
        self.goals_manager.set_daily_screen_time_goal(hours)
        
        # Use toast notification if available
        if self.notifier:
            self.notifier.success(
                "Goal Saved! ✅",
                f"Daily screen time goal set to {hours} hours.",
                duration=4000
            )
            print(f"Toast: Daily goal set to {hours} hours")
        else:
            # Fallback to QMessageBox
            QMessageBox.information(self, "Success", f"Daily goal set to {hours} hours!")
        
        self.update_progress()
    
    def add_app_limit(self):
        """Add app-specific limit"""
        app_name = self.app_combo.currentText()
        hours = self.app_limit_spinbox.value()
        
        if app_name:
            self.goals_manager.set_app_limit(app_name, hours)
            self.update_limits_list()
            self.update_progress()
            
            # Use toast notification if available
            if self.notifier:
                self.notifier.success(
                    "Limit Added! ✅",
                    f"Time limit set for {app_name}: {hours} hours/day",
                    duration=4000
                )
                print(f"Toast: Limit set for {app_name}")
            else:
                # Fallback to QMessageBox
                QMessageBox.information(self, "Success", f"Limit set for {app_name}: {hours} hours/day")
    
    def update_limits_list(self):
        """Update the list of current limits"""
        self.limits_list_widget.clear()
        
        # Show/hide the list widget and label based on whether there are limits
        if not self.goals_manager.goals['app_limits']:
            self.limits_list_widget.hide()
            if hasattr(self, 'limits_label'):
                self.limits_label.hide()
            return
        else:
            self.limits_list_widget.show()
            if hasattr(self, 'limits_label'):
                self.limits_label.show()
        
        for app_name, limit_seconds in self.goals_manager.goals['app_limits'].items():
            hours = limit_seconds / 3600
            item = QListWidgetItem(f"{app_name}: {hours:.1f} hours/day")
            
            # Add remove button
            widget = QWidget()
            widget.setStyleSheet("background-color: transparent;")
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 2, 10, 2)  # Reduced vertical padding
            layout.setSpacing(10)
            
            label = QLabel(f"{app_name}: {hours:.1f} hours/day")
            theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
            is_dark = self.theme_manager.dark_mode if self.theme_manager else False
            text_color = '#FFFFFF' if is_dark else '#1C1C1E'
            label.setStyleSheet(f"background-color: transparent; color: {text_color}; font-size: 14px; font-weight: 500;")
            
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedWidth(85)
            remove_btn.setFixedHeight(36)
            remove_btn.clicked.connect(lambda checked, app=app_name: self.remove_limit(app))
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #CC2E24;
                }
                QPushButton:pressed {
                    background-color: #A01E17;
                }
            """)
            
            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(remove_btn)
            
            # Set proper item height - increased by 15px
            item.setSizeHint(QSize(widget.sizeHint().width(), 57))
            self.limits_list_widget.addItem(item)
            self.limits_list_widget.setItemWidget(item, widget)
        
        # Adjust list height based on content
        item_count = self.limits_list_widget.count()
        if item_count > 0:
            item_height = self.limits_list_widget.sizeHintForRow(0)
            total_height = min(item_height * item_count + 20, 250)  # Max 250px
            self.limits_list_widget.setMinimumHeight(total_height)
            self.limits_list_widget.setMaximumHeight(total_height)
        
        # Force card to resize only if it exists
        if hasattr(self, 'app_limits_card'):
            self.app_limits_card.adjustSize()
            self.app_limits_card.updateGeometry()
    
    def remove_limit(self, app_name):
        """Remove app limit"""
        self.goals_manager.remove_app_limit(app_name)
        self.update_limits_list()
        self.update_progress()
    
    def update_progress(self):
        """Update progress bars"""
        # Clear existing progress bars
        for i in reversed(range(self.daily_progress_layout.count())): 
            self.daily_progress_layout.itemAt(i).widget().setParent(None)
        
        for i in reversed(range(self.app_progress_layout.count())): 
            self.app_progress_layout.itemAt(i).widget().setParent(None)
        
        date = datetime.now().strftime('%Y-%m-%d')
        app_data = self.db_manager.get_app_usage_by_date(date)
        
        # Daily progress
        if self.goals_manager.goals['daily_screen_time_enabled']:
            total_time = sum(duration for _, duration in app_data)
            limit = self.goals_manager.goals['daily_screen_time_goal']
            progress = (total_time / limit * 100) if limit > 0 else 0
            
            progress_bar = self.create_progress_bar(
                "Daily Screen Time",
                total_time,
                limit,
                min(progress, 100)
            )
            self.daily_progress_layout.addWidget(progress_bar)
        
        # App-specific progress
        if self.goals_manager.goals['app_limits_enabled']:
            for app_name, duration in app_data:
                if app_name in self.goals_manager.goals['app_limits']:
                    limit = self.goals_manager.goals['app_limits'][app_name]
                    progress = (duration / limit * 100) if limit > 0 else 0
                    
                    progress_bar = self.create_progress_bar(
                        app_name,
                        duration,
                        limit,
                        min(progress, 100)
                    )
                    self.app_progress_layout.addWidget(progress_bar)
    
    def create_progress_bar(self, label, current, limit, percentage):
        """Create a progress bar widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Get theme colors
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        muted_color = '#98989D' if is_dark else '#8E8E93'
        
        # Label
        info_layout = QHBoxLayout()
        name_label = QLabel(label)
        name_label.setStyleSheet(f"font-weight: 600; color: {text_color}; background-color: transparent;")
        
        current_hours = current / 3600
        limit_hours = limit / 3600
        time_label = QLabel(f"{current_hours:.1f}h / {limit_hours:.1f}h")
        time_label.setStyleSheet(f"color: {muted_color}; background-color: transparent;")
        
        info_layout.addWidget(name_label)
        info_layout.addStretch()
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        
        # Progress bar
        progress = QProgressBar()
        progress.setValue(int(percentage))
        progress.setTextVisible(True)
        progress.setFormat(f"{int(percentage)}%")
        progress.setFixedHeight(25)
        
        # Color based on progress
        if percentage >= 100:
            color = "#FF3B30"  # Red - exceeded
        elif percentage >= 80:
            color = "#FF9500"  # Orange - warning
        else:
            color = "#34C759"  # Green - good
        
        # Background color for progress bar
        bar_bg = "#2C2C2E" if is_dark else "#F2F2F7"
        bar_border = "#48484A" if is_dark else "#E5E5EA"
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {bar_border};
                border-radius: 8px;
                text-align: center;
                font-weight: 600;
                background-color: {bar_bg};
                color: {text_color};
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)
        
        layout.addWidget(progress)
        
        return widget
    
    def update_theme(self):
        """Update theme for all widgets"""
        # Update title
        self.apply_title_styling()
        
        # Update all header labels
        if hasattr(self, 'daily_goal_header'):
            self.apply_header_label_styling(self.daily_goal_header)
        if hasattr(self, 'app_limits_header'):
            self.apply_header_label_styling(self.app_limits_header)
        if hasattr(self, 'progress_header'):
            self.apply_header_label_styling(self.progress_header)
        if hasattr(self, 'limits_label'):
            self.apply_section_label_styling(self.limits_label)
        
        # Re-apply all card styling
        if hasattr(self, 'daily_goal_card'):
            self.apply_card_styling(self.daily_goal_card)
        if hasattr(self, 'app_limits_card'):
            self.apply_card_styling(self.app_limits_card)
        if hasattr(self, 'progress_card'):
            self.apply_card_styling(self.progress_card)
        
        # Re-apply all other styling
        if hasattr(self, 'daily_goal_spinbox'):
            self.apply_spinbox_styling(self.daily_goal_spinbox)
        if hasattr(self, 'app_combo'):
            self.apply_combobox_styling(self.app_combo)
        if hasattr(self, 'app_limit_spinbox'):
            self.apply_spinbox_styling(self.app_limit_spinbox)
        if hasattr(self, 'limits_list_widget'):
            self.apply_list_styling(self.limits_list_widget)
            self.update_limits_list()  # Re-render list items with new theme
        
        # Re-apply scroll area styling
        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            self.apply_scroll_styling(scroll_area)
        
        # Update progress with new colors
        self.update_progress()
        
        # Force update
        self.update()

# Export
__all__ = ['GoalsManager', 'GoalsWidget']
