#!/usr/bin/env python3
"""
Category Manager - Helper for managing app categories inline
"""

import json
import os
from PyQt6.QtWidgets import QComboBox, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QObject, pyqtSignal
from PyQt6.QtGui import QCursor

class CategoryManager(QObject):
    """Manages app categories and provides utilities for category dropdowns"""
    
    # Signal emitted when categories are updated
    categories_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.categories_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_categories.json')
        self.app_categories = self.load_categories()
    
    def load_categories(self):
        """Load app categories from JSON file"""
        if os.path.exists(self.categories_file):
            try:
                with open(self.categories_file, 'r') as f:
                    categories = json.load(f)
                    # Ensure all required categories exist
                    default_cats = self.get_default_categories()
                    for cat in default_cats:
                        if cat not in categories:
                            categories[cat] = default_cats[cat]
                    return categories
            except Exception as e:
                print(f"Error loading categories: {e}")
        return self.get_default_categories()
    
    def get_default_categories(self):
        """Return default app categorizations"""
        return {
            'productive': ['code', 'visual studio', 'pycharm', 'intellij', 'vscode', 'excel', 'word', 
                          'powerpoint', 'outlook', 'teams', 'slack', 'github', 'terminal', 'cmd',
                          'sublime', 'atom', 'webstorm', 'rider', 'clion', 'datagrip', 'lenovovantage'],
            'entertainment': ['spotify', 'netflix', 'youtube', 'prime', 'vlc', 'steam', 'epic', 
                            'twitch', 'discord', 'reddit', 'hulu', 'disneyplus', 'hbo'],
            'neutral': ['chrome', 'firefox', 'edge', 'safari', 'brave', 'explorer', 'finder', 
                       'notepad', 'calculator', 'file', 'task', 'photoshop'],
            'social': ['messenger', 'telegram', 'signal', 'skype', 'zoom', 'whatsapp', 'snapchat',
                      'instagram', 'facebook', 'twitter'],
            'uncategorized': ['python']
        }
    
    def save_categories(self):
        """Save categories to JSON file"""
        try:
            with open(self.categories_file, 'w') as f:
                json.dump(self.app_categories, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving categories: {e}")
            return False
    
    def get_app_category(self, app_name):
        """Get category for an app"""
        app_lower = app_name.lower().replace('.exe', '')
        
        for category, apps in self.app_categories.items():
            for pattern in apps:
                if pattern.lower() in app_lower:
                    return category
        
        return 'uncategorized'
    
    def update_app_category(self, app_name, new_category):
        """Update category for an app"""
        # Clean app name
        app_pattern = app_name.lower().replace('.exe', '').strip()
        
        # Remove from all categories
        for category in self.app_categories:
            if app_pattern in self.app_categories[category]:
                self.app_categories[category].remove(app_pattern)
        
        # Add to new category
        if new_category not in self.app_categories:
            self.app_categories[new_category] = []
        
        if app_pattern not in self.app_categories[new_category]:
            self.app_categories[new_category].append(app_pattern)
        
        # Save changes
        result = self.save_categories()
        
        # Emit signal to notify listeners that categories have changed
        if result:
            self.categories_updated.emit()
        
        return result
    
    def create_category_combo(self, app_name, theme, is_dark, on_change_callback=None):
        """Create a styled combo box for category selection"""
        combo = QComboBox()
        combo.addItems(['Productive', 'Entertainment', 'Neutral', 'Social', 'Other'])
        
        # Set current selection
        current_category = self.get_app_category(app_name)
        if current_category == 'uncategorized':
            combo.setCurrentText('Other')
        else:
            combo.setCurrentText(current_category.capitalize())
        
        # Properties - use setFixedSize for absolute control
        combo.setEditable(False)
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        combo.setFixedSize(QSize(135, 32))  # Fixed size - this is the key!
        
        # Apply styling
        combo_style = self.get_combo_style(theme, is_dark)
        combo.setStyleSheet(combo_style)
        
        # Connect change handler
        if on_change_callback:
            combo.currentTextChanged.connect(lambda text: on_change_callback(app_name, text))
        
        return combo
    
    def get_combo_style(self, theme, is_dark):
        """Get combo box style"""
        return f"""
            QComboBox {{
                background-color: {theme['panel_bg']};
                border: 2px solid {theme['border']};
                border-radius: 6px;
                padding-left: 10px;
                padding-right: 25px;
                padding-top: 3px;
                padding-bottom: 3px;
                color: {theme['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }}
            QComboBox:hover {{ 
                border-color: #007AFF;
                background-color: {theme.get('table_hover', theme['panel_bg'])};
            }}
            QComboBox:focus {{
                border-color: #007AFF;
            }}
            QComboBox::drop-down {{ 
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 22px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{ 
                width: 0px;
                height: 0px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {theme['text_primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['panel_bg']};
                border: 2px solid #007AFF;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                selection-background-color: #007AFF;
                selection-color: white;
                color: {theme['text_primary']};
                outline: none;
                padding: 2px 0;
            }}
            QComboBox QAbstractItemView::item {{
                height: 30px;
                padding-left: 10px;
                padding-right: 10px;
                color: {theme['text_primary']};
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #007AFF;
                color: white;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #007AFF;
                color: white;
            }}
        """
    
    def get_category_color(self, category):
        """Get color for a category"""
        colors = {
            'productive': '#34C759', 
            'entertainment': '#FF3B30', 
            'social': '#FF9500', 
            'neutral': '#007AFF', 
            'uncategorized': '#8E8E93'
        }
        return colors.get(category, '#8E8E93')
