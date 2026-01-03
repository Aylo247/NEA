import json
from typing import Dict
from PyQt5.QtGui import QColor

class ThemeManager:
    """
    manages application themes, including loading theme definitions from JSON,
    generating QSS strings for PyQt5 widgets, and retrieving colors/fonts
    """

    def __init__(self, themes_file: str = "themes.json") -> None:
        """initialize the ThemeManager with a JSON file path"""
        self.themes_file = themes_file
        self.themes = self._load_themes()

    def _load_themes(self) -> dict:
        """load theme definitions from a JSON file"""
        try:
            with open(self.themes_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_theme(self, theme_name: str) -> str:
        """get the QSS string for a theme"""
        if not theme_name:
            return ""
        theme = self.themes.get(theme_name.lower(), {})
        return self.theme_to_qss(theme)

    def get_theme_dict(self, theme_name: str) -> Dict:
        """get the raw theme dictionary"""
        if not theme_name:
            return {}
        return self.themes.get(theme_name.lower(), {})

    def theme_to_qss(self, theme: dict) -> str:
        """convert a theme dictionary into a PyQt5 QSS stylesheet"""
        return f"""
        * {{
            font-family: "{theme.get('font', 'Helvetica Neue')}";
            color: {theme.get('font_color', theme.get('label_color', '#000000'))};
        }}
        QMainWindow {{ background-color: {theme.get('window_bg', '#FFFFFF')}; }}
        QWidget {{ background-color: {theme.get('background', '#FFFFFF')}; color: {theme.get('label_color', '#000000')}; }}
        QGroupBox {{
            background-color: {theme.get('groupbox_bg', '#FFFFFF')};
            border: 1px solid {theme.get('border_color', '#000000')};
            border-radius: 6px;
            margin-top: 27px;
            padding: 6px;
        }}
        QLabel {{ color: {theme.get('label_color', '#000000')}; background-color: transparent; }}
        QPushButton {{
            background-color: {theme.get('button_bg', '#DDDDDD')};
            color: {theme.get('button_fg', '#000000')};
            border: 1px solid {theme.get('border_color', '#000000')};
            border-radius: 6px;
            padding: 6px 10px;
        }}
        QPushButton:hover {{ background-color: {theme.get('button_hover', '#CCCCCC')}; }}
        QLineEdit, QTextEdit {{
            color: {theme.get('lineedit_fg', '#000000')};
            background-color: {theme.get('lineedit_bg', '#FFFFFF')};
            border: 1px solid {theme.get('border_color', '#000000')};
            border-radius: 4px;
            padding: 2px 4px;
        }}
        QComboBox {{
            color: {theme.get('combobox_fg', '#000000')};
            background-color: {theme.get('combobox_bg', '#FFFFFF')};
            border: 1px solid {theme.get('border_color', '#000000')};
            border-radius: 4px;
            padding: 2px 4px;
        }}
        QCheckBox {{
            color: {theme.get('checkbox_fg', '#000000')};
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{ background: {theme.get('scrollbar_bg', '#E0E0E0')}; }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {theme.get('scrollbar_fg', '#C0C0C0')};
            border-radius: 4px;
        }}
        QTableWidget {{
            background-color: {theme.get('table_bg', '#FFFFFF')};
            color: {theme.get('table_fg', '#000000')};
            gridline-color: {theme.get('calendar_grid_light', '#EAEAEA')};
        }}
        QHeaderView::section {{
            background-color: {theme.get('table_header_bg', '#E5E5E5')};
            color: {theme.get('table_header_fg', '#000000')};
            border: 1px solid {theme.get('border_color', '#000000')};
            padding: 4px;
            font-weight: bold;
        }}
        """

    def get_colour(self, theme_name: str, key: str, fallback: str = "#000000") -> QColor:
        """get a QColor object for a specific theme key"""
        theme = self.get_theme_dict(theme_name)
        return QColor(theme.get(key, fallback))

    def get_font(self, theme_name: str, fallback: str = "Arial") -> str:
        """get the font for a theme"""
        theme = self.get_theme_dict(theme_name)
        return theme.get("font", fallback)
