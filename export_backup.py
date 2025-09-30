#!/usr/bin/env python3
"""Export & Backup Module for Puthu Tracker"""

import csv
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Check for PDF support
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class ExportBackupWidget(QWidget):
    def __init__(self, db_manager, theme_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.theme_manager = theme_manager
        self.backup_manager = BackupManager(db_manager)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("📤 Export & Backup")
        self.apply_title_styling(title)
        layout.addWidget(title)
        
        # Export Section
        layout.addWidget(self.create_export_section())
        
        # Backup Section
        layout.addWidget(self.create_backup_section())
        
        # Restore Section
        layout.addWidget(self.create_restore_section())
        
        layout.addStretch()
        self.setLayout(layout)
    
    def apply_title_styling(self, label):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_color = theme.get('text_primary', '#1C1C1E')
        label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 900;
            color: {text_color};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
    
    def create_export_section(self):
        section = QFrame()
        self.apply_section_styling(section)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.export_title = QLabel("📊 Export Data")
        self.apply_section_title_styling(self.export_title)
        layout.addWidget(self.export_title)
        
        self.export_desc = QLabel("Export your tracking data for analysis")
        self.apply_description_styling(self.export_desc)
        layout.addWidget(self.export_desc)
        
        # Export buttons
        btn_layout = QHBoxLayout()
        
        csv_btn = self.create_button("📄 Export CSV", "#007AFF")
        csv_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(csv_btn)
        
        pdf_btn = self.create_button("📑 Export PDF", "#34C759")
        pdf_btn.clicked.connect(self.export_pdf)
        if not PDF_AVAILABLE:
            pdf_btn.setEnabled(False)
        btn_layout.addWidget(pdf_btn)
        
        json_btn = self.create_button("🗂️ Export JSON", "#FF9500")
        json_btn.clicked.connect(self.export_json)
        btn_layout.addWidget(json_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Date range
        date_layout = QHBoxLayout()
        self.from_label = QLabel("From:")
        self.apply_label_styling(self.from_label)
        date_layout.addWidget(self.from_label)
        
        self.start_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.apply_date_styling(self.start_date)
        date_layout.addWidget(self.start_date)
        
        self.to_label = QLabel("To:")
        self.apply_label_styling(self.to_label)
        date_layout.addWidget(self.to_label)
        
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.apply_date_styling(self.end_date)
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        return section
    
    def create_backup_section(self):
        section = QFrame()
        self.apply_section_styling(section)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.backup_title = QLabel("💾 Backup Management")
        self.apply_section_title_styling(self.backup_title)
        layout.addWidget(self.backup_title)
        
        # Info
        info_layout = QHBoxLayout()
        self.last_backup_label = QLabel("Last: Never")
        self.apply_label_styling(self.last_backup_label)
        self.backup_count_label = QLabel("Total: 0")
        self.apply_label_styling(self.backup_count_label)
        info_layout.addWidget(self.last_backup_label)
        info_layout.addWidget(self.backup_count_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        backup_btn = self.create_button("🔄 Create Backup", "#007AFF")
        backup_btn.clicked.connect(self.create_backup)
        btn_layout.addWidget(backup_btn)
        
        view_btn = self.create_button("📁 View Backups", "#FF9500")
        view_btn.clicked.connect(self.view_backups)
        btn_layout.addWidget(view_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.update_backup_info()
        return section
    
    def create_restore_section(self):
        section = QFrame()
        self.apply_section_styling(section)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.restore_title = QLabel("📥 Import & Restore")
        self.apply_section_title_styling(self.restore_title)
        layout.addWidget(self.restore_title)
        
        restore_btn = self.create_button("♻️ Restore Backup", "#FF3B30")
        restore_btn.clicked.connect(self.restore_backup)
        layout.addWidget(restore_btn)
        
        self.warning_label = QLabel("⚠️ Warning: Restoring will replace all current data")
        self.apply_warning_styling(self.warning_label)
        layout.addWidget(self.warning_label)
        
        return section
    
    def apply_section_styling(self, section):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            bg = '#1C1C1E'
            border = '#38383A'
        else:
            bg = '#FFFFFF'
            border = '#E5E5EA'
        
        section.setStyleSheet(f"QFrame {{background-color: {bg}; border: 1px solid {border}; border-radius: 12px;}}")
    
    def apply_section_title_styling(self, label):
        """Apply section title styling based on theme"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        
        label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {text_color};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
    
    def apply_description_styling(self, label):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        text_muted = theme.get('text_muted', '#8E8E93')
        label.setStyleSheet(f"""
            font-size: 14px;
            color: {text_muted};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
    
    def apply_label_styling(self, label):
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        text_color = '#FFFFFF' if is_dark else '#1C1C1E'
        
        label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {text_color};
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
    
    def apply_warning_styling(self, label):
        label.setStyleSheet("""
            color: #FF3B30;
            font-size: 13px;
            font-weight: 500;
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
    
    def apply_date_styling(self, date_edit):
        """Apply theme-aware styling to date edit widgets"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        
        if is_dark:
            bg_color = '#2C2C2E'
            text_color = '#FFFFFF'
            border_color = '#48484A'
        else:
            bg_color = '#F8F9FA'
            text_color = '#1C1C1E'
            border_color = '#D1D1D6'
        
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                padding: 8px 12px;
                border: 2px solid {border_color};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                color: {text_color};
                background-color: {bg_color};
                min-width: 120px;
            }}
            QDateEdit:focus {{
                border-color: #007AFF;
            }}
            QDateEdit::drop-down {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def create_button(self, text, color):
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{background-color: {color}; color: white; border: none; 
            border-radius: 10px; font-size: 14px; font-weight: 600; padding: 0 20px;}}
            QPushButton:hover {{opacity: 0.9;}}
            QPushButton:disabled {{background-color: #8E8E93; opacity: 0.5;}}
        """)
        return btn
    
    def export_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export CSV",
                str(Path.home() / f"puthu_export_{datetime.now().strftime('%Y%m%d')}.csv"),
                "CSV Files (*.csv)"
            )
            if path:
                DataExporter(self.db_manager).export_to_csv(
                    path,
                    self.start_date.date().toString("yyyy-MM-dd"),
                    self.end_date.date().toString("yyyy-MM-dd")
                )
                QMessageBox.information(self, "Success", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
    
    def export_pdf(self):
        """Export to PDF - Enhanced with better error handling"""
        try:
            # Check if reportlab is available
            try:
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.units import inch
                from reportlab.lib.enums import TA_CENTER
                PDF_AVAILABLE = True
            except ImportError:
                PDF_AVAILABLE = False
            
            if not PDF_AVAILABLE:
                reply = QMessageBox.question(
                    self, "Install ReportLab?",
                    "PDF export requires the 'reportlab' library.\n\n"
                    "Would you like to install it now?\n\n"
                    "Command: pip install reportlab",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    QMessageBox.information(self, "Install Instructions",
                        "Please open Command Prompt and run:\n\n"
                        "pip install reportlab\n\n"
                        "Then restart Puthu Tracker.")
                return
            
            path, _ = QFileDialog.getSaveFileName(
                self, "Export PDF",
                str(Path.home() / f"puthu_report_{datetime.now().strftime('%Y%m%d')}.pdf"),
                "PDF Files (*.pdf)"
            )
            if path:
                DataExporter(self.db_manager).export_to_pdf(
                    path,
                    self.start_date.date().toString("yyyy-MM-dd"),
                    self.end_date.date().toString("yyyy-MM-dd")
                )
                QMessageBox.information(self, "Success", f"PDF created:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF export failed:\n{str(e)}\n\nMake sure reportlab is installed: pip install reportlab")
    
    def export_json(self):
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export JSON",
                str(Path.home() / f"puthu_export_{datetime.now().strftime('%Y%m%d')}.json"),
                "JSON Files (*.json)"
            )
            if path:
                DataExporter(self.db_manager).export_to_json(
                    path,
                    self.start_date.date().toString("yyyy-MM-dd"),
                    self.end_date.date().toString("yyyy-MM-dd")
                )
                QMessageBox.information(self, "Success", f"Exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
    
    def create_backup(self):
        try:
            path = self.backup_manager.create_backup()
            self.update_backup_info()
            QMessageBox.information(self, "Success", f"Backup created:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed:\n{e}")
    
    def view_backups(self):
        if self.backup_manager.backup_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.backup_manager.backup_dir)))
        else:
            QMessageBox.information(self, "No Backups", "No backups created yet.")
    
    def restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup",
            str(self.backup_manager.backup_dir),
            "Database Files (*.db)"
        )
        if not path:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Restore",
            "⚠️ This will replace all data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.backup_manager.restore_backup(path)
                QMessageBox.information(self, "Success", 
                                      "Restored! Restart the app.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Restore failed:\n{e}")
    
    def update_backup_info(self):
        backups = self.backup_manager.list_backups()
        if backups:
            self.last_backup_label.setText(f"Last: {backups[0]['date_str']}")
            self.backup_count_label.setText(f"Total: {len(backups)}")
        else:
            self.last_backup_label.setText("Last: Never")
            self.backup_count_label.setText("Total: 0")
    
    def update_theme(self):
        """Update all styling when theme changes"""
        theme = self.theme_manager.get_current_theme() if self.theme_manager else {}
        is_dark = self.theme_manager.dark_mode if self.theme_manager else False
        tc = '#FFFFFF' if is_dark else '#1C1C1E'
        tm = '#98989D' if is_dark else '#8E8E93'
        
        # Update ALL labels by finding them
        for label in self.findChildren(QLabel):
            current_text = label.text()
            
            # Main page title
            if "📤 Export & Backup" in current_text:
                label.setStyleSheet(f"font-size:28px;font-weight:900;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            
            # Section titles with emojis - MORE SPECIFIC MATCHING
            elif "📊 Export Data" in current_text or "Export Data" in current_text:
                label.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            elif "💾 Backup Management" in current_text or "Backup Management" in current_text:
                label.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            elif "📥 Import & Restore" in current_text or "Import & Restore" in current_text:
                label.setStyleSheet(f"font-size:18px;font-weight:700;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            
            # Description text
            elif "Export your tracking data" in current_text:
                label.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent;border:none;padding:0px;margin:0px")
            elif "Generate detailed" in current_text:
                label.setStyleSheet(f"font-size:14px;color:{tm};background-color:transparent;border:none;padding:0px;margin:0px")
            
            # Labels (From:, To:, Last:, Total:)
            elif current_text in ["From:", "To:", "Last:", "Total:"]:
                label.setStyleSheet(f"font-size:14px;font-weight:600;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            
            # Last: Never and Total: 0 text
            elif "Last:" in current_text or "Total:" in current_text:
                label.setStyleSheet(f"font-size:14px;font-weight:600;color:{tc};background-color:transparent;border:none;padding:0px;margin:0px")
            
            # Warning label (always red)
            elif "⚠️ Warning" in current_text or "Warning:" in current_text:
                label.setStyleSheet("color:#FF3B30;font-size:13px;font-weight:500;background-color:transparent;border:none;padding:0px;margin:0px")
        
        # Update date edits
        for date_edit in self.findChildren(QDateEdit):
            self.apply_date_styling(date_edit)
        
        # Update all section frames (cards) - FORCE UPDATE ALL FRAMES
        for section in self.findChildren(QFrame):
            # Apply styling to all QFrame widgets that are section cards
            if section.layout():
                self.apply_section_styling(section)
        
        # Force visual update
        self.update()


class DataExporter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_data_range(self, start_date, end_date):
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT app_name, window_title, start_time, end_time, duration, date
                FROM app_usage WHERE date BETWEEN ? AND ? ORDER BY start_time
            """, (start_date, end_date))
            app_data = cursor.fetchall()
            
            cursor.execute("""
                SELECT browser_name, tab_title, url, start_time, end_time, duration, date
                FROM browser_usage WHERE date BETWEEN ? AND ? ORDER BY start_time
            """, (start_date, end_date))
            browser_data = cursor.fetchall()
            return app_data, browser_data
    
    def export_to_csv(self, path, start_date, end_date):
        app_data, browser_data = self.get_data_range(start_date, end_date)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Puthu Tracker Export'])
            writer.writerow(['Date Range:', start_date, 'to', end_date])
            writer.writerow([])
            
            writer.writerow(['=== APPLICATIONS ==='])
            writer.writerow(['App', 'Window', 'Start', 'End', 'Duration(s)', 'Date'])
            for row in app_data:
                writer.writerow(row)
            
            writer.writerow([])
            writer.writerow(['=== BROWSER ==='])
            writer.writerow(['Browser', 'Tab', 'URL', 'Start', 'End', 'Duration(s)', 'Date'])
            for row in browser_data:
                writer.writerow(row)
    
    def export_to_json(self, path, start_date, end_date):
        app_data, browser_data = self.get_data_range(start_date, end_date)
        data = {
            'export_info': {
                'date_range': {'start': start_date, 'end': end_date},
                'export_date': datetime.now().isoformat(),
                'version': '2.0'
            },
            'app_usage': [
                {'app': r[0], 'window': r[1], 'start': r[2], 'end': r[3], 
                 'duration': r[4], 'date': r[5]} for r in app_data
            ],
            'browser_usage': [
                {'browser': r[0], 'tab': r[1], 'url': r[2], 'start': r[3], 
                 'end': r[4], 'duration': r[5], 'date': r[6]} for r in browser_data
            ]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def export_to_pdf(self, path, start_date, end_date):
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab not installed")
        
        app_data, browser_data = self.get_data_range(start_date, end_date)
        doc = SimpleDocTemplate(path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title', parent=styles['Heading1'], fontSize=24,
            textColor=colors.HexColor('#007AFF'), spaceAfter=30, alignment=TA_CENTER
        )
        
        story.append(Paragraph("Puthu Tracker Report", title_style))
        story.append(Paragraph(f"Period: {start_date} to {end_date}", styles['Normal']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                              styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        total_time = sum(r[4] for r in app_data)
        hrs, mins = total_time // 3600, (total_time % 3600) // 60
        
        summary = [
            ['Metric', 'Value'],
            ['Total Time', f'{hrs}h {mins}m'],
            ['Apps Used', str(len(set(r[0] for r in app_data)))],
            ['Sessions', str(len(app_data))]
        ]
        
        t = Table(summary, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#007AFF')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
        
        # Top Apps
        app_totals = {}
        for r in app_data:
            app_totals[r[0]] = app_totals.get(r[0], 0) + r[4]
        
        top_apps = sorted(app_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        app_table = [['Application', 'Time']]
        for app, dur in top_apps:
            h, m = dur // 3600, (dur % 3600) // 60
            app_table.append([app, f'{h}h {m}m'])
        
        t2 = Table(app_table, colWidths=[3*inch, 2*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34C759')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Top Applications", styles['Heading2']))
        story.append(t2)
        
        doc.build(story)


class BackupManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.backup_dir = Path(__file__).parent / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self.settings_file = self.backup_dir / 'settings.json'
        self.load_settings()
    
    def load_settings(self):
        if self.settings_file.exists():
            with open(self.settings_file) as f:
                self.settings = json.load(f)
        else:
            self.settings = {'auto_backup': False, 'max_backups': 10}
            self.save_settings()
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def create_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'backup_{timestamp}.db'
        shutil.copy2(self.db_manager.db_path, backup_path)
        self.cleanup_old_backups()
        return backup_path
    
    def restore_backup(self, backup_path):
        self.create_backup()  # Backup current before restoring
        shutil.copy2(backup_path, self.db_manager.db_path)
    
    def list_backups(self):
        backups = []
        for f in self.backup_dir.glob('backup_*.db'):
            stat = f.stat()
            backups.append({
                'path': f,
                'name': f.name,
                'date': datetime.fromtimestamp(stat.st_mtime),
                'date_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
        return sorted(backups, key=lambda x: x['date'], reverse=True)
    
    def cleanup_old_backups(self):
        backups = self.list_backups()
        max_backups = self.settings.get('max_backups', 10)
        if len(backups) > max_backups:
            for backup in backups[max_backups:]:
                backup['path'].unlink()


class AutoBackupSettingsDialog(QDialog):
    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.setWindowTitle("Auto-Backup Settings")
        self.setFixedSize(400, 250)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Enable checkbox
        self.enable_cb = QCheckBox("Enable Auto-Backup")
        self.enable_cb.setChecked(self.backup_manager.settings.get('auto_backup', False))
        layout.addWidget(self.enable_cb)
        
        # Max backups
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Keep last:"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 50)
        self.max_spin.setValue(self.backup_manager.settings.get('max_backups', 10))
        max_layout.addWidget(self.max_spin)
        max_layout.addWidget(QLabel("backups"))
        max_layout.addStretch()
        layout.addLayout(max_layout)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        self.backup_manager.settings['auto_backup'] = self.enable_cb.isChecked()
        self.backup_manager.settings['max_backups'] = self.max_spin.value()
        self.backup_manager.save_settings()
        self.accept()
