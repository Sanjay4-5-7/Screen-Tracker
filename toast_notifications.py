#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern Toast Notification System for Puthu Tracker
Beautiful slide-in notifications with animations
"""

from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

class ToastNotification(QWidget):
    """Modern toast notification that slides in from the corner"""
    
    dismissed = pyqtSignal()
    action_clicked = pyqtSignal()
    
    def __init__(self, title, message, notification_type="info", 
                 duration=5000, action_text=None, parent=None):
        super().__init__(parent)
        
        self.notification_type = notification_type
        self.duration = duration
        self.action_text = action_text
        
        self.setup_ui(title, message)
        self.setup_animations()
        
    def setup_ui(self, title, message):
        """Setup the notification UI"""
        # Window flags for overlay
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Fixed size
        self.setFixedSize(400, 120)
        
        # Main container
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 400, 120)
        
        # Apply styling based on type
        self.apply_styling()
        
        # Layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Icon based on type
        self.icon_label = QLabel(self.get_icon())
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                min-width: 45px;
                max-width: 45px;
                min-height: 40px;
            }
        """)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.title_label, 1, alignment=Qt.AlignmentFlag.AlignVCenter)  # stretch factor 1
        header_layout.addStretch(0)  # No stretch after title
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 22px;
                font-weight: bold;
                padding-bottom: 2px;
                margin: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.close_btn.clicked.connect(self.dismiss)
        header_layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        layout.addLayout(header_layout)
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        layout.addWidget(self.message_label)
        
        # Action button (optional)
        if self.action_text:
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.action_btn = QPushButton(self.action_text)
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.25);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.35);
                }
            """)
            self.action_btn.clicked.connect(self.on_action_clicked)
            button_layout.addWidget(self.action_btn)
            
            layout.addLayout(button_layout)
        
        # Opacity effect for fade animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.container.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
    def apply_styling(self):
        """Apply color scheme based on notification type"""
        colors = {
            "info": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0EA5E9, stop:1 #0284C7);",
            "success": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10B981, stop:1 #059669);",
            "warning": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F59E0B, stop:1 #D97706);",
            "error": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EF4444, stop:1 #DC2626);",
            "goal": "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B5CF6, stop:1 #7C3AED);",
        }
        
        style = colors.get(self.notification_type, colors["info"])
        
        self.container.setStyleSheet(f"""
            QWidget {{
                {style}
                border-radius: 12px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def get_icon(self):
        """Get icon emoji based on notification type"""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "goal": "🎯",
        }
        return icons.get(self.notification_type, "ℹ️")
    
    def setup_animations(self):
        """Setup slide and fade animations"""
        # Slide animation
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(400)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out.finished.connect(self.close)
        
    def show_notification(self, screen_geometry):
        """Show notification with slide-in animation"""
        # Calculate start and end positions (bottom-right corner)
        margin = 20
        end_x = screen_geometry.width() - self.width() - margin
        end_y = screen_geometry.height() - self.height() - margin - 50  # Above taskbar
        
        start_x = screen_geometry.width()  # Start off-screen (right)
        start_y = end_y
        
        # Set start position
        self.move(start_x, start_y)
        
        # Configure animation
        self.slide_animation.setStartValue(QPoint(start_x, start_y))
        self.slide_animation.setEndValue(QPoint(end_x, end_y))
        
        # Show and animate
        self.show()
        self.slide_animation.start()
        self.fade_in.start()
        
        # Auto-dismiss timer
        if self.duration > 0:
            QTimer.singleShot(self.duration, self.dismiss)
    
    def dismiss(self):
        """Dismiss notification with fade out"""
        self.fade_out.start()
        self.dismissed.emit()
    
    def on_action_clicked(self):
        """Handle action button click"""
        self.action_clicked.emit()
        self.dismiss()


class NotificationManager:
    """Manages multiple toast notifications"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.active_notifications = []
        self.notification_spacing = 10
    
    def show_notification(self, title, message, notification_type="info", 
                         duration=5000, action_text=None, action_callback=None):
        """Show a toast notification"""
        # Create notification
        toast = ToastNotification(
            title=title,
            message=message,
            notification_type=notification_type,
            duration=duration,
            action_text=action_text,
            parent=self.parent
        )
        
        # Connect action callback
        if action_callback:
            toast.action_clicked.connect(action_callback)
        
        # Connect dismissed signal
        toast.dismissed.connect(lambda: self.remove_notification(toast))
        
        # Get screen geometry
        if self.parent:
            screen = self.parent.screen().geometry()
        else:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
        
        # Calculate position based on existing notifications
        y_offset = sum(n.height() + self.notification_spacing 
                      for n in self.active_notifications)
        
        # Adjust screen geometry for stacking
        adjusted_screen = screen
        if y_offset > 0:
            adjusted_screen.setHeight(screen.height() - y_offset)
        
        # Show notification
        toast.show_notification(adjusted_screen)
        self.active_notifications.append(toast)
        
        return toast
    
    def remove_notification(self, toast):
        """Remove notification from active list"""
        if toast in self.active_notifications:
            self.active_notifications.remove(toast)
            self.reposition_notifications()
    
    def reposition_notifications(self):
        """Reposition remaining notifications"""
        if not self.parent:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
        else:
            screen = self.parent.screen().geometry()
        
        margin = 20
        base_y = screen.height() - margin - 50
        
        for i, notification in enumerate(self.active_notifications):
            new_y = base_y - (i * (notification.height() + self.notification_spacing))
            new_x = screen.width() - notification.width() - margin
            
            # Animate to new position
            animation = QPropertyAnimation(notification, b"pos")
            animation.setDuration(300)
            animation.setEndValue(QPoint(new_x, new_y))
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
    
    def clear_all(self):
        """Dismiss all active notifications"""
        for toast in self.active_notifications[:]:
            toast.dismiss()
    
    # Convenience methods for different notification types
    
    def info(self, title, message, duration=5000, action_text=None, action_callback=None):
        """Show info notification"""
        return self.show_notification(title, message, "info", duration, action_text, action_callback)
    
    def success(self, title, message, duration=4000, action_text=None, action_callback=None):
        """Show success notification"""
        return self.show_notification(title, message, "success", duration, action_text, action_callback)
    
    def warning(self, title, message, duration=6000, action_text=None, action_callback=None):
        """Show warning notification"""
        return self.show_notification(title, message, "warning", duration, action_text, action_callback)
    
    def error(self, title, message, duration=7000, action_text=None, action_callback=None):
        """Show error notification"""
        return self.show_notification(title, message, "error", duration, action_text, action_callback)
    
    def goal(self, title, message, duration=6000, action_text=None, action_callback=None):
        """Show goal/achievement notification"""
        return self.show_notification(title, message, "goal", duration, action_text, action_callback)


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Toast Notification Demo")
            self.setGeometry(100, 100, 600, 400)
            
            # Create notification manager
            self.notifier = NotificationManager(self)
            
            # Setup UI
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setSpacing(10)
            
            # Test buttons
            buttons = [
                ("Show Info", self.show_info),
                ("Show Success", self.show_success),
                ("Show Warning", self.show_warning),
                ("Show Error", self.show_error),
                ("Show Goal", self.show_goal),
                ("Show With Action", self.show_with_action),
                ("Show Multiple", self.show_multiple),
                ("Clear All", self.notifier.clear_all),
            ]
            
            for text, callback in buttons:
                btn = QPushButton(text)
                btn.clicked.connect(callback)
                layout.addWidget(btn)
        
        def show_info(self):
            self.notifier.info(
                "Information",
                "This is an informational message with some details."
            )
        
        def show_success(self):
            self.notifier.success(
                "Success!",
                "Your tracking data has been saved successfully."
            )
        
        def show_warning(self):
            self.notifier.warning(
                "Daily Limit Warning",
                "You've used Chrome for 90 minutes today. Consider taking a break!"
            )
        
        def show_error(self):
            self.notifier.error(
                "Error",
                "Failed to save backup. Please check disk space."
            )
        
        def show_goal(self):
            self.notifier.goal(
                "Goal Reached! 🎉",
                "You've maintained focus for 2 hours straight. Great work!",
                action_text="View Stats"
            )
        
        def show_with_action(self):
            self.notifier.warning(
                "Break Reminder",
                "You've been working for 90 minutes. Time for a break?",
                action_text="Start Break",
                action_callback=lambda: print("Break started!")
            )
        
        def show_multiple(self):
            self.notifier.success("Task 1", "First notification")
            QTimer.singleShot(500, lambda: self.notifier.info("Task 2", "Second notification"))
            QTimer.singleShot(1000, lambda: self.notifier.warning("Task 3", "Third notification"))
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
