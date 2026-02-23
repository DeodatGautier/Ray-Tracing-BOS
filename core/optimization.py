"""
core/optimization.py - Advanced parallel optimization with Adam optimizer
"""

import numpy as np
from typing import Dict, List, Optional
from scipy.interpolate import interp1d
import warnings
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil

from PyQt5.QtCore import QObject, pyqtSignal

from .simulation import RayTracingSimulation, SimulationParameters
from .refractive_index import RefractiveIndexType
from utils.constants import DEFAULT_GRID_SIZE, DEFAULT_BOUNDS, DEFAULT_NUM_RAYS, \
                           DEFAULT_STEP_SIZE, DEFAULT_MAX_STEPS
from utils.geometry import ExperimentGeometry


class SystemConfig:
    """Automatic system configuration for optimal performance."""

    @staticmethod
    def get_optimal_config():
        """
        Determine optimal configuration based on system resources.

        Returns:
            Dict with optimal parameters for current system
        """
        # Get system information
        total_cores = mp.cpu_count()
        total_memory_gb = psutil.virtual_memory().total / (1024**3)  # GB
        available_memory_gb = psutil.virtual_memory().available / (1024**3)

        # Base configuration
        config = {
            'total_cores': total_cores,
            'total_memory_gb': total_memory_gb,
            'available_memory_gb': available_memory_gb,
        }

        # Determine optimal parallelization strategy
        if total_cores >= 16:
            config.update({
                'parallel_simulations': 4,
                'cores_per_simulation': 4,
                'optimization_grid_scale': 1.0,
                'optimization_rays_scale': 1.0,
                'step_size_multiplier': 1.0,
                'max_steps_scale': 1.0,
            })
        elif total_cores >= 8:
            config.update({
                'parallel_simulations': 3,
                'cores_per_simulation': 2,
                'optimization_grid_scale': 0.75,
                'optimization_rays_scale': 0.5,
                'step_size_multiplier': 1.25,
                'max_steps_scale': 0.8,
            })
        elif total_cores >= 4:
            config.update({
                'parallel_simulations': 2,
                'cores_per_simulation': 2,
                'optimization_grid_scale': 0.5,
                'optimization_rays_scale': 0.25,
                'step_size_multiplier': 1.25,
                'max_steps_scale': 0.9,
            })
        else:
            config.update({
                'parallel_simulations': 1,
                'cores_per_simulation': max(1, total_cores - 1),
                'optimization_grid_scale': 0.25,
                'optimization_rays_scale': 0.125,
                'step_size_multiplier': 2.0,
                'max_steps_scale': 0.4,
            })

        # Adjust based on available memory
        if available_memory_gb < 4:
            config['optimization_grid_scale'] *= 0.75
            config['parallel_simulations'] = max(1, config['parallel_simulations'] - 1)

        return config

    @staticmethod
    def print_config(config: Dict):
        """Print system configuration for debugging."""
        print(f"=== System Configuration ===")
        print(f"CPU Cores: {config['total_cores']}")
        print(f"Available Memory: {config['available_memory_gb']:.1f} GB")
        print(f"Parallel Simulations: {config['parallel_simulations']}")
        print(f"Cores per Simulation: {config['cores_per_simulation']}")
        print(f"Grid Scale: {config['optimization_grid_scale']}")
        print(f"Rays Scale: {config['optimization_rays_scale']}")
        print(f"Step Size Multiplier: {config['step_size_multiplier']}")
        print("===========================")


class OptimizationParameters:
    """Parameters for optimization with auto-configuration and fixed parameters."""

    def __init__(self, full_params: List[float], fixed_indices: List[int], **kwargs):
        """
        Parameters
        ----------
        full_params : list of float
            Complete list of 5 parameters: [A, B, C, D, X0].
        fixed_indices : list of int
            Indices of parameters that are fixed (not optimized).
        """
        self.full_params = np.array(full_params, dtype=np.float64)
        self.fixed_indices = fixed_indices
        self.variable_indices = [i for i in range(5) if i not in fixed_indices]
        self.initial_params = self.full_params[self.variable_indices].tolist()

        self.learning_rate = kwargs.get('learning_rate', 0.001)
        self.epsilon = kwargs.get('epsilon', 1e-4)
        self.max_iterations = kwargs.get('max_iterations', 60)
        self.base_grid_size = kwargs.get('base_grid_size', DEFAULT_GRID_SIZE)
        self.base_bounds = kwargs.get('bounds', DEFAULT_BOUNDS)
        self.base_num_rays = kwargs.get('base_num_rays', DEFAULT_NUM_RAYS)
        self.function_type = kwargs.get('function_type', 'gaussian')
        self.geometry = kwargs.get('geometry', None)

        # Get automatic system configuration
        sys_config = SystemConfig.get_optimal_config()

        # Auto-configure parallelization
        self.parallel_simulations = kwargs.get('parallel_simulations',
                                              sys_config['parallel_simulations'])
        self.num_workers_per_sim = kwargs.get('num_workers_per_sim',
                                             sys_config['cores_per_simulation'])

        # Auto-scale optimization parameters
        grid_scale = sys_config['optimization_grid_scale']
        self.optimization_grid_size = (
            max(64, int(self.base_grid_size[0] * grid_scale)),
            max(64, int(self.base_grid_size[1] * grid_scale))
        )

        rays_scale = sys_config['optimization_rays_scale']
        self.optimization_num_rays = max(15, int(self.base_num_rays * rays_scale))

        self.step_size_multiplier = sys_config['step_size_multiplier']
        self.max_steps_scale = sys_config['max_steps_scale']

        # Compute appropriate max_steps for optimization based on object thickness (if geometry used)
        effective_ds = DEFAULT_STEP_SIZE * self.step_size_multiplier
        if self.geometry is not None:
            # Only need to integrate inside the object
            object_thickness = self.geometry.y_max_obj - self.geometry.y_min_obj
            self.optimization_max_steps = int(object_thickness / effective_ds) * 2
        else:
            self.optimization_max_steps = int(DEFAULT_MAX_STEPS * self.max_steps_scale)

        # Store system config for reference
        self.system_config = sys_config


class GradientCalculator:
    """Parallel gradient calculator with adaptive resource management."""

    def __init__(self, base_params: OptimizationParameters,
                 experimental_data: Dict):
        self.base_params = base_params
        self.experimental_data = experimental_data

        # Extract experimental data
        self.x_exp = experimental_data.get('x', np.array([]))
        self.delta_exp = experimental_data.get('delta', np.array([]))

        # Flag for stopping
        self._stop_requested = False

    def compute_gradient(self, params: np.ndarray, current_error: float) -> np.ndarray:
        """
        Compute gradient with adaptive parallel simulations.

        Args:
            params: Current *variable* parameter vector
            current_error: Current error value

        Returns:
            Gradient vector (same length as params)
        """
        n_params = len(params)
        grad = np.zeros_like(params)

        # Prepare all parameter variations
        param_variations = []
        for i in range(n_params):
            params_pert = params.copy()
            params_pert[i] += self.base_params.epsilon
            param_variations.append((i, params_pert))

        # Run all simulations in parallel
        with ProcessPoolExecutor(max_workers=self.base_params.parallel_simulations) as executor:
            future_to_index = {}
            for i, params_pert in param_variations:
                future = executor.submit(self._run_fast_simulation, params_pert)
                future_to_index[future] = i

            results = {}
            for future in as_completed(future_to_index):
                if self._stop_requested:
                    future.cancel()
                    continue
                i = future_to_index[future]
                try:
                    error_pert = future.result(timeout=300)
                    results[i] = error_pert
                except Exception as e:
                    warnings.warn(f"Gradient component {i} failed: {str(e)}")
                    results[i] = float('inf')  # treat as infinite error

        # Calculate gradient components
        for i in range(n_params):
            if i in results and not np.isinf(results[i]) and not np.isnan(results[i]):
                grad[i] = (results[i] - current_error) / self.base_params.epsilon
            else:
                grad[i] = 0.0  # no valid gradient info

        return grad

    def _run_fast_simulation(self, var_params: np.ndarray) -> float:
        """
        Run a single simulation with optimization settings.
        var_params : current *variable* parameters.
        """
        try:
            # Construct full parameter vector (5 elements)
            full_params = self.base_params.full_params.copy()
            full_params[self.base_params.variable_indices] = var_params

            # Create refractive index function (with fixed indices)
            n_func = RefractiveIndexType.get_function(
                self.base_params.function_type,
                full_params.tolist(),
                fixed_indices=self.base_params.fixed_indices
            )

            # Create simulation parameters with optimization settings
            sim_params = SimulationParameters(
                refractive_func=n_func,
                grid_size=self.base_params.optimization_grid_size,
                bounds=((-self.base_params.base_bounds, self.base_params.base_bounds),
                        (-self.base_params.base_bounds, self.base_params.base_bounds)),
                ray_start_y=self.base_params.base_bounds,
                num_rays=self.base_params.optimization_num_rays,
                ds=DEFAULT_STEP_SIZE * self.base_params.step_size_multiplier,
                max_steps=self.base_params.optimization_max_steps,
                num_workers=self.base_params.num_workers_per_sim,
                geometry=self.base_params.geometry
            )

            # Run simulation
            simulation = RayTracingSimulation(sim_params)
            simulation._initialize_grid()
            simulation._trace_rays_parallel_optimized()
            results = simulation._calculate_results()

            if not results or 'displacements' not in results:
                return float('inf')

            # Calculate error using fast interpolation (use sensor coordinates)
            return self._calculate_fast_error(results)

        except Exception as e:
            warnings.warn(f"Fast simulation failed: {str(e)}")
            return float('inf')

    def _calculate_fast_error(self, simulation_results: Dict) -> float:
        """Calculate error using fast interpolation with sensor coordinates."""
        displacements = simulation_results.get('displacements', np.array([]))
        # Use x_sensor if available (geometry case), otherwise fallback to x_starts
        x_sim = simulation_results.get('x_sensor', simulation_results.get('x_starts', np.array([])))

        if len(displacements) < 2 or len(self.x_exp) == 0:
            return float('inf')

        try:
            interp_func = interp1d(x_sim, displacements, kind='linear',
                                   bounds_error=False, fill_value='extrapolate')
            delta_sim = interp_func(self.x_exp)
            mse = np.mean((delta_sim - self.delta_exp) ** 2)
            return mse
        except Exception:
            return float('inf')


class OptimizationWorker(QObject):
    """
    Optimization worker with Adam optimizer, automatic system configuration,
    gradient clipping, and per‑parameter bounds.
    """

    progress = pyqtSignal(int, float, list, str)  # iteration, error, parameters, message
    finished = pyqtSignal(dict)  # optimization results
    error = pyqtSignal(str)       # error message

    def __init__(self, parameters: OptimizationParameters,
                 experimental_data: Dict, parent=None):
        super().__init__(parent)
        self.params = parameters
        self.experimental_data = experimental_data

        self.best_params = None
        self.best_error = float('inf')
        self.best_simulation = None
        self._stop_requested = False

        self.gradient_calculator = GradientCalculator(parameters, experimental_data)

        # Adam parameters
        self.m = np.zeros(len(parameters.variable_indices), dtype=np.float64)   # first moment
        self.v = np.zeros(len(parameters.variable_indices), dtype=np.float64)   # second moment
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.epsilon = 1e-8
        self.learning_rate = parameters.learning_rate
        self.t = 0  # time step

        # Gradient clipping
        self.max_grad_norm = 1.0

        self.error_history = []

        SystemConfig.print_config(parameters.system_config)

    def run(self):
        """Main optimization loop with Adam."""
        try:
            x_exp = self.experimental_data.get('x', np.array([]))
            delta_exp = self.experimental_data.get('delta', np.array([]))

            if len(x_exp) < 3 or len(delta_exp) < 3:
                self.error.emit("Insufficient experimental data for optimization")
                return

            self.progress.emit(0, float('inf'), [], "Calculating initial error...")

            # Initial error using variable parameters
            current_params = np.array(self.params.initial_params, dtype=np.float64)
            current_error = self._calculate_error(current_params, fast=True)

            self.best_params = current_params.copy()
            self.best_error = current_error
            self.error_history.append(current_error)

            self.progress.emit(1, current_error, current_params.tolist(),
                               f"Initial error: {current_error:.4e}")

            # Main optimization loop
            for iteration in range(self.params.max_iterations):
                if self._stop_requested:
                    self.progress.emit(iteration, current_error, current_params.tolist(),
                                       "Optimization stopped by user")
                    break

                # Calculate gradient
                grad_msg = (f"Computing gradient with {self.params.parallel_simulations} "
                            f"parallel simulations...")
                self.progress.emit(iteration + 1, current_error, current_params.tolist(), grad_msg)

                grad = self.gradient_calculator.compute_gradient(current_params, current_error)

                if self._stop_requested:
                    break

                # Gradient clipping
                grad_norm = np.linalg.norm(grad)
                if grad_norm > self.max_grad_norm:
                    grad = grad * self.max_grad_norm / grad_norm

                print(f"Iter {iteration}: grad_norm = {grad_norm:.3e}")

                # Adam update
                self.t += 1
                self.m = self.beta1 * self.m + (1 - self.beta1) * grad
                self.v = self.beta2 * self.v + (1 - self.beta2) * (grad ** 2)

                # Bias correction
                m_hat = self.m / (1 - self.beta1 ** self.t)
                v_hat = self.v / (1 - self.beta2 ** self.t)

                # Parameter update
                old_params = current_params.copy()
                current_params -= self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)

                # Apply per‑parameter bounds
                for i, global_idx in enumerate(self.params.variable_indices):
                    if global_idx == 4:  # X0 can be negative
                        current_params[i] = np.clip(current_params[i], -10.0, 10.0)
                    else:  # A, B, C, D positive (refractive index and shape parameters)
                        current_params[i] = np.clip(current_params[i], 1e-6, 10.0)

                new_error = self._calculate_error(current_params, fast=True)

                # accept = self._accept_new_parameters(current_error, new_error, iteration)
                accept = True

                if accept:
                    current_error = new_error
                    self.error_history.append(current_error)
                    if new_error < self.best_error:
                        improvement = (self.best_error - new_error) / self.best_error * 100
                        self.best_error = new_error
                        self.best_params = current_params.copy()
                        self.progress.emit(
                            iteration + 1, current_error, current_params.tolist(),
                            f"New best error: {new_error:.4e} (improvement: {improvement:.1f}%)"
                        )
                    else:
                        # Still accepted, report progress
                        self.progress.emit(
                            iteration + 1, current_error, current_params.tolist(),
                            f"Iteration {iteration+1}: error = {new_error:.4e}"
                        )
                else:
                    # Reject update: revert parameters and reduce learning rate slightly
                    current_params = old_params
                    self.learning_rate *= 0.95
                    self.progress.emit(
                        iteration + 1, current_error, current_params.tolist(),
                        f"Rejected update, reducing LR to {self.learning_rate:.6f}"
                    )

                if self._check_convergence(iteration, current_error, grad):
                    self.progress.emit(iteration + 1, current_error, current_params.tolist(),
                                       f"Converged at iteration {iteration + 1}")
                    break

            # Final simulation with full accuracy
            self.progress.emit(100, self.best_error, self.best_params.tolist(),
                               "Running final simulation with full accuracy...")
            final_simulation = self._run_final_simulation(self.best_params)

            # Build full parameter list for output (5 elements)
            full_best_params = self.params.full_params.copy()
            full_best_params[self.params.variable_indices] = self.best_params

            results = {
                'best_params': full_best_params.tolist(),
                'best_error': self.best_error,
                'initial_error': self.error_history[0] if self.error_history else current_error,
                'function_type': self.params.function_type,
                'iterations_completed': iteration + 1,
                'simulation': final_simulation,
                'final_learning_rate': self.learning_rate,
                'converged': iteration < self.params.max_iterations - 1,
                'system_config': self.params.system_config,
                'optimization_config': {
                    'parallel_simulations': self.params.parallel_simulations,
                    'optimization_grid_size': self.params.optimization_grid_size,
                    'optimization_num_rays': self.params.optimization_num_rays,
                    'cores_per_simulation': self.params.num_workers_per_sim,
                },
                'fixed_indices': self.params.fixed_indices,
                'geometry': self.params.geometry.to_dict() if self.params.geometry else None
            }

            self.finished.emit(results)


        except Exception as e:

            self.error.emit(f"Optimization error: {str(e)}")

    def stop(self):
        self._stop_requested = True
        self.gradient_calculator._stop_requested = True

    def _calculate_error(self, var_params: np.ndarray, fast: bool = True) -> float:
        try:
            if fast:
                return self.gradient_calculator._run_fast_simulation(var_params)
            else:
                simulation = self._run_full_simulation(var_params)
                if simulation and 'displacements' in simulation:
                    return self.gradient_calculator._calculate_fast_error(simulation)
                return float('inf')
        except Exception as e:
            warnings.warn(f"Error calculation failed: {str(e)}")
            return float('inf')

    def _run_full_simulation(self, var_params: np.ndarray) -> Optional[Dict]:
        full_params = self.params.full_params.copy()
        full_params[self.params.variable_indices] = var_params
        n_func = RefractiveIndexType.get_function(
            self.params.function_type,
            full_params.tolist(),
            fixed_indices=self.params.fixed_indices
        )

        # Adjust max_steps for full simulation: use object thickness with DEFAULT_STEP_SIZE
        if self.params.geometry is not None:
            object_thickness = self.params.geometry.y_max_obj - self.params.geometry.y_min_obj
            max_steps = int(object_thickness / DEFAULT_STEP_SIZE) * 2
        else:
            max_steps = DEFAULT_MAX_STEPS

        sim_params = SimulationParameters(
            refractive_func=n_func,
            grid_size=self.params.base_grid_size,
            bounds=((-self.params.base_bounds, self.params.base_bounds),
                    (-self.params.base_bounds, self.params.base_bounds)),
            ray_start_y=self.params.base_bounds,
            num_rays=self.params.base_num_rays,
            ds=DEFAULT_STEP_SIZE,
            max_steps=max_steps,
            num_workers=max(1, mp.cpu_count() - 1),
            geometry=self.params.geometry
        )

        simulation = RayTracingSimulation(sim_params)
        simulation._initialize_grid()
        simulation._trace_rays_parallel_optimized()
        return simulation._calculate_results()

    def _run_final_simulation(self, var_params: np.ndarray) -> Dict:
        # For final simulation, use full accuracy settings (already set in _run_full_simulation)
        result = self._run_full_simulation(var_params)
        return result if result is not None else {}

    def _accept_new_parameters(self, old_error: float, new_error: float,
                               iteration: int) -> bool:
        if new_error < old_error:
            return True
        temperature = max(0.5, 1.0 - (iteration / self.params.max_iterations))
        probability = np.exp(-(new_error - old_error) / (temperature * old_error + 1e-10))
        return np.random.random() < probability

    def _check_convergence(self, iteration: int, error: float,
                           gradient: np.ndarray) -> bool:
        grad_norm = np.linalg.norm(gradient)
        if grad_norm < 1e-6:
            return True
        if len(self.error_history) >= 10:
            recent = self.error_history[-10:]
            if np.std(recent) < 1e-8 * np.mean(recent):
                return True
        if iteration >= self.params.max_iterations - 1:
            return True
        return False