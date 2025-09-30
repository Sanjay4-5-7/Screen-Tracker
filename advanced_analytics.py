#!/usr/bin/env python3
"""Advanced Analytics - Detailed insights and reports for Puthu Tracker"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

class AnalyticsManager:
    """Manages analytics calculations and data processing"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_top_apps(self, period='daily', date=None, limit=5):
        """Get top N apps for a period"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if period == 'daily':
            data = self.db.get_app_usage_by_date(date)
        elif period == 'weekly':
            data = self.get_weekly_data()
        elif period == 'monthly':
            data = self.get_monthly_data()
        else:
            data = self.db.get_app_usage_by_date(date)
        
        # Return top N apps
        return data[:limit] if len(data) >= limit else data
    
    def get_weekly_data(self):
        """Get aggregated data for the past 7 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        app_totals = defaultdict(int)
        
        for i in range(8):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_data = self.db.get_app_usage_by_date(date)
            for app, duration in daily_data:
                app_totals[app] += duration
        
        # Convert to sorted list
        return sorted(app_totals.items(), key=lambda x: x[1], reverse=True)
    
    def get_monthly_data(self):
        """Get aggregated data for the past 30 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        app_totals = defaultdict(int)
        
        for i in range(31):
            date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            daily_data = self.db.get_app_usage_by_date(date)
            for app, duration in daily_data:
                app_totals[app] += duration
        
        return sorted(app_totals.items(), key=lambda x: x[1], reverse=True)
    
    def get_heatmap_data(self, days=30):
        """Get daily usage data for heatmap"""
        end_date = datetime.now()
        heatmap_data = []
        
        for i in range(days):
            date = (end_date - timedelta(days=days - i - 1)).strftime('%Y-%m-%d')
            daily_data = self.db.get_app_usage_by_date(date)
            total_seconds = sum(duration for _, duration in daily_data)
            total_hours = total_seconds / 3600
            
            heatmap_data.append({
                'date': date,
                'hours': total_hours,
                'day_name': datetime.strptime(date, '%Y-%m-%d').strftime('%a')
            })
        
        return heatmap_data
    
    def calculate_productivity_score(self, date):
        """Calculate productivity score for a date (0-100)"""
        # This is a simple implementation - can be enhanced based on app categories
        daily_data = self.db.get_app_usage_by_date(date)
        
        if not daily_data:
            return 0
        
        # Simple scoring: more diverse usage = higher productivity
        total_time = sum(duration for _, duration in daily_data)
        app_count = len(daily_data)
        
        # Normalize score (this is simplified)
        score = min(100, (app_count * 10) + (total_time / 3600) * 5)
        return int(score)
    
    def get_productivity_streak(self):
        """Calculate consecutive productive days"""
        streak = 0
        current_date = datetime.now()
        
        for i in range(365):  # Check up to a year
            date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
            score = self.calculate_productivity_score(date)
            
            if score >= 50:  # Threshold for "productive day"
                streak += 1
            else:
                break
        
        return streak
    
    def compare_periods(self, period1_start, period1_end, period2_start, period2_end):
        """Compare two time periods"""
        def get_period_stats(start, end):
            days = (end - start).days + 1
            total_time = 0
            app_usage = defaultdict(int)
            
            for i in range(days):
                date = (start + timedelta(days=i)).strftime('%Y-%m-%d')
                daily_data = self.db.get_app_usage_by_date(date)
                for app, duration in daily_data:
                    total_time += duration
                    app_usage[app] += duration
            
            return {
                'total_time': total_time,
                'daily_average': total_time / days if days > 0 else 0,
                'top_app': max(app_usage.items(), key=lambda x: x[1]) if app_usage else ('None', 0),
                'app_count': len(app_usage)
            }
        
        period1 = get_period_stats(period1_start, period1_end)
        period2 = get_period_stats(period2_start, period2_end)
        
        return period1, period2

class AdvancedAnalyticsWidget(QWidget):
    """Advanced analytics widget with detailed insights"""
    
    def __init__(self, db_manager, theme_manager=None):
        super().__init__()
        self.db = db_manager
        self.theme = theme_manager
        self.analytics = AnalyticsManager(db_manager)
        self.init_ui()
    
    def init_ui(self):
        theme = self.theme.get_current_theme() if self.theme else {}
        is_dark = self.theme.dark_mode if self.theme else False
        tc = theme.get('text_primary', '#FFFFFF' if is_dark else '#1C1C1E')
        tm = theme.get('text_muted', '#98989D' if is_dark else '#8E8E93')
        bg = theme.get('card_bg', '#1C1C1E' if is_dark else '#FFFFFF')
        
        # Check if layout already exists and clear it
        if self.layout():
            QWidget().setLayout(self.layout())
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea {background-color: transparent; border: none;}")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 15, 0)
        
        # Title
        title = QLabel("📊 Advanced Analytics")
        title.setStyleSheet(f"font-size:28px;font-weight:700;color:{tc};background-color:transparent;margin-bottom:10px")
        layout.addWidget(title)
        
        # Productivity Streak Card
        streak_card = self.create_streak_card(bg, tc, tm)
        layout.addWidget(streak_card)
        
        # Top Apps Card
        top_apps_card = self.create_top_apps_card(bg, tc, tm)
        layout.addWidget(top_apps_card)
        
        # Heatmap Card
        heatmap_card = self.create_heatmap_card(bg, tc, tm, is_dark)
        layout.addWidget(heatmap_card)
        
        # Period Comparison Card
        comparison_card = self.create_comparison_card(bg, tc, tm)
        layout.addWidget(comparison_card)
        
        # Weekly Report Card
        report_card = self.create_report_card(bg, tc, tm)
        layout.addWidget(report_card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
    
    def create_streak_card(self, bg, tc, tm):
        """Create productivity streak card"""
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        
        self.streak_header = QLabel("🔥 Productivity Streak")
        self.streak_header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        layout.addWidget(self.streak_header)
        
        streak = self.analytics.get_productivity_streak()
        
        self.streak_value = QLabel(f"{streak} Days")
        self.streak_value.setStyleSheet(f"font-size:48px;font-weight:800;color:#FF9500;background-color:transparent;margin:20px 0")
        self.streak_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.streak_value)
        
        self.streak_desc = QLabel(f"Keep it up! You've been productive for {streak} consecutive days.")
        self.streak_desc.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent")
        self.streak_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.streak_desc.setWordWrap(True)
        layout.addWidget(self.streak_desc)
        
        return card
    
    def create_top_apps_card(self, bg, tc, tm):
        """Create top apps leaderboard card"""
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        
        # Header with period selector
        header_layout = QHBoxLayout()
        header = QLabel("🏆 Top 5 Apps")
        header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "This Week", "This Month"])
        self.period_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.period_combo.currentTextChanged.connect(self.update_top_apps)
        
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(self.period_combo)
        layout.addLayout(header_layout)
        
        # Top apps list
        self.top_apps_layout = QVBoxLayout()
        self.top_apps_layout.setSpacing(10)
        layout.addLayout(self.top_apps_layout)
        
        self.update_top_apps("Today")
        
        return card
    
    def update_top_apps(self, period_text):
        """Update top apps display"""
        # Clear existing - properly delete widgets
        while self.top_apps_layout.count():
            item = self.top_apps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout_recursive(item.layout())
        
        # Get data
        period_map = {"Today": "daily", "This Week": "weekly", "This Month": "monthly"}
        period = period_map.get(period_text, "daily")
        top_apps = self.analytics.get_top_apps(period=period)
        
        theme = self.theme.get_current_theme() if self.theme else {}
        tc = theme.get('text_primary', '#FFFFFF' if self.theme.dark_mode else '#1C1C1E')
        tm = theme.get('text_muted', '#98989D' if self.theme.dark_mode else '#8E8E93')
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, (app, duration) in enumerate(top_apps):
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            # Create a container widget for each row
            row_widget = QWidget()
            row_widget.setStyleSheet("background-color: transparent;")
            app_row = QHBoxLayout(row_widget)
            app_row.setContentsMargins(0, 5, 0, 5)
            app_row.setSpacing(10)
            
            medal_label = QLabel(medals[i])
            medal_label.setStyleSheet(f"font-size:24px;background-color:transparent")
            medal_label.setFixedWidth(40)
            
            app_label = QLabel(app)
            app_label.setStyleSheet(f"font-size:15px;font-weight:600;color:{tc};background-color:transparent")
            
            time_label = QLabel(time_str)
            time_label.setStyleSheet(f"font-size:15px;font-weight:600;color:{tm};background-color:transparent")
            time_label.setFixedWidth(80)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            app_row.addWidget(medal_label)
            app_row.addWidget(app_label)
            app_row.addStretch()
            app_row.addWidget(time_label)
            
            self.top_apps_layout.addWidget(row_widget)
    
    def clear_layout_recursive(self, layout):
        """Recursively clear a layout and delete all widgets"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout_recursive(item.layout())
    
    def create_heatmap_card(self, bg, tc, tm, is_dark):
        """Create activity heatmap card using Qt widgets instead of matplotlib"""
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        
        header = QLabel("📅 Activity Heatmap (Last 30 Days)")
        header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        layout.addWidget(header)
        
        # Get heatmap data
        data = self.analytics.get_heatmap_data(30)
        
        # Color function
        def get_color(hours):
            if hours == 0:
                return '#E5E5EA' if not is_dark else '#2C2C2E'
            elif hours < 2:
                return '#C6F6D5'
            elif hours < 4:
                return '#68D391'
            elif hours < 6:
                return '#48BB78'
            elif hours < 8:
                return '#38A169'
            else:
                return '#2F855A'
        
        # Create grid container
        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: transparent;")
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 10, 0, 10)
        
        # Create cells
        for i, day_data in enumerate(data):
            col = i % 7
            row = i // 7
            
            # Create cell widget
            cell = QFrame()
            cell.setFixedSize(120, 70)
            bg_color = get_color(day_data['hours'])
            
            # IMPORTANT: Set object name so we can identify cells later
            cell.setObjectName("heatmap_cell")
            
            cell.setStyleSheet(f"""
                QFrame#heatmap_cell {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 8px;
                }}
                QLabel {{
                    border: none;
                    background-color: transparent;
                }}
            """)
            
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(5, 8, 5, 8)
            cell_layout.setSpacing(2)
            
            # Day name - always white text with !important-like specificity
            day_label = QLabel(day_data['day_name'][:2])
            day_label.setObjectName("heatmap_label")  # Mark as heatmap label
            day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_label.setStyleSheet("QLabel#heatmap_label{font-size:14px;font-weight:bold;color:#FFFFFF;background-color:transparent;border:none}")
            cell_layout.addWidget(day_label)
            
            # Hours - always white text with !important-like specificity
            if day_data['hours'] > 0:
                hours_label = QLabel(f"{day_data['hours']:.1f}h")
                hours_label.setObjectName("heatmap_label")  # Mark as heatmap label
                hours_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hours_label.setStyleSheet("QLabel#heatmap_label{font-size:12px;font-weight:600;color:#FFFFFF;background-color:transparent;border:none}")
                cell_layout.addWidget(hours_label)
            
            grid_layout.addWidget(cell, row, col)
        
        layout.addWidget(grid_container)
        
        # Add legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(15)
        legend_label = QLabel("Activity Level:")
        legend_label.setStyleSheet(f"font-size:13px;font-weight:600;color:{tm};background-color:transparent")
        legend_layout.addWidget(legend_label)
        
        colors = [
            ("0h", "#E5E5EA" if not is_dark else "#2C2C2E"),
            ("0-2h", "#C6F6D5"),
            ("2-4h", "#68D391"),
            ("4-6h", "#48BB78"),
            ("6-8h", "#38A169"),
            ("8+h", "#2F855A")
        ]
        
        for label, color in colors:
            color_box = QLabel()
            color_box.setFixedSize(40, 20)
            color_box.setStyleSheet(f"background-color:{color};border-radius:4px;border:1px solid {'#48484A' if is_dark else '#D1D1D6'}")
            
            text_label = QLabel(label)
            text_label.setStyleSheet(f"font-size:11px;color:{tm};background-color:transparent")
            
            legend_layout.addWidget(color_box)
            legend_layout.addWidget(text_label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        return card

    
    def create_comparison_card(self, bg, tc, tm):
        """Create period comparison card"""
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        
        self.comparison_header = QLabel("📊 This Week vs Last Week")
        self.comparison_header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        layout.addWidget(self.comparison_header)
        
        # Calculate comparison
        today = datetime.now()
        this_week_start = today - timedelta(days=7)
        last_week_start = today - timedelta(days=14)
        last_week_end = today - timedelta(days=7)
        
        this_week, last_week = self.analytics.compare_periods(
            this_week_start, today, last_week_start, last_week_end
        )
        
        # Display comparison
        comp_layout = QHBoxLayout()
        
        # This week
        this_week_widget = self.create_period_widget("This Week", this_week, tc, tm)
        comp_layout.addWidget(this_week_widget)
        
        # VS label
        vs_label = QLabel("VS")
        vs_label.setStyleSheet(f"font-size:24px;font-weight:800;color:{tm};background-color:transparent")
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_layout.addWidget(vs_label)
        
        # Last week
        last_week_widget = self.create_period_widget("Last Week", last_week, tc, tm)
        comp_layout.addWidget(last_week_widget)
        
        layout.addLayout(comp_layout)
        
        # Change indicator
        change = ((this_week['total_time'] - last_week['total_time']) / last_week['total_time'] * 100) if last_week['total_time'] > 0 else 0
        change_text = f"{'📈' if change > 0 else '📉'} {abs(change):.1f}% {'increase' if change > 0 else 'decrease'} from last week"
        
        self.comparison_change = QLabel(change_text)
        self.comparison_change.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent;margin-top:15px")
        self.comparison_change.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.comparison_change)
        
        return card
    
    def create_period_widget(self, title, stats, tc, tm):
        """Create a widget showing period statistics"""
        widget = QFrame()
        widget.setStyleSheet("QFrame {background-color: transparent; border: none;}")
        layout = QVBoxLayout(widget)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size:14px;font-weight:600;color:{tm};background-color:transparent")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        hours = stats['total_time'] // 3600
        time_label = QLabel(f"{hours}h")
        time_label.setStyleSheet(f"font-size:32px;font-weight:800;color:{tc};background-color:transparent")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)
        
        top_app = stats['top_app'][0]
        top_app_label = QLabel(f"Top: {top_app}")
        top_app_label.setStyleSheet(f"font-size:12px;color:{tm};background-color:transparent")
        top_app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(top_app_label)
        
        return widget
    
    def create_report_card(self, bg, tc, tm):
        """Create weekly report card"""
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 24, 30, 24)
        
        self.report_header = QLabel("📄 Reports")
        self.report_header.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
        layout.addWidget(self.report_header)
        
        self.report_desc = QLabel("Generate detailed usage reports")
        self.report_desc.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent;margin-bottom:15px")
        layout.addWidget(self.report_desc)
        
        # Report buttons
        button_layout = QHBoxLayout()
        
        weekly_btn = QPushButton("📊 Weekly Report")
        weekly_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        weekly_btn.clicked.connect(self.generate_weekly_report)
        weekly_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        monthly_btn = QPushButton("📅 Monthly Report")
        monthly_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #28A745;
            }
        """)
        monthly_btn.clicked.connect(self.generate_monthly_report)
        monthly_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        button_layout.addWidget(weekly_btn)
        button_layout.addWidget(monthly_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return card
    
    def generate_weekly_report(self):
        """Generate weekly report"""
        try:
            # Calculate date range for this week
            today = datetime.now()
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            
            # Ask user for format
            msg = QMessageBox()
            msg.setWindowTitle("Weekly Report")
            msg.setText("Generate Weekly Report")
            msg.setInformativeText("Choose export format:")
            
            csv_btn = msg.addButton("📄 CSV", QMessageBox.ButtonRole.ActionRole)
            json_btn = msg.addButton("🗂️ JSON", QMessageBox.ButtonRole.ActionRole)
            pdf_btn = msg.addButton("📑 PDF", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)
            
            msg.exec()
            clicked = msg.clickedButton()
            
            if clicked == cancel_btn:
                return
            
            # Create exporter
            from export_backup import DataExporter
            exporter = DataExporter(self.db)
            
            # Generate report based on choice
            if clicked == csv_btn:
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Weekly Report",
                    str(Path.home() / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.csv"),
                    "CSV Files (*.csv)"
                )
                if path:
                    exporter.export_to_csv(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Weekly report saved:\n{path}")
            
            elif clicked == json_btn:
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Weekly Report",
                    str(Path.home() / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json"),
                    "JSON Files (*.json)"
                )
                if path:
                    exporter.export_to_json(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Weekly report saved:\n{path}")
            
            elif clicked == pdf_btn:
                try:
                    from reportlab.lib import colors
                    PDF_AVAILABLE = True
                except ImportError:
                    PDF_AVAILABLE = False
                
                if not PDF_AVAILABLE:
                    QMessageBox.warning(self, "PDF Unavailable",
                        "PDF export requires reportlab library.\n\n"
                        "Install with: pip install reportlab")
                    return
                
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Weekly Report",
                    str(Path.home() / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"),
                    "PDF Files (*.pdf)"
                )
                if path:
                    exporter.export_to_pdf(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Weekly report saved:\n{path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")
    
    def generate_monthly_report(self):
        """Generate monthly report"""
        try:
            # Calculate date range for this month
            today = datetime.now()
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            
            # Ask user for format
            msg = QMessageBox()
            msg.setWindowTitle("Monthly Report")
            msg.setText("Generate Monthly Report")
            msg.setInformativeText("Choose export format:")
            
            csv_btn = msg.addButton("📄 CSV", QMessageBox.ButtonRole.ActionRole)
            json_btn = msg.addButton("🗂️ JSON", QMessageBox.ButtonRole.ActionRole)
            pdf_btn = msg.addButton("📑 PDF", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg.addButton(QMessageBox.StandardButton.Cancel)
            
            msg.exec()
            clicked = msg.clickedButton()
            
            if clicked == cancel_btn:
                return
            
            # Create exporter
            from export_backup import DataExporter
            exporter = DataExporter(self.db)
            
            # Generate report based on choice
            if clicked == csv_btn:
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Monthly Report",
                    str(Path.home() / f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv"),
                    "CSV Files (*.csv)"
                )
                if path:
                    exporter.export_to_csv(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Monthly report saved:\n{path}")
            
            elif clicked == json_btn:
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Monthly Report",
                    str(Path.home() / f"monthly_report_{datetime.now().strftime('%Y%m%d')}.json"),
                    "JSON Files (*.json)"
                )
                if path:
                    exporter.export_to_json(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Monthly report saved:\n{path}")
            
            elif clicked == pdf_btn:
                try:
                    from reportlab.lib import colors
                    PDF_AVAILABLE = True
                except ImportError:
                    PDF_AVAILABLE = False
                
                if not PDF_AVAILABLE:
                    QMessageBox.warning(self, "PDF Unavailable",
                        "PDF export requires reportlab library.\n\n"
                        "Install with: pip install reportlab")
                    return
                
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Monthly Report",
                    str(Path.home() / f"monthly_report_{datetime.now().strftime('%Y%m%d')}.pdf"),
                    "PDF Files (*.pdf)"
                )
                if path:
                    exporter.export_to_pdf(path, start_date, end_date)
                    QMessageBox.information(self, "Success", f"Monthly report saved:\n{path}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report:\n{str(e)}")
    
    def update_theme(self):
        """Update theme by refreshing all styled elements"""
        # Store current period selection if it exists
        current_period = self.period_combo.currentText() if hasattr(self, 'period_combo') else "Today"
        
        # Get new theme colors
        theme = self.theme.get_current_theme() if self.theme else {}
        is_dark = self.theme.dark_mode if self.theme else False
        tc = '#FFFFFF' if is_dark else '#1C1C1E'
        tm = '#98989D' if is_dark else '#8E8E93'
        bg = '#1C1C1E' if is_dark else '#FFFFFF'
        border = '#48484A' if is_dark else '#E5E5EA'
        
        # Update scroll area styling
        scroll = self.findChild(QScrollArea)
        if scroll:
            scroll.setStyleSheet("QScrollArea {background-color: transparent; border: none;}")
        
        # Update ALL cards (QFrame widgets) - BUT EXCLUDE HEATMAP CELLS
        for card in self.findChildren(QFrame):
            # Skip heatmap cells
            if card.objectName() == "heatmap_cell":
                continue
            if card.layout():
                card.setStyleSheet(f"QFrame{{background-color:{bg};border-radius:12px;border:none}}")
        
        # Update ALL labels by text matching - BUT SKIP HEATMAP LABELS
        for label in self.findChildren(QLabel):
            # Skip heatmap labels - they should always stay white
            if label.objectName() == "heatmap_label":
                continue
                
            text = label.text()
            
            # Main title
            if "Advanced Analytics" in text or "📊 Advanced Analytics" in text:
                label.setStyleSheet(f"font-size:28px;font-weight:700;color:{tc};background-color:transparent;margin-bottom:10px")
            
            # Section headers (18px)
            elif any(header in text for header in ["🔥 Productivity Streak", "🏆 Top 5 Apps", "📅 Activity Heatmap", "📊 This Week vs Last Week", "📄 Reports"]):
                label.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent")
            
            # Streak number (48px - keep orange)
            elif "Days" in text and "font-size:48px" in label.styleSheet():
                pass  # Keep original orange color
            
            # Period comparison large numbers (32px)
            elif "h" in text and "font-size:32px" in label.styleSheet():
                label.setStyleSheet(f"font-size:32px;font-weight:800;color:{tc};background-color:transparent")
            
            # VS label (24px)
            elif text == "VS":
                label.setStyleSheet(f"font-size:24px;font-weight:800;color:{tm};background-color:transparent")
            
            # App names and times (15px)
            elif "font-size:15px" in label.styleSheet():
                if label.alignment() & Qt.AlignmentFlag.AlignRight:
                    # Time labels (right-aligned)
                    label.setStyleSheet(f"font-size:15px;font-weight:600;color:{tm};background-color:transparent")
                else:
                    # App names
                    label.setStyleSheet(f"font-size:15px;font-weight:600;color:{tc};background-color:transparent")
            
            # Description text (14px)
            elif "font-size:14px" in label.styleSheet():
                label.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent")
            
            # Small labels (12px) - period widget labels
            elif "font-size:12px" in label.styleSheet():
                label.setStyleSheet(f"font-size:12px;color:{tm};background-color:transparent")
            
            # Legend text (11px)
            elif "font-size:11px" in label.styleSheet():
                label.setStyleSheet(f"font-size:11px;color:{tm};background-color:transparent")
        
        # Update period combo box
        if hasattr(self, 'period_combo'):
            self.period_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: #007AFF;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QComboBox::drop-down {{
                    border: none;
                }}
            """)
            # Restore selection
            index = self.period_combo.findText(current_period)
            if index >= 0:
                self.period_combo.setCurrentIndex(index)
        
        # Force refresh of top apps list
        if hasattr(self, 'period_combo'):
            self.update_top_apps(self.period_combo.currentText())
        
        # Force visual update
        self.update()

__all__ = ['AdvancedAnalyticsWidget', 'AnalyticsManager']
