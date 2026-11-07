"""Quant Dark Pro Theme & Global QSS Stylesheet for Qlib Studio."""

from __future__ import annotations

# Color Tokens (TradingView / Bloomberg Financial Dark Pro Palette)
BG_CANVAS = "#0B0E14"
BG_SURFACE = "#131722"
BG_ELEVATED = "#1A2030"
BG_INPUT = "#0E131D"
BORDER_SUBTLE = "#21283B"
BORDER_FOCUS = "#2962FF"

TEXT_PRIMARY = "#E6EDF3"
TEXT_SECONDARY = "#8B949E"
TEXT_MUTED = "#586069"

ACCENT_BLUE = "#2962FF"
ACCENT_BLUE_HOVER = "#3D73FF"
ACCENT_CYAN = "#00E5FF"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_AMBER = "#F5A623"
ACCENT_GREEN = "#00C087"
ACCENT_RED = "#FF4D4F"


QUANT_DARK_QSS = f"""
/* Global Window & Base Widgets */
QMainWindow, QDialog {{
    background-color: {BG_CANVAS};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    selection-background-color: {ACCENT_BLUE};
    selection-color: #FFFFFF;
}}

/* Card Panels */
QFrame#CardFrame {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 8px;
}}

QFrame#CardFrameHover:hover {{
    background-color: {BG_ELEVATED};
    border: 1px solid #2E3A59;
    border-radius: 8px;
}}

QFrame#TopHeaderBar {{
    background-color: #0E121B;
    border-bottom: 1px solid {BORDER_SUBTLE};
}}

QFrame#LeftNavigationBar {{
    background-color: #0E121B;
    border-right: 1px solid {BORDER_SUBTLE};
}}

QFrame#BottomLogDrawer {{
    background-color: #0D1119;
    border-top: 1px solid {BORDER_SUBTLE};
}}

/* Typography Helpers */
QLabel#PageTitle {{
    font-size: 19px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.3px;
}}

QLabel#PageSubtitle {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

QLabel#SectionTitle {{
    font-size: 14px;
    font-weight: 600;
    color: #F0F6FC;
}}

QLabel#FieldLabel {{
    font-size: 12px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
}}

/* Buttons */
QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A334B;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: #242C42;
    border-color: #3B486B;
}}

QPushButton:pressed {{
    background-color: #181E2E;
}}

QPushButton:disabled {{
    background-color: #12151E;
    color: {TEXT_MUTED};
    border-color: #1B202E;
}}

QPushButton#PrimaryButton {{
    background-color: {ACCENT_BLUE};
    color: #FFFFFF;
    border: 1px solid #4175FF;
    font-weight: 700;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {ACCENT_BLUE_HOVER};
    border-color: #628DFF;
}}

QPushButton#SuccessButton {{
    background-color: #00A876;
    color: #FFFFFF;
    border: 1px solid #00C087;
    font-weight: 700;
}}

QPushButton#SuccessButton:hover {{
    background-color: #00C087;
}}

QPushButton#DangerButton {{
    background-color: #C93638;
    color: #FFFFFF;
    border: 1px solid #FF4D4F;
    font-weight: 700;
}}

QPushButton#DangerButton:hover {{
    background-color: #E04345;
}}

/* Navigation Sidebar Buttons */
QPushButton#NavButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    text-align: left;
    padding: 11px 16px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#NavButton:hover {{
    background-color: #151B28;
    color: #FFFFFF;
}}

QPushButton#NavButton[active="true"] {{
    background-color: #161F35;
    color: #FFFFFF;
    border-left: 3px solid {ACCENT_BLUE};
}}

/* Inputs, ComboBoxes, SpinBoxes */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 5px;
    padding: 5px 9px;
    min-height: 20px;
    font-family: "JetBrains Mono", "Consolas", "Segoe UI", monospace;
    font-size: 12px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
    background-color: #111726;
}}

QComboBox::drop-down {{
    border: none;
    width: 22px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid #2E3A59;
    selection-background-color: {ACCENT_BLUE};
    outline: 0;
}}

/* CheckBox */
QCheckBox {{
    spacing: 7px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #35415E;
    background-color: {BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

/* Tables */
QTableWidget, QTableView {{
    background-color: {BG_SURFACE};
    alternate-background-color: #10141F;
    color: {TEXT_PRIMARY};
    gridline-color: #1C2233;
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 6px;
    selection-background-color: #1D2C52;
    selection-color: #FFFFFF;
    font-family: "JetBrains Mono", "Consolas", "Microsoft YaHei UI", monospace;
    font-size: 12px;
}}

QHeaderView::section {{
    background-color: #0F131E;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    font-size: 11px;
    padding: 7px 8px;
    border: none;
    border-bottom: 1px solid {BORDER_SUBTLE};
    border-right: 1px solid #181E2C;
}}

/* TabWidget */
QTabWidget::pane {{
    border: 1px solid {BORDER_SUBTLE};
    background-color: {BG_SURFACE};
    border-radius: 6px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: #0F131D;
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_SUBTLE};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 16px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 12px;
}}

QTabBar::tab:selected {{
    background-color: {BG_SURFACE};
    color: #FFFFFF;
    border-top: 2px solid {ACCENT_BLUE};
}}

QTabBar::tab:hover:!selected {{
    background-color: #161C2B;
    color: {TEXT_PRIMARY};
}}

/* Splitter */
QSplitter::handle {{
    background-color: {BORDER_SUBTLE};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* ProgressBar */
QProgressBar {{
    background-color: #0D111A;
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 4px;
    text-align: center;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
    max-height: 16px;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_BLUE}, stop:1 {ACCENT_CYAN});
    border-radius: 3px;
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #283147;
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #3B4868;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: #283147;
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""
