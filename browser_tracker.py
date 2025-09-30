#!/usr/bin/env python3
"""
Browser Tracker Module for Puthu Tracker
Enhanced browser monitoring with tab tracking capabilities
"""

import json
import sqlite3
import subprocess
import re
from datetime import datetime
from pathlib import Path
import psutil

class BrowserTracker:
    """Enhanced browser tracking with tab title extraction"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.supported_browsers = {
            'chrome.exe': 'Google Chrome',
            'firefox.exe': 'Mozilla Firefox',
            'msedge.exe': 'Microsoft Edge',
            'opera.exe': 'Opera',
            'brave.exe': 'Brave Browser',
            'iexplore.exe': 'Internet Explorer'
        }
        self.current_browser_session = None
    
    def is_browser(self, app_name):
        """Check if the application is a supported browser"""
        return app_name.lower() in self.supported_browsers
    
    def get_browser_name(self, app_name):
        """Get friendly browser name"""
        return self.supported_browsers.get(app_name.lower(), app_name)
    
    def extract_url_from_title(self, window_title):
        """Extract URL information from browser window title"""
        # Common patterns for different browsers
        patterns = [
            r'https?://[^\s\-]+',  # Direct URL pattern
            r'([^-]+) - Google Chrome',  # Chrome pattern
            r'([^-]+) - Mozilla Firefox',  # Firefox pattern
            r'([^-]+) - Microsoft Edge',  # Edge pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, window_title)
            if match:
                return match.group(1).strip()
        
        return window_title
    
    def get_active_tabs(self, browser_name):
        """Get active tabs for supported browsers (Windows-specific)"""
        try:
            if 'chrome' in browser_name.lower():
                return self._get_chrome_tabs()
            elif 'firefox' in browser_name.lower():
                return self._get_firefox_tabs()
            elif 'edge' in browser_name.lower():
                return self._get_edge_tabs()
        except Exception as e:
            print(f"Error getting tabs for {browser_name}: {e}")
        
        return []
    
    def _get_chrome_tabs(self):
        """Get Chrome tabs using debugging port (if enabled)"""
        try:
            # This requires Chrome to be started with --remote-debugging-port=9222
            import requests
            response = requests.get('http://localhost:9222/json/tabs', timeout=1)
            if response.status_code == 200:
                tabs = response.json()
                return [(tab.get('title', 'Unknown'), tab.get('url', '')) for tab in tabs]
        except:
            pass
        return []
    
    def _get_firefox_tabs(self):
        """Get Firefox tabs (limited without extensions)"""
        # Firefox tab extraction is more complex and typically requires extensions
        return []
    
    def _get_edge_tabs(self):
        """Get Edge tabs using similar method to Chrome"""
        try:
            import requests
            response = requests.get('http://localhost:9223/json/tabs', timeout=1)
            if response.status_code == 200:
                tabs = response.json()
                return [(tab.get('title', 'Unknown'), tab.get('url', '')) for tab in tabs]
        except:
            pass
        return []
    
    def track_browser_session(self, browser_app, window_title, start_time, end_time, duration):
        """Track browser session with enhanced data"""
        browser_name = self.get_browser_name(browser_app)
        tab_title = self.extract_url_from_title(window_title)
        
        # Try to get URL if possible
        url = ""
        active_tabs = self.get_active_tabs(browser_name)
        if active_tabs:
            # Find matching tab
            for title, tab_url in active_tabs:
                if title in window_title or window_title in title:
                    url = tab_url
                    break
        
        # Save to database
        self.db_manager.save_browser_usage(
            browser_name,
            tab_title,
            url,
            start_time.isoformat() if isinstance(start_time, datetime) else start_time,
            end_time.isoformat() if isinstance(end_time, datetime) else end_time,
            duration
        )
    
    def get_browser_stats(self, date=None):
        """Get browser usage statistics"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        browser_data = self.db_manager.get_browser_usage_by_date(date)
        
        # Process data for analytics
        stats = {
            'total_browser_time': 0,
            'browsers_used': set(),
            'most_visited_sites': {},
            'browser_breakdown': {}
        }
        
        for browser_name, tab_title, duration in browser_data:
            stats['total_browser_time'] += duration
            stats['browsers_used'].add(browser_name)
            
            if browser_name not in stats['browser_breakdown']:
                stats['browser_breakdown'][browser_name] = 0
            stats['browser_breakdown'][browser_name] += duration
            
            # Extract domain from tab title for site stats
            domain = self._extract_domain(tab_title)
            if domain:
                if domain not in stats['most_visited_sites']:
                    stats['most_visited_sites'][domain] = 0
                stats['most_visited_sites'][domain] += duration
        
        # Convert set to list for JSON serialization
        stats['browsers_used'] = list(stats['browsers_used'])
        
        # Sort most visited sites
        stats['most_visited_sites'] = dict(sorted(
            stats['most_visited_sites'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return stats
    
    def _extract_domain(self, title_or_url):
        """Extract domain from title or URL"""
        # Simple domain extraction
        patterns = [
            r'https?://(?:www\.)?([^/]+)',
            r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title_or_url)
            if match:
                return match.group(1)
        
        return None

class ProductivityAnalyzer:
    """Analyze productivity based on application usage"""
    
    def __init__(self, category_manager=None):
        # Use shared category manager if provided, otherwise load default categories
        self.category_manager = category_manager
        if not category_manager:
            self.productivity_categories = self._load_categories()
    
    def _load_categories(self):
        """Load productivity categories (fallback if no category_manager)"""
        return {
            'productive': [
                'code.exe', 'devenv.exe', 'pycharm64.exe', 'idea64.exe',
                'sublime_text.exe', 'notepad++.exe', 'atom.exe', 'vscode.exe',
                'excel.exe', 'winword.exe', 'powerpnt.exe', 'onenote.exe',
                'outlook.exe', 'teams.exe', 'slack.exe', 'zoom.exe'
            ],
            'neutral': [
                'chrome.exe', 'firefox.exe', 'msedge.exe', 'explorer.exe',
                'notepad.exe', 'calculator.exe', 'cmd.exe', 'powershell.exe'
            ],
            'entertainment': [
                'steam.exe', 'discord.exe', 'spotify.exe', 'vlc.exe',
                'netflix.exe', 'youtube.exe', 'games.exe', 'photoshop.exe'
            ],
            'social': [
                'whatsapp.exe', 'telegram.exe', 'skype.exe', 'facebook.exe',
                'instagram.exe', 'twitter.exe', 'linkedin.exe'
            ]
        }
    
    def categorize_app(self, app_name):
        """Categorize application by productivity"""
        # Use shared category manager if available
        if self.category_manager:
            return self.category_manager.get_app_category(app_name)
        
        # Fallback to local categories
        app_lower = app_name.lower()
        
        for category, apps in self.productivity_categories.items():
            if app_lower in apps:
                return category
        
        return 'uncategorized'
    
    def calculate_productivity_score(self, usage_data):
        """Calculate productivity score based on usage"""
        category_weights = {
            'productive': 1.0,
            'neutral': 0.5,
            'entertainment': -0.3,
            'social': -0.2,
            'uncategorized': 0.0
        }
        
        total_time = 0
        weighted_score = 0
        
        for app_name, duration in usage_data:
            category = self.categorize_app(app_name)
            weight = category_weights.get(category, 0.0)
            
            total_time += duration
            weighted_score += duration * weight
        
        if total_time == 0:
            return 50  # Neutral score
        
        # Normalize to 0-100 scale
        raw_score = (weighted_score / total_time) * 100
        # Adjust to make 50 the neutral point
        productivity_score = max(0, min(100, 50 + raw_score))
        
        return round(productivity_score, 1)
    
    def get_productivity_insights(self, usage_data):
        """Get detailed productivity insights"""
        categorized_time = {
            'productive': 0,
            'neutral': 0,
            'entertainment': 0,
            'social': 0,
            'uncategorized': 0
        }
        
        for app_name, duration in usage_data:
            category = self.categorize_app(app_name)
            categorized_time[category] += duration
        
        total_time = sum(categorized_time.values())
        
        insights = {
            'productivity_score': self.calculate_productivity_score(usage_data),
            'time_breakdown': categorized_time,
            'time_percentages': {
                category: round((time / total_time * 100), 1) if total_time > 0 else 0
                for category, time in categorized_time.items()
            },
            'recommendations': self._generate_recommendations(categorized_time, total_time)
        }
        
        return insights
    
    def _generate_recommendations(self, categorized_time, total_time):
        """Generate productivity recommendations"""
        recommendations = []
        
        if total_time == 0:
            return ["Start tracking to get personalized recommendations!"]
        
        productive_percentage = (categorized_time['productive'] / total_time) * 100
        entertainment_percentage = (categorized_time['entertainment'] / total_time) * 100
        
        if productive_percentage < 30:
            recommendations.append("Consider dedicating more time to productive applications")
        elif productive_percentage > 70:
            recommendations.append("Great job maintaining high productivity!")
        
        if entertainment_percentage > 40:
            recommendations.append("Try to balance entertainment time with productive activities")
        
        if categorized_time['social'] > 3600:  # More than 1 hour
            recommendations.append("Consider setting time limits for social applications")
        
        return recommendations if recommendations else ["Keep up the balanced usage!"]

# Export classes for use in main application
__all__ = ['BrowserTracker', 'ProductivityAnalyzer']
