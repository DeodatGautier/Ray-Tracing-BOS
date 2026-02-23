"""
gui/main_window.py - Main application window with preset management.
"""

import multiprocessing as mp
from typing import Dict, List
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QTabWidget,
    QStatusBar, QAction, QFileDialog, QDialog, QListWidget,
    QDialogButtonBox, QVBoxLayout as QVBoxLayoutDlg, QLabel
)
from PyQt5.QtCore import Qt, QThread
import json

from core.simulation import RayTracingSimulation, SimulationParameters
from core.optimization import OptimizationWorker, OptimizationParameters
from core.refractive_index import RefractiveIndexType
from utils.data_io import DataLoader, DataExporter
from utils.dialogs import show_error_dialog, show_warning_dialog, show_info_dialog, create_progress_dialog
from gui.widgets.styles import APP_STYLESHEET
from gui.widgets.plot_widgets import TopDownWidget, PlotWidget2D, ComparisonPlotWidget
from gui.control_panel import ControlPanel
from utils.geometry import ExperimentGeometry
from utils.dialogs import FunctionHelpDialog
from utils.helpers import create_text_icon


class PresetDialog(QDialog):
    """Dialog for selecting a preset from the presets folder."""

    def __init__(self, presets_dir: Path, parent=None):
        super().__init__(parent)
        self.presets_dir = presets_dir
        self.setWindowTitle("Load Preset")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayoutDlg(self)

        label = QLabel("Select a preset file:")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.addItems([f.name for f in presets_dir.glob("*.json")])
        if self.list_widget.count() == 0:
            self.list_widget.addItem("(No presets found)")
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.selected_file = None

    def get_selected_file(self) -> Path:
        if self.list_widget.currentItem() and self.list_widget.currentItem().text() != "(No presets found)":
            return self.presets_dir / self.list_widget.currentItem().text()
        return None


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.experimental_data = None
        self.current_simulation = None
        self.optimization_worker = None

        self.control_panel = None
        self.top_down_widget = None
        self.plot_widget_2d = None
        self.comparison_widget = None

        self.simulation_thread = None
        self.optimization_thread = None

        # Determine project root and data/presets folders
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.presets_dir = self.project_root / "presets"
        self.presets_dir.mkdir(exist_ok=True)  # create if not exists

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Ray Tracing BOS")
        self.setGeometry(50, 50, 1500, 900)
        self.setStyleSheet(APP_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        self.create_menu_bar()

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e2e8f0;
            }
            QSplitter::handle:hover {
                background-color: #4a6ee0;
            }
        """)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(4, 4, 4, 4)

        self.control_panel = ControlPanel()
        left_layout.addWidget(self.control_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(4, 4, 4, 4)

        plot_tabs = QTabWidget()
        plot_tabs.setDocumentMode(True)

        self.top_down_widget = TopDownWidget()
        plot_tabs.addTab(self.top_down_widget, "Top-Down")

        self.plot_widget_2d = PlotWidget2D()
        plot_tabs.addTab(self.plot_widget_2d, "2D Analysis")

        self.comparison_widget = ComparisonPlotWidget()
        plot_tabs.addTab(self.comparison_widget, "Comparison")

        right_layout.addWidget(plot_tabs)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([420, 1150])

        main_layout.addWidget(main_splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.status_bar.setSizeGripEnabled(False)

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e2e8f0;
                padding: 2px;
            }
            QMenuBar::item {
                padding: 4px 8px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #e2e8f0;
            }
        """)

        file_menu = menubar.addMenu("&File")

        load_data_action = QAction("&Load Data...", self)
        load_data_action.setIcon(create_text_icon("📂"))
        load_data_action.setShortcut("Ctrl+O")
        load_data_action.triggered.connect(self.load_experimental_data)
        file_menu.addAction(load_data_action)

        file_menu.addSeparator()

        save_preset_action = QAction("Save Preset...", self)
        save_preset_action.setIcon(create_text_icon("💾"))
        save_preset_action.triggered.connect(self.save_preset)
        file_menu.addAction(save_preset_action)

        load_preset_action = QAction("Load Preset...", self)
        load_preset_action.setIcon(create_text_icon("📂"))
        load_preset_action.triggered.connect(self.load_preset_dialog)
        file_menu.addAction(load_preset_action)

        file_menu.addSeparator()

        export_results_action = QAction("&Export Results...", self)
        export_results_action.setIcon(create_text_icon("💾"))
        export_results_action.setShortcut("Ctrl+S")
        export_results_action.triggered.connect(self.export_results)
        file_menu.addAction(export_results_action)

        export_plots_action = QAction("Export &Plots...", self)
        export_plots_action.setIcon(create_text_icon("📊"))
        export_plots_action.setShortcut("Ctrl+P")
        export_plots_action.triggered.connect(self.export_plots)
        file_menu.addAction(export_plots_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setIcon(create_text_icon("🚪"))
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        sim_menu = menubar.addMenu("&Simulation")

        run_simulation_action = QAction("&Run Simulation", self)
        run_simulation_action.setIcon(create_text_icon("▶"))
        run_simulation_action.setShortcut("F5")
        run_simulation_action.triggered.connect(self.run_simulation)
        sim_menu.addAction(run_simulation_action)

        run_optimization_action = QAction("Run &Optimization", self)
        run_optimization_action.setIcon(create_text_icon("⚡"))
        run_optimization_action.setShortcut("F6")
        run_optimization_action.triggered.connect(self.run_optimization)
        sim_menu.addAction(run_optimization_action)

        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.setIcon(create_text_icon("ℹ️"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        functions_action = QAction("Function Descriptions", self)
        functions_action.setIcon(create_text_icon("📘"))
        functions_action.triggered.connect(self.show_function_help)
        help_menu.addAction(functions_action)

    def setup_connections(self):
        """Connect signals from control panel to handlers."""
        self.control_panel.simulation_requested.connect(self.run_simulation)
        self.control_panel.optimization_requested.connect(self.run_optimization)
        self.control_panel.load_data_requested.connect(self.load_experimental_data)

    def load_experimental_data(self):
        """Open file dialog starting in the project's data folder."""
        # Ensure data directory exists
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Experimental Data",
            str(self.data_dir),
            "Data files (*.xlsx *.xls *.csv *.txt);;All files (*)"
        )
        if file_path:
            try:
                self.experimental_data = DataLoader.load_data(file_path)
                self.control_panel.set_experimental_data(self.experimental_data)
                self.status_bar.showMessage(f"Loaded: {Path(file_path).name}")
                if self.current_simulation:
                    self.comparison_widget.update_plot(self.current_simulation, self.experimental_data)
            except Exception as e:
                show_error_dialog(self, "Error", f"Failed to load data: {str(e)}")

    def save_preset(self):
        """Save current settings as a JSON preset file."""
        params = self.control_panel.get_all_parameters()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Preset", str(self.presets_dir), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(params, f, indent=2, ensure_ascii=False)
                self.status_bar.showMessage(f"Preset saved: {Path(file_path).name}")
            except Exception as e:
                show_error_dialog(self, "Error", f"Failed to save preset: {e}")

    def load_preset_dialog(self):
        """Show a dialog to select a preset from the presets folder."""
        if not self.presets_dir.exists():
            show_warning_dialog(self, "Warning", "Presets folder not found.")
            return
        dialog = PresetDialog(self.presets_dir, self)
        if dialog.exec_() == QDialog.Accepted:
            file_path = dialog.get_selected_file()
            if file_path and file_path.exists():
                self.load_preset(file_path)

    def load_preset(self, file_path: Path):
        """Load settings from a preset file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                params = json.load(f)
            self.control_panel.set_all_parameters(params)
            self.status_bar.showMessage(f"Preset loaded: {file_path.name}")
        except Exception as e:
            show_error_dialog(self, "Error", f"Failed to load preset: {e}")

    def export_results(self):
        """Export simulation results to file."""
        if not self.current_simulation:
            show_warning_dialog(self, "Warning", "No simulation results to export")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", str(Path.home()),
            "JSON files (*.json);;CSV files (*.csv);;All files (*)"
        )
        if file_path:
            try:
                DataExporter.export_results(file_path, self.current_simulation)
                self.status_bar.showMessage(f"Exported: {Path(file_path).name}")
            except Exception as e:
                show_error_dialog(self, "Error", f"Failed to export results: {str(e)}")

    def export_plots(self):
        """Export plots to image files."""
        if not self.current_simulation:
            show_warning_dialog(self, "Warning", "No plots to export")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Plots", str(Path.home()),
            "PNG files (*.png);;PDF files (*.pdf);;SVG files (*.svg)"
        )
        if file_path:
            try:
                file_path = Path(file_path)
                base_name = file_path.stem
                extension = file_path.suffix
                plots = [
                    (self.top_down_widget, "3d"),
                    (self.plot_widget_2d, "2d"),
                    (self.comparison_widget, "comparison")
                ]
                for plot_widget, suffix in plots:
                    output_path = file_path.parent / f"{base_name}_{suffix}{extension}"
                    plot_widget.export_plot(str(output_path))
                self.status_bar.showMessage("Plots exported successfully")
            except Exception as e:
                show_error_dialog(self, "Error", f"Failed to export plots: {str(e)}")

    def run_simulation(self):
        """Start a simulation thread."""
        params = self.control_panel.get_simulation_parameters()
        func_params = self.control_panel.get_function_parameters()
        func_type = self.control_panel.get_function_type()
        geo_params = self.control_panel.get_geometry_parameters()
        fixed_indices = self.control_panel.get_fixed_indices()

        geometry = None
        if geo_params['use_geometry']:
            geometry = ExperimentGeometry(
                distance_bg=geo_params['dist_bg'],
                distance_lens=geo_params['dist_lens'],
                thickness=geo_params['thickness'],
                focal_length=geo_params['focal']
            )
            # Adjust max_steps based on object thickness
            object_thickness = geometry.y_max_obj - geometry.y_min_obj
            required_steps = int(object_thickness / params['step_size']) * 2
            params['max_steps'] = max(params['max_steps'], required_steps)

        refractive_func = RefractiveIndexType.get_function(
            func_type, func_params, fixed_indices=fixed_indices
        )

        sim_params = SimulationParameters(
            refractive_func=refractive_func,
            grid_size=(params['grid_x'], params['grid_y']),
            bounds=((-params['bounds'], params['bounds']),
                    (-params['bounds'], params['bounds'])),
            ray_start_y=params['bounds'],
            num_rays=params['num_rays'],
            ds=params['step_size'],
            max_steps=params['max_steps'],
            geometry=geometry
        )

        self.progress_dialog = create_progress_dialog(self, "Running simulation...")
        self.progress_dialog.show()

        self.simulation_thread = QThread()
        self.simulation_worker = RayTracingSimulation(sim_params)
        self.simulation_worker.moveToThread(self.simulation_thread)
        self.simulation_worker.progress.connect(self.update_simulation_progress)
        self.simulation_worker.finished.connect(self.on_simulation_complete)
        self.simulation_worker.error.connect(self.on_simulation_error)
        self.simulation_thread.started.connect(self.simulation_worker.run)
        self.simulation_thread.start()

        self.status_bar.showMessage("Running simulation...")

    def run_optimization(self):
        """Start an optimization thread."""
        if not self.experimental_data:
            show_warning_dialog(self, "Warning", "Please load experimental data first")
            return

        opt_params_dict = self.control_panel.get_optimization_parameters()
        sim_params_dict = self.control_panel.get_simulation_parameters()
        func_type = self.control_panel.get_function_type()
        full_params = self.control_panel.get_function_parameters()
        geo_params = self.control_panel.get_geometry_parameters()
        fixed_indices = self.control_panel.get_fixed_indices()

        geometry = None
        if geo_params['use_geometry']:
            geometry = ExperimentGeometry(
                distance_bg=geo_params['dist_bg'],
                distance_lens=geo_params['dist_lens'],
                thickness=geo_params['thickness'],
                focal_length=geo_params['focal']
            )

        total_cores = mp.cpu_count()
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024 ** 3)

        info_text = f"""
        <h3>System Configuration</h3>
        <b>CPU:</b> {total_cores} cores<br>
        <b>Memory:</b> {memory_gb:.1f} GB<br><br>
        <h3>Optimization Settings</h3>
        Geometry enabled: {geo_params['use_geometry']}<br>
        BG distance: {geo_params['dist_bg']} mm<br>
        Lens distance: {geo_params['dist_lens']} mm<br>
        Thickness: {geo_params['thickness']} mm<br>
        Focal length: {geo_params['focal']} mm<br>
        Fixed indices: {fixed_indices}<br>
        Starting optimization...
        """
        show_info_dialog(self, "Starting Optimization", info_text)

        opt_params = OptimizationParameters(
            full_params=full_params,
            fixed_indices=fixed_indices,
            learning_rate=opt_params_dict['learning_rate'],
            epsilon=opt_params_dict['epsilon'],
            max_iterations=opt_params_dict['max_iterations'],
            base_grid_size=(sim_params_dict['grid_x'], sim_params_dict['grid_y']),
            bounds=sim_params_dict['bounds'],
            base_num_rays=sim_params_dict['num_rays'],
            function_type=func_type,
            geometry=geometry
        )

        config = opt_params.system_config
        config_text = f"""
        <h3>Auto-Configuration Applied</h3>
        <b>Parallel Simulations:</b> {opt_params.parallel_simulations}<br>
        <b>Cores per Simulation:</b> {opt_params.num_workers_per_sim}<br>
        <b>Optimization Grid:</b> {opt_params.optimization_grid_size[0]}×{opt_params.optimization_grid_size[1]}<br>
        <b>Optimization Rays:</b> {opt_params.optimization_num_rays}<br>
        <b>Total CPU Utilization:</b> {opt_params.parallel_simulations * opt_params.num_workers_per_sim}/{total_cores} cores
        """
        self.opt_progress_dialog = create_progress_dialog(
            self, "Parallel Optimization", config_text
        )
        self.opt_progress_dialog.setMinimumWidth(500)
        self.opt_progress_dialog.show()

        self.optimization_thread = QThread()
        self.optimization_worker = OptimizationWorker(opt_params, self.experimental_data, self)
        self.optimization_worker.moveToThread(self.optimization_thread)
        self.optimization_worker.progress.connect(self.update_optimization_progress)
        self.optimization_worker.finished.connect(self.on_optimization_complete)
        self.optimization_worker.error.connect(self.on_optimization_error)
        self.optimization_thread.started.connect(self.optimization_worker.run)
        self.optimization_thread.start()

        self.status_bar.showMessage(f"Running optimization on {total_cores} CPU cores...")

    def update_simulation_progress(self, value: int, message: str):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(max(0, min(100, value)))
            self.progress_dialog.setLabelText(message)
            self.status_bar.showMessage(f"Simulation: {message}")

    def on_simulation_complete(self, results: dict):
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.quit()
            self.simulation_thread.wait()
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        self.current_simulation = results
        self.top_down_widget.update_plot(results)
        self.plot_widget_2d.update_plot(results)
        if self.experimental_data:
            self.comparison_widget.update_plot(results, self.experimental_data)
        self.status_bar.showMessage("Simulation complete")

    def on_simulation_error(self, error_message: str):
        if hasattr(self, 'simulation_thread'):
            self.simulation_thread.quit()
            self.simulation_thread.wait()
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        show_error_dialog(self, "Simulation Error", error_message)
        self.status_bar.showMessage("Simulation failed")

    def update_optimization_progress(self, iteration: int, error: float, params: List[float], msg: str):
        if hasattr(self, 'opt_progress_dialog'):
            max_iter = self.control_panel.get_optimization_parameters()['max_iterations']
            if max_iter > 0:
                progress = int((iteration / max_iter) * 100)
                progress = max(0, min(100, progress))
            else:
                progress = 0
            self.opt_progress_dialog.setValue(progress)
            self.opt_progress_dialog.setLabelText(msg)
            self.status_bar.showMessage(f"Optimization: {msg}")

    def on_optimization_complete(self, results: dict):
        if hasattr(self, 'optimization_thread'):
            self.optimization_thread.quit()
            self.optimization_thread.wait()
        if hasattr(self, 'opt_progress_dialog'):
            self.opt_progress_dialog.close()

        self.control_panel.set_function_parameters(results['best_params'])
        self.run_simulation()
        self.status_bar.showMessage(f"Optimization complete. MSE: {results['best_error']:.6e}")

    def on_optimization_error(self, error_message: str):
        if hasattr(self, 'optimization_thread'):
            self.optimization_thread.quit()
            self.optimization_thread.wait()
        if hasattr(self, 'opt_progress_dialog'):
            self.opt_progress_dialog.close()
        show_error_dialog(self, "Optimization Error", error_message)
        self.status_bar.showMessage("Optimization failed")

    def show_about(self):
        about_text = """
        <h2>Ray Tracing BOS</h2>
        <p>Version 1.0.0</p>
        <p>A tool for simulating ray tracing through axisymmetric refractive index distributions
        and solving inverse problems to determine refractive index fields from experimental data.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Ray tracing simulation with Runge-Kutta integration</li>
            <li>Multiple refractive index distribution functions</li>
            <li>Parameter optimization using gradient descent</li>
            <li>Experimental data import (Excel, CSV)</li>
            <li>2D visualization</li>
            <li>Multi-threaded computations</li>
            <li>Preset management</li>
        </ul>
        <p>© 2026 Alexander Kurilov.</p>
        """
        show_info_dialog(self, "About", about_text)

    def show_function_help(self):
        dialog = FunctionHelpDialog(self)
        dialog.exec_()

    def closeEvent(self, event):
        if hasattr(self, 'simulation_thread') and self.simulation_thread and self.simulation_thread.isRunning():
            self.simulation_thread.quit()
            self.simulation_thread.wait()
        if hasattr(self, 'optimization_thread') and self.optimization_thread and self.optimization_thread.isRunning():
            self.optimization_thread.quit()
            self.optimization_thread.wait()
        event.accept()