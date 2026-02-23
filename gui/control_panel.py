"""
gui/control_panel.py - Control panel widget with preset support and improved data loading.
"""

from typing import Dict, List
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QScrollArea, QFrame, QGridLayout, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
import json

from core.refractive_index import RefractiveIndexType
from utils.constants import (
    FunctionType, DEFAULT_GRID_SIZE, DEFAULT_BOUNDS,
    DEFAULT_NUM_RAYS, DEFAULT_STEP_SIZE, DEFAULT_MAX_STEPS,
    DEFAULT_LEARNING_RATE, DEFAULT_EPSILON, DEFAULT_MAX_ITERATIONS,
    PARAMETER_DESCRIPTIONS
)
from gui.widgets.styles import (
    FUNCTION_DESC_STYLE, SIMULATION_BUTTON_STYLE, OPTIMIZATION_BUTTON_STYLE,
    GROUPBOX_MINIMAL_STYLE
)


class ControlPanel(QWidget):
    """Control panel for simulation and optimization parameters."""

    simulation_requested = pyqtSignal()
    optimization_requested = pyqtSignal()
    function_changed = pyqtSignal(str)
    load_data_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.function_type = FunctionType.GAUSSIAN
        # Default parameters: A = 1.000292 (air), B = 1.001, C = 0.5, D = 2.0, X0 = 0.0
        self.function_params = [1.000292, 1.001, 0.5, 2.0, 0.0]
        self.experimental_data = None
        self.use_geometry = True

        self.init_ui()
        self.update_function_description()   # ensure description is shown at startup

    def init_ui(self):
        """Initialize all UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(4, 4, 4, 4)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(8)
        container_layout.setContentsMargins(2, 2, 2, 2)

        # Experimental Data Group
        data_group = self._create_data_group()
        container_layout.addWidget(data_group)

        # Function Selection Group (with Fix A and parameters)
        func_group = self._create_function_group()
        container_layout.addWidget(func_group)

        # Geometry Group
        geo_group = self._create_geometry_group()
        container_layout.addWidget(geo_group)

        # Parameters Grid (simulation & optimization)
        params_group = self._create_parameters_grid()
        container_layout.addWidget(params_group)

        # Action Buttons
        btn_group = self._create_button_group()
        container_layout.addWidget(btn_group)

        container_layout.addStretch()
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

    def _create_data_group(self) -> QGroupBox:
        """Create the experimental data group."""
        group = QGroupBox("📊 Experimental Data")
        group.setStyleSheet(GROUPBOX_MINIMAL_STYLE)
        group.setMinimumHeight(120)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 10, 6, 6)

        self.data_info_label = QLabel("📁 No data loaded")
        self.data_info_label.setWordWrap(True)
        self.data_info_label.setStyleSheet("""
            QLabel {
                padding: 6px;
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-radius: 4px;
                border: 1px solid #e2e8f0;
                color: #4a5568;
                font-weight: 500;
                font-size: 9pt;
                min-height: 50px;
                line-height: 1.3;
            }
        """)
        self.data_info_label.setMinimumHeight(50)
        layout.addWidget(self.data_info_label)

        self.load_button = QPushButton("📂 Load Experimental Data")
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #4a6ee0;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: 500;
                font-size: 9pt;
                min-height: 26px;
            }
            QPushButton:hover {
                background-color: #3a5ed0;
            }
        """)
        self.load_button.clicked.connect(self.load_data_requested.emit)
        layout.addWidget(self.load_button)

        return group

    def _create_function_group(self) -> QGroupBox:
        """Create the refractive index function group."""
        group = QGroupBox("📈 Refractive Index Function")
        group.setStyleSheet(GROUPBOX_MINIMAL_STYLE)
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 10, 6, 6)

        # Function selection combo
        func_layout = QHBoxLayout()
        func_layout.setSpacing(6)
        func_label = QLabel("Function:")
        func_label.setMinimumWidth(70)
        func_layout.addWidget(func_label)

        self.function_combo = QComboBox()
        self.function_combo.addItems(["Gaussian", "Lorentzian", "Step", "Parabolic", "Linear X"])
        self.function_combo.currentTextChanged.connect(self.on_function_changed)
        func_layout.addWidget(self.function_combo, 1)
        layout.addLayout(func_layout)

        # Function description label
        self.function_desc_label = QLabel()
        self.function_desc_label.setWordWrap(True)
        self.function_desc_label.setStyleSheet(FUNCTION_DESC_STYLE)
        self.function_desc_label.setMaximumHeight(45)
        layout.addWidget(self.function_desc_label)

        # Fix A checkbox
        self.fix_A_cb = QCheckBox("Fix A (background refractive index)")
        layout.addWidget(self.fix_A_cb)

        # Parameter grid (A, B, C, D, X0)
        self.param_widget = QWidget()
        self.param_layout = QGridLayout(self.param_widget)
        self.param_layout.setHorizontalSpacing(8)
        self.param_layout.setVerticalSpacing(4)
        self.param_layout.setContentsMargins(0, 0, 0, 0)

        self.param_spins = []
        param_names = ["A", "B", "C", "D", "X0"]
        descriptions = ["Background index", "Center index", "Width/decay", "Power/steepness", "Horizontal shift (mm)"]

        # Row 0: A, B, C
        for i in range(3):
            label = QLabel(f"{param_names[i]}:")
            label.setToolTip(descriptions[i])
            label.setStyleSheet("font-size: 9pt;")
            self.param_layout.addWidget(label, 0, i*2, Qt.AlignRight | Qt.AlignVCenter)

            spin = QDoubleSpinBox()
            spin.setRange(-10.0 if i == 4 else 0.0, 10.0)  # X0 can be negative
            spin.setDecimals(6)
            spin.setValue(self.function_params[i])
            spin.setSingleStep(0.1)
            spin.setFixedWidth(85)
            spin.setStyleSheet("font-size: 9pt;")
            spin.valueChanged.connect(self.update_function_params)
            self.param_layout.addWidget(spin, 0, i*2+1, Qt.AlignLeft | Qt.AlignVCenter)
            self.param_spins.append(spin)

        # Row 1: D, X0
        for j, i in enumerate([3, 4]):
            label = QLabel(f"{param_names[i]}:")
            label.setToolTip(descriptions[i])
            label.setStyleSheet("font-size: 9pt;")
            self.param_layout.addWidget(label, 1, j*2, Qt.AlignRight | Qt.AlignVCenter)

            spin = QDoubleSpinBox()
            spin.setRange(-10.0 if i == 4 else 0.0, 10000.0 if i == 3 else 10.0)  # D can be large
            spin.setDecimals(6)
            spin.setValue(self.function_params[i])
            spin.setSingleStep(0.1)
            spin.setFixedWidth(85)
            spin.setStyleSheet("font-size: 9pt;")
            spin.valueChanged.connect(self.update_function_params)
            self.param_layout.addWidget(spin, 1, j*2+1, Qt.AlignLeft | Qt.AlignVCenter)
            self.param_spins.append(spin)

        layout.addWidget(self.param_widget)

        return group

    def _create_geometry_group(self) -> QGroupBox:
        """Create the experiment geometry group."""
        group = QGroupBox("📐 Experiment Geometry")
        group.setStyleSheet(GROUPBOX_MINIMAL_STYLE)
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(4)
        layout.setContentsMargins(6, 10, 6, 6)

        self.enable_geometry_cb = QCheckBox("Use geometry")
        self.enable_geometry_cb.setChecked(self.use_geometry)
        self.enable_geometry_cb.toggled.connect(self._on_geometry_toggled)
        layout.addWidget(self.enable_geometry_cb, 0, 0, 1, 4)

        # Row 1: distances
        layout.addWidget(QLabel("BG distance:"), 1, 0)
        self.dist_bg_spin = QDoubleSpinBox()
        self.dist_bg_spin.setRange(10, 2000)
        self.dist_bg_spin.setValue(500.0)
        self.dist_bg_spin.setSuffix(" mm")
        layout.addWidget(self.dist_bg_spin, 1, 1)

        layout.addWidget(QLabel("Lens distance:"), 1, 2)
        self.dist_lens_spin = QDoubleSpinBox()
        self.dist_lens_spin.setRange(10, 2000)
        self.dist_lens_spin.setValue(500.0)
        self.dist_lens_spin.setSuffix(" mm")
        layout.addWidget(self.dist_lens_spin, 1, 3)

        # Row 2: thickness and focal length
        layout.addWidget(QLabel("Thickness:"), 2, 0)
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.1, 200)
        self.thickness_spin.setValue(5.0)
        self.thickness_spin.setSuffix(" mm")
        layout.addWidget(self.thickness_spin, 2, 1)

        layout.addWidget(QLabel("Focal length:"), 2, 2)
        self.focal_spin = QDoubleSpinBox()
        self.focal_spin.setRange(10, 1000)
        self.focal_spin.setValue(100.0)
        self.focal_spin.setSuffix(" mm")
        layout.addWidget(self.focal_spin, 2, 3)

        self._on_geometry_toggled(self.use_geometry)
        return group

    def _on_geometry_toggled(self, checked: bool):
        """Enable/disable geometry spinboxes based on checkbox."""
        self.dist_bg_spin.setEnabled(checked)
        self.dist_lens_spin.setEnabled(checked)
        self.thickness_spin.setEnabled(checked)
        self.focal_spin.setEnabled(checked)

    def _create_parameters_grid(self) -> QGroupBox:
        """Create the simulation and optimization parameters grid."""
        group = QGroupBox("⚙️ Parameters")
        group.setStyleSheet(GROUPBOX_MINIMAL_STYLE)

        grid = QGridLayout(group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        grid.setContentsMargins(8, 12, 8, 8)

        # SIMULATION COLUMN
        sim_label = QLabel("<b>Simulation</b>")
        sim_label.setStyleSheet("color: #2c5282; font-size: 9pt;")
        grid.addWidget(sim_label, 0, 0, 1, 2, Qt.AlignLeft)

        grid.addWidget(QLabel("Grid Size:"), 1, 0, Qt.AlignRight)
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(32, 1024)
        self.grid_spin.setValue(DEFAULT_GRID_SIZE[0])
        self.grid_spin.setFixedWidth(85)
        grid.addWidget(self.grid_spin, 1, 1, Qt.AlignLeft)

        grid.addWidget(QLabel("Bounds:"), 2, 0, Qt.AlignRight)
        self.bounds_spin = QDoubleSpinBox()
        self.bounds_spin.setRange(1.0, 300.0)
        self.bounds_spin.setValue(DEFAULT_BOUNDS)
        self.bounds_spin.setSuffix(" mm")
        self.bounds_spin.setFixedWidth(85)
        grid.addWidget(self.bounds_spin, 2, 1, Qt.AlignLeft)

        grid.addWidget(QLabel("Rays:"), 3, 0, Qt.AlignRight)
        self.rays_spin = QSpinBox()
        self.rays_spin.setRange(10, 1000)
        self.rays_spin.setValue(DEFAULT_NUM_RAYS)
        self.rays_spin.setFixedWidth(85)
        grid.addWidget(self.rays_spin, 3, 1, Qt.AlignLeft)

        # OPTIMIZATION COLUMN
        opt_label = QLabel("<b>Optimization</b>")
        opt_label.setStyleSheet("color: #2c5282; font-size: 9pt;")
        grid.addWidget(opt_label, 0, 2, 1, 2, Qt.AlignLeft)

        grid.addWidget(QLabel("LR:"), 1, 2, Qt.AlignRight)
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.000001, 0.1)
        self.lr_spin.setValue(DEFAULT_LEARNING_RATE)
        self.lr_spin.setDecimals(6)
        self.lr_spin.setFixedWidth(85)
        grid.addWidget(self.lr_spin, 1, 3, Qt.AlignLeft)

        grid.addWidget(QLabel("Epsilon:"), 2, 2, Qt.AlignRight)
        self.eps_spin = QDoubleSpinBox()
        self.eps_spin.setRange(1e-8, 1e-3)
        self.eps_spin.setValue(DEFAULT_EPSILON)
        self.eps_spin.setDecimals(8)
        self.eps_spin.setFixedWidth(85)
        grid.addWidget(self.eps_spin, 2, 3, Qt.AlignLeft)

        grid.addWidget(QLabel("Iterations:"), 3, 2, Qt.AlignRight)
        self.iter_spin = QSpinBox()
        self.iter_spin.setRange(10, 1000)
        self.iter_spin.setValue(DEFAULT_MAX_ITERATIONS)
        self.iter_spin.setFixedWidth(85)
        grid.addWidget(self.iter_spin, 3, 3, Qt.AlignLeft)

        # ADVANCED PARAMETERS
        adv_label = QLabel("<b>Advanced</b>")
        adv_label.setStyleSheet("color: #2c5282; font-size: 9pt;")
        grid.addWidget(adv_label, 4, 0, 1, 4, Qt.AlignLeft)

        grid.addWidget(QLabel("Step Size:"), 5, 0, Qt.AlignRight)
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.0001, 1)
        self.step_spin.setValue(DEFAULT_STEP_SIZE)
        self.step_spin.setDecimals(6)
        self.step_spin.setFixedWidth(85)
        grid.addWidget(self.step_spin, 5, 1, Qt.AlignLeft)

        grid.addWidget(QLabel("Max Steps:"), 5, 2, Qt.AlignRight)
        self.max_steps_spin = QSpinBox()
        self.max_steps_spin.setRange(100, 50000)
        self.max_steps_spin.setValue(DEFAULT_MAX_STEPS)
        self.max_steps_spin.setFixedWidth(85)
        grid.addWidget(self.max_steps_spin, 5, 3, Qt.AlignLeft)

        return group

    def _create_button_group(self) -> QWidget:
        """Create the main action buttons (Simulation, Optimization)."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 4, 0, 4)

        self.sim_button = QPushButton("▶ Run Simulation")
        self.sim_button.setStyleSheet(SIMULATION_BUTTON_STYLE)
        self.sim_button.setMinimumHeight(34)
        self.sim_button.clicked.connect(self.simulation_requested.emit)

        self.opt_button = QPushButton("⚡ Run Optimization")
        self.opt_button.setStyleSheet(OPTIMIZATION_BUTTON_STYLE)
        self.opt_button.setMinimumHeight(34)
        self.opt_button.clicked.connect(self.optimization_requested.emit)
        self.opt_button.setEnabled(False)

        layout.addWidget(self.sim_button)
        layout.addWidget(self.opt_button)

        return widget

    def on_function_changed(self, func_name: str):
        """Handle function type change."""
        if func_name == "Linear X":
            func_type = FunctionType.LINEARX
        else:
            func_type = func_name.lower()
        self.function_type = func_type
        self.update_function_description()
        self.function_changed.emit(func_type)

    def update_function_description(self):
        """Update the function description label with proper HTML entities."""
        formula = RefractiveIndexType.get_formula(self.function_type)
        # Replace < and > with HTML entities for proper display
        formula = formula.replace('<', '&lt;').replace('>', '&gt;')
        self.function_desc_label.setText(f"<i>{formula}</i>")

    def update_function_params(self):
        """Update internal parameter list from spinboxes."""
        for i, spin in enumerate(self.param_spins):
            self.function_params[i] = spin.value()

    def set_experimental_data(self, data: Dict):
        """Update UI with loaded experimental data."""
        self.experimental_data = data
        if data:
            x = data.get('x', [])
            delta = data.get('delta', [])
            info_text = f"""
            <b>📈 Data Loaded</b><br>
            Points: {len(x)}<br>
            X range: {min(x):.2f}–{max(x):.2f} mm<br>
            Δ range: {min(delta):.3f}–{max(delta):.3f} mm
            """
            self.data_info_label.setText(info_text)
            self.opt_button.setEnabled(True)
        else:
            self.data_info_label.setText("📁 No data loaded")
            self.opt_button.setEnabled(False)

    def set_function_parameters(self, params: List[float]):
        """Set the function parameters (list of 5 values)."""
        self.function_params = params[:5]
        for i, spin in enumerate(self.param_spins):
            if i < len(params):
                spin.setValue(params[i])

    def get_function_type(self) -> str:
        return self.function_type

    def get_function_parameters(self) -> List[float]:
        return self.function_params.copy()

    def get_fixed_indices(self) -> List[int]:
        """Return indices of parameters that are fixed (currently only A)."""
        fixed = []
        if self.fix_A_cb.isChecked():
            fixed.append(0)
        return fixed

    def get_simulation_parameters(self) -> Dict:
        return {
            'grid_x': self.grid_spin.value(),
            'grid_y': self.grid_spin.value(),
            'bounds': self.bounds_spin.value(),
            'num_rays': self.rays_spin.value(),
            'step_size': self.step_spin.value(),
            'max_steps': self.max_steps_spin.value()
        }

    def get_optimization_parameters(self) -> Dict:
        return {
            'learning_rate': self.lr_spin.value(),
            'epsilon': self.eps_spin.value(),
            'max_iterations': self.iter_spin.value()
        }

    def get_geometry_parameters(self) -> Dict:
        return {
            'use_geometry': self.enable_geometry_cb.isChecked(),
            'dist_bg': self.dist_bg_spin.value(),
            'dist_lens': self.dist_lens_spin.value(),
            'thickness': self.thickness_spin.value(),
            'focal': self.focal_spin.value()
        }

    def get_all_parameters(self) -> dict:
        """Collect all current settings into a dictionary for saving."""
        return {
            'function_type': self.get_function_type(),
            'function_params': self.get_function_parameters(),
            'fixed_indices': self.get_fixed_indices(),
            'geometry': self.get_geometry_parameters(),
            'simulation': self.get_simulation_parameters(),
            'optimization': self.get_optimization_parameters()
        }

    def set_all_parameters(self, params: dict):
        """Restore all settings from a dictionary."""
        if 'function_type' in params:
            # Convert stored type (e.g., "gaussian") to display name
            display_name = params['function_type'].capitalize()
            idx = self.function_combo.findText(display_name)
            if idx >= 0:
                self.function_combo.setCurrentIndex(idx)
        if 'function_params' in params:
            self.set_function_parameters(params['function_params'])
        if 'fixed_indices' in params:
            # For now we only support fixing A (index 0)
            self.fix_A_cb.setChecked(0 in params['fixed_indices'])
        if 'geometry' in params:
            g = params['geometry']
            self.enable_geometry_cb.setChecked(g.get('use_geometry', True))
            self.dist_bg_spin.setValue(g.get('dist_bg', 500.0))
            self.dist_lens_spin.setValue(g.get('dist_lens', 500.0))
            self.thickness_spin.setValue(g.get('thickness', 5.0))
            self.focal_spin.setValue(g.get('focal', 100.0))
        if 'simulation' in params:
            s = params['simulation']
            self.grid_spin.setValue(s.get('grid_x', 256))
            self.bounds_spin.setValue(s.get('bounds', 10.0))
            self.rays_spin.setValue(s.get('num_rays', 121))
            self.step_spin.setValue(s.get('step_size', 0.008))
            self.max_steps_spin.setValue(s.get('max_steps', 8000))
        if 'optimization' in params:
            o = params['optimization']
            self.lr_spin.setValue(o.get('learning_rate', 0.00001))
            self.eps_spin.setValue(o.get('epsilon', 1e-5))
            self.iter_spin.setValue(o.get('max_iterations', 60))