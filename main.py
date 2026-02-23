"""
main.py - Main entry point for Ray Tracing & Refractive Index Fitting Application
"""

import sys
import logging
import multiprocessing
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from gui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ray_tracing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    multiprocessing.freeze_support()
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Ray Tracing BOS")
        app.setOrganizationName("Nanolab")

        app.setWindowIcon(QIcon("resources/icon.ico"))

        window = MainWindow()
        window.setWindowIcon(QIcon("resources/icon.ico"))

        # Set application-wide font
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("Application started successfully")

        # Execute application
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()