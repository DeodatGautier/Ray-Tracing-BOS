"""
gui/widgets/base_plot_widget.py - Base plot widget
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class BasePlotWidget(QWidget):
    """Base widget for matplotlib plots."""

    def __init__(self, parent=None, figsize=(10, 8)):
        super().__init__(parent)

        self.figure = Figure(figsize=figsize, dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.axes = None

    def export_plot(self, file_path: str):
        """Export plot to file."""
        self.figure.savefig(file_path, dpi=300, bbox_inches='tight')

    def reset_view(self):
        """Reset plot view to default."""
        if self.axes is not None:
            if hasattr(self.axes, '__iter__'):
                for ax in self.axes.flat:
                    ax.relim()
                    ax.autoscale_view()
            else:
                self.axes.relim()
                self.axes.autoscale_view()
            self.canvas.draw()

    def clear_plot(self):
        """Clear the plot."""
        self.figure.clear()
        self.canvas.draw()