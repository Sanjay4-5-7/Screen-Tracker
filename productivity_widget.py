#!/usr/bin/env python3
"""
Enhanced Productivity Widget for Puthu Tracker
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from browser_tracker import ProductivityAnalyzer
import numpy as np

class ProductivityWidget(QWidget):
    def __init__(self, db_manager, theme_manager=None, category_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        # Use the shared category manager or create analyzer with default categories
        if category_manager:
            self.analyzer = ProductivityAnalyzer(category_manager=category_manager)
        else:
            self.analyzer = ProductivityAnalyzer()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with fixed styling that won't change
        self.title_label = QLabel("Productivity Analysis")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #1C1C1E;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Productivity score card
        self.score_card = self.create_score_card()
        layout.addWidget(self.score_card)
        
        # Category breakdown - removed container and title
        # Pie chart for category breakdown with no border
        chart_widget = QWidget()
        chart_widget.setStyleSheet("background-color: transparent; border: none;")
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        layout.addWidget(chart_widget)
        
        self.setLayout(layout)
        self.update_productivity_data()
    
    def update_theme(self):
        """Update styling when theme changes"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')
        
        # Update title text color
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 10px;
                    background-color: transparent;
                }}
            """)
        
        # CRITICAL: Redraw the chart with the new theme
        self.update_productivity_data()
    
    def apply_title_styling(self, label):
        """Apply title styling based on theme"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')
        
        # Use a simpler approach that doesn't conflict
        label.setStyleSheet(f"color: {text_color}; font-size: 28px; font-weight: 700; margin-bottom: 10px;")
    
    def apply_subtitle_styling(self, label):
        """Apply subtitle styling based on theme"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')
        
        # Use a simpler approach that doesn't conflict
        label.setStyleSheet(f"color: {text_color}; font-size: 18px; font-weight: 600; margin-bottom: 15px;")
    
    def apply_container_styling(self, container):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            container.setStyleSheet("""
                QFrame {
                    background-color: #1C1C1E;
                    border-radius: 12px;
                    border: 1px solid #48484A;
                }
            """)
        else:
            container.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 12px;
                    border: 1px solid #E5E5EA;
                }
            """)
    
    def create_score_card(self):
        """Create productivity score card"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #007AFF, stop:1 #34C759);
                border-radius: 16px;
                border: none;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # Score section
        score_layout = QVBoxLayout()
        
        score_label = QLabel("Productivity Score")
        score_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 500;
            opacity: 0.9;
        """)
        
        self.score_value = QLabel("--")
        self.score_value.setStyleSheet("""
            color: white;
            font-size: 48px;
            font-weight: 700;
        """)
        
        score_layout.addWidget(score_label)
        score_layout.addWidget(self.score_value)
        
        # Status section
        status_layout = QVBoxLayout()
        
        self.status_emoji = QLabel("📊")
        self.status_emoji.setStyleSheet("font-size: 32px;")
        
        self.status_text = QLabel("Analyzing...")
        self.status_text.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 500;
            opacity: 0.9;
        """)
        
        status_layout.addWidget(self.status_emoji, alignment=Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_text, alignment=Qt.AlignmentFlag.AlignCenter)
        status_layout.addStretch()
        
        layout.addLayout(score_layout)
        layout.addStretch()
        layout.addLayout(status_layout)
        
        return card
    
    def create_recommendations_widget(self):
        """Create recommendations widget"""
        widget = QFrame()
        self.apply_container_styling(widget)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("💡 Recommendations")
        self.apply_subtitle_styling(title)
        layout.addWidget(title)
        
        self.recommendations_list = QVBoxLayout()
        layout.addLayout(self.recommendations_list)
        
        return widget
    
    def update_productivity_data(self):
        """Update all productivity data and visualizations"""
        # Get today's usage data
        usage_data = self.db_manager.get_app_usage_by_date()
        
        if not usage_data:
            self.show_no_data_message()
            return
        
        # Get productivity insights
        insights = self.analyzer.get_productivity_insights(usage_data)
        
        # Update score card
        self.update_score_card(insights)
        
        # Update category breakdown chart
        self.update_category_chart(insights)
    
    def update_score_card(self, insights):
        """Update productivity score card"""
        score = insights['productivity_score']
        self.score_value.setText(str(int(score)))
        
        # Update status based on score
        if score >= 80:
            self.status_emoji.setText("🎯")
            self.status_text.setText("Excellent!")
            gradient = "stop:0 #34C759, stop:1 #30D158"
        elif score >= 60:
            self.status_emoji.setText("👍")
            self.status_text.setText("Good")
            gradient = "stop:0 #007AFF, stop:1 #34C759"
        elif score >= 40:
            self.status_emoji.setText("⚖️")
            self.status_text.setText("Balanced")
            gradient = "stop:0 #FF9500, stop:1 #FFCC02"
        else:
            self.status_emoji.setText("⚠️")
            self.status_text.setText("Needs Focus")
            gradient = "stop:0 #FF3B30, stop:1 #FF9500"
        
        # Update card gradient
        self.score_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, {gradient});
                border-radius: 16px;
                border: none;
            }}
        """)
    
    def update_category_chart(self, insights):
        """Update category breakdown pie chart"""
        self.ax.clear()
        
        # Check if dark mode is enabled
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        time_breakdown = insights['time_breakdown']
        
        # Filter out categories with 0 time
        categories = []
        values = []
        colors = []
        
        category_colors = {
            'productive': '#34C759',
            'neutral': '#007AFF', 
            'entertainment': '#FF3B30',
            'social': '#FF9500',
            'uncategorized': '#8E8E93'
        }
        
        category_labels = {
            'productive': 'Productive',
            'neutral': 'Neutral',
            'entertainment': 'Entertainment', 
            'social': 'Social',
            'uncategorized': 'Other'
        }
        
        for category, time_seconds in time_breakdown.items():
            if time_seconds > 0:
                categories.append(category_labels[category])
                values.append(time_seconds / 3600)  # Convert to hours
                colors.append(category_colors[category])
        
        if values:
            # Create pie chart with consistent styling
            wedges, texts, autotexts = self.ax.pie(
                values, 
                labels=categories,
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 11, 'fontweight': '500'}
            )
            
            # Style percentage text with better visibility
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('600')
                autotext.set_fontsize(10)
                autotext.set_bbox(dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
            
            # Style category labels based on background
            label_color = '#FFFFFF' if is_dark else '#1C1C1E'
            for text in texts:
                text.set_fontsize(11)
                text.set_fontweight('600')
                text.set_color(label_color)
        else:
            no_data_color = '#FFFFFF' if is_dark else '#8E8E93'
            self.ax.text(0.5, 0.5, 'No data available\nStart tracking to see\nproductivity analysis!', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14, color=no_data_color,
                        fontweight='500')
        
        # Set chart title and background based on theme
        title_color = '#FFFFFF' if is_dark else '#1C1C1E'
        bg_color = '#000000' if is_dark else 'white'
        
        self.ax.set_title('Time Distribution by Category', fontsize=16, fontweight='bold', 
                         pad=20, color=title_color)
        
        # Ensure equal aspect ratio
        self.ax.set_aspect('equal')
        
        # Set background colors based on theme
        self.figure.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        # Layout adjustments
        self.figure.tight_layout(pad=2.0)
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.1)
        
        self.canvas.draw()
    
    def update_recommendations(self, recommendations):
        """Update recommendations list"""
        # Clear existing recommendations
        while self.recommendations_list.count():
            child = self.recommendations_list.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add new recommendations
        for i, recommendation in enumerate(recommendations):
            rec_widget = self.create_recommendation_item(recommendation, i + 1)
            self.recommendations_list.addWidget(rec_widget)
    
    def create_recommendation_item(self, text, number):
        """Create a single recommendation item"""
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #F8F8F8;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 8px;
            }
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Number badge
        number_label = QLabel(str(number))
        number_label.setFixedSize(24, 24)
        number_label.setStyleSheet("""
            QLabel {
                background-color: #007AFF;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
                text-align: center;
            }
        """)
        number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Recommendation text
        rec_text = QLabel(text)
        rec_text.setStyleSheet("""
            color: #3C3C43;
            font-size: 14px;
            font-weight: 500;
            line-height: 1.4;
        """)
        rec_text.setWordWrap(True)
        
        layout.addWidget(number_label)
        layout.addWidget(rec_text)
        
        return item
    
    def show_no_data_message(self):
        """Show message when no data is available"""
        self.score_value.setText("--")
        self.status_emoji.setText("📊")
        self.status_text.setText("No data yet")
        
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'Start tracking to see\nyour productivity analysis!', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=self.ax.transAxes,
                    fontsize=16, color='#8E8E93')
        self.figure.tight_layout()
        self.canvas.draw()

class CircularProgressBar(QWidget):
    """Custom circular progress bar for productivity score"""
    
    def __init__(self, value=0, max_value=100):
        super().__init__()
        self.value = value
        self.max_value = max_value
        self.setMinimumSize(120, 120)
    
    def setValue(self, value):
        self.value = max(0, min(value, self.max_value))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 10
        
        # Background circle
        painter.setPen(QPen(QColor("#E5E5EA"), 8))
        painter.drawEllipse(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        
        # Progress arc
        progress_angle = int(360 * self.value / self.max_value)
        
        # Color based on value
        if self.value >= 80:
            color = QColor("#34C759")
        elif self.value >= 60:
            color = QColor("#007AFF")
        elif self.value >= 40:
            color = QColor("#FF9500")
        else:
            color = QColor("#FF3B30")
        
        painter.setPen(QPen(color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(center.x() - radius, center.y() - radius, radius * 2, radius * 2, 
                       90 * 16, -progress_angle * 16)
        
        # Center text
        painter.setPen(QPen(QColor("#1C1C1E")))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(int(self.value)))

# Export for use in main application
__all__ = ['ProductivityWidget', 'CircularProgressBar']
