#!/usr/bin/env python3
"""
Test script for notifications
Run this to test if toast notifications are working
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
from toast_notifications import NotificationManager

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toast Notification Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create notification manager
        self.notifier = NotificationManager(self)
        
        # Setup UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        
        # Test buttons
        buttons = [
            ("Test Info Notification", self.test_info),
            ("Test Success Notification", self.test_success),
            ("Test Warning Notification", self.test_warning),
            ("Test Error Notification", self.test_error),
            ("Test Goal Notification", self.test_goal),
            ("Test Multiple Notifications", self.test_multiple),
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
    
    def test_info(self):
        self.notifier.info(
            "Information",
            "This is a test information message with some details."
        )
        print("Info notification triggered!")
    
    def test_success(self):
        self.notifier.success(
            "Success!",
            "Your test was successful. The notification system is working!"
        )
        print("Success notification triggered!")
    
    def test_warning(self):
        self.notifier.warning(
            "Warning",
            "You've reached 80% of your daily limit. Consider taking a break!"
        )
        print("Warning notification triggered!")
    
    def test_error(self):
        self.notifier.error(
            "Error!",
            "Daily limit exceeded! You've used more time than allowed."
        )
        print("Error notification triggered!")
    
    def test_goal(self):
        self.notifier.goal(
            "Goal Reached! 🎉",
            "You've maintained focus for 2 hours straight. Great work!",
            action_text="View Stats"
        )
        print("Goal notification triggered!")
    
    def test_multiple(self):
        self.notifier.success("Task 1", "First notification")
        QTimer.singleShot(500, lambda: self.notifier.info("Task 2", "Second notification"))
        QTimer.singleShot(1000, lambda: self.notifier.warning("Task 3", "Third notification"))
        print("Multiple notifications triggered!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("Test window opened - click buttons to test notifications!")
    sys.exit(app.exec())
