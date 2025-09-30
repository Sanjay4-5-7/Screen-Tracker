#!/usr/bin/env python3
"""
Background Runner for Puthu Tracker
This script runs the app in the background with a system tray icon
File extension .pyw prevents console window from appearing
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import main application
from main import QApplication, MainWindow, QStyle
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

class BackgroundApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when window closed
        
        # Create main window but don't show it yet
        self.window = MainWindow()
        
        # Create system tray icon
        self.create_tray_icon()
        
        # Start tracking automatically
        self.window.start_tracking()
    
    def create_tray_icon(self):
        """Create system tray icon with menu"""
        # Use computer icon for tray
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        
        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.tray_icon.setToolTip("Puthu Tracker - Running")
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide window action
        show_action = QAction("📊 Show Dashboard", self.app)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Start/Stop tracking actions
        self.tracking_action = QAction("⏸️ Pause Tracking", self.app)
        self.tracking_action.triggered.connect(self.toggle_tracking)
        tray_menu.addAction(self.tracking_action)
        
        tray_menu.addSeparator()
        
        # Quick stats action
        stats_action = QAction("📈 Quick Stats", self.app)
        stats_action.triggered.connect(self.show_quick_stats)
        tray_menu.addAction(stats_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("❌ Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Double-click to show window
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Show notification
        self.tray_icon.showMessage(
            "Puthu Tracker Started",
            "Running in background. Double-click tray icon to open.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Show the main window"""
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()
    
    def toggle_tracking(self):
        """Toggle tracking on/off"""
        if self.window.tracker.tracking:
            self.window.stop_tracking()
            self.tracking_action.setText("▶️ Resume Tracking")
            self.tray_icon.setToolTip("Puthu Tracker - Paused")
        else:
            self.window.start_tracking()
            self.tracking_action.setText("⏸️ Pause Tracking")
            self.tray_icon.setToolTip("Puthu Tracker - Running")
    
    def show_quick_stats(self):
        """Show quick statistics notification"""
        # Get today's data
        today_data = self.window.db_manager.get_app_usage_by_date()
        
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
        
        self.tray_icon.showMessage(
            "Puthu Tracker Stats",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )
    
    def exit_app(self):
        """Exit the application completely"""
        # Stop tracking
        if self.window.tracker.tracking:
            self.window.stop_tracking()
        
        # Hide tray icon
        self.tray_icon.hide()
        
        # Quit application
        self.app.quit()
    
    def run(self):
        """Run the application"""
        return self.app.exec()

def main():
    app = BackgroundApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
