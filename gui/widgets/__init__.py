"""
gui.widgets package - Custom widget components
"""

from .base_plot_widget import BasePlotWidget
from .plot_widgets import (
    TopDownWidget,
    PlotWidget2D,
    ComparisonPlotWidget
)

__all__ = [
    'BasePlotWidget',
    'TopDownWidget',
    'PlotWidget2D',
    'ComparisonPlotWidget'
]