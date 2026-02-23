"""
gui/widgets/styles.py - Centralized styling - OPTIMIZED FOR MINIMALISM
"""

# Application stylesheet - MINIMAL VERSION
APP_STYLESHEET = """
    QMainWindow {
        background-color: #f8f9fa;
    }
    QWidget {
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 9pt;
    }
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 12px;
        background-color: white;
        font-weight: 500;
        color: #2d3748;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 6px;
        color: #4a5568;
    }
    QPushButton {
        background-color: #4a6ee0;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        font-weight: 500;
        min-height: 28px;
    }
    QPushButton:hover {
        background-color: #3a5ed0;
    }
    QPushButton:pressed {
        background-color: #2a4ec0;
    }
    QPushButton:disabled {
        background-color: #cbd5e0;
        color: #718096;
    }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
        border: 1px solid #cbd5e0;
        border-radius: 3px;
        padding: 4px 6px;
        background-color: white;
        min-height: 24px;
        font-size: 9pt;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #4a6ee0;
        background-color: #f7fafc;
    }
    QTabWidget::pane {
        border: 1px solid #e2e8f0;
        background-color: white;
        border-radius: 4px;
    }
    QTabBar::tab {
        background-color: #edf2f7;
        padding: 6px 12px;
        margin-right: 2px;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: white;
        border-bottom: 2px solid #4a6ee0;
        color: #4a6ee0;
    }
    QTabBar::tab:hover:!selected {
        background-color: #e2e8f0;
    }
    QStatusBar {
        background-color: #2d3748;
        color: #e2e8f0;
        padding: 3px;
        font-size: 8pt;
    }
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    QScrollBar:vertical {
        border: none;
        background: #edf2f7;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #a0aec0;
        border-radius: 4px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #718096;
    }
    QTableWidget {
        border: 1px solid #e2e8f0;
        background-color: white;
        gridline-color: #edf2f7;
        font-size: 9pt;
    }
    QTableWidget::item {
        padding: 3px;
    }
    QHeaderView::section {
        background-color: #f7fafc;
        padding: 4px;
        border: none;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 500;
    }
    QLabel {
        color: #4a5568;
    }
    QMenuBar {
        background-color: #f8f9fa;
        border-bottom: 1px solid #e2e8f0;
        padding: 2px;
    }
    QMenuBar::item {
        padding: 4px 8px;
        border-radius: 3px;
        spacing: 3px;
        background-color: transparent;
    }
    QMenuBar::item:selected {
        background-color: #e2e8f0;
    }
    QMenuBar::item:pressed {
        background-color: #cbd5e0;
    }
    QMenu {
        background-color: white;
        border: 1px solid #cbd5e0;
        border-radius: 4px;
        padding: 4px 0px;
    }
    QMenu::item {
        padding: 4px 24px 4px 8px;
        background-color: transparent;
        color: #2d3748;
    }
    QMenu::item:selected {
        background-color: #e2e8f0;
    }
    QMenu::item:pressed {
        background-color: #cbd5e0;
    }
    QMenu::icon {
        padding-left: 4px;
        width: 20px;
    }
    QMenu::separator {
        height: 1px;
        background-color: #e2e8f0;
        margin: 4px 10px;
    }
"""

# Compact form style
COMPACT_FORM_STYLE = """
    QLabel {
        font-size: 9pt;
        color: #4a5568;
        padding-right: 4px;
    }
    QDoubleSpinBox, QSpinBox {
        max-width: 90px;
        font-size: 9pt;
    }
"""

# Minimal groupbox style
GROUPBOX_MINIMAL_STYLE = """
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 5px;
        margin-top: 8px;
        padding-top: 10px;
        background-color: white;
        font-weight: 500;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 6px;
        padding: 0 5px;
        color: #4a5568;
    }
"""

# Specific widget styles - COMPACT VERSION
FUNCTION_DESC_STYLE = """
    QLabel {
        padding: 6px;
        background-color: #f0f9ff;
        border-radius: 3px;
        border-left: 2px solid #4a6ee0;
        color: #2b6cb0;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 8pt;
        line-height: 1.2;
    }
"""

DATA_INFO_STYLE = """
    QLabel {
        padding: 8px;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        color: #4a5568;
        font-weight: 500;
        font-size: 9pt;
        line-height: 1.3;
    }
"""

STATS_STYLE = """
    QLabel {
        padding: 8px;
        background: linear-gradient(135deg, #e7f5ff 0%, #d0ebff 100%);
        border-radius: 4px;
        border: 1px solid #a5d8ff;
        color: #1864ab;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 8pt;
        line-height: 1.4;
    }
"""

RESULTS_TEXT_STYLE = """
    QTextEdit {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 8px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 9pt;
        line-height: 130%;
    }
"""

# Button styles - COMPACT VERSION
SIMULATION_BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #38a169, stop:1 #2f855a);
        color: white;
        font-weight: 600;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 10pt;
        min-height: 32px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #2f855a, stop:1 #276749);
    }
    QPushButton:pressed {
        background: #276749;
    }
"""

OPTIMIZATION_BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #4a6ee0, stop:1 #3a5ed0);
        color: white;
        font-weight: 600;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 10pt;
        min-height: 32px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3a5ed0, stop:1 #2a4ec0);
    }
    QPushButton:pressed {
        background: #2a4ec0;
    }
"""