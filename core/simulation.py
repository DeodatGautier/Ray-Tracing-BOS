"""
core/simulation.py - Core simulation classes with fully parallel ray processing.
"""

import numpy as np
from typing import Dict, Tuple, Optional, List, Any
from scipy.ndimage import map_coordinates
import warnings
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

from PyQt5.QtCore import QObject, pyqtSignal

from .refractive_index import RefractiveIndexFunction
from utils.constants import DEFAULT_GRID_SIZE, DEFAULT_BOUNDS, DEFAULT_NUM_RAYS, \
                           DEFAULT_STEP_SIZE, DEFAULT_MAX_STEPS, DEFAULT_RAY_START_Y
from utils.geometry import ExperimentGeometry


class SimulationParameters:
    """Parameters for ray tracing simulation."""

    def __init__(self, refractive_func: RefractiveIndexFunction, **kwargs):
        self.refractive_func = refractive_func
        self.grid_size = kwargs.get('grid_size', DEFAULT_GRID_SIZE)
        self.bounds = kwargs.get('bounds', ((-DEFAULT_BOUNDS, DEFAULT_BOUNDS),
                                          (-DEFAULT_BOUNDS, DEFAULT_BOUNDS)))
        self.ray_start_y = kwargs.get('ray_start_y', DEFAULT_RAY_START_Y)
        self.num_rays = kwargs.get('num_rays', DEFAULT_NUM_RAYS)
        self.ds = kwargs.get('ds', DEFAULT_STEP_SIZE)
        self.max_steps = kwargs.get('max_steps', DEFAULT_MAX_STEPS)
        self.num_workers = kwargs.get('num_workers', max(1, mp.cpu_count() - 1))
        self.geometry = kwargs.get('geometry', None)  # optional ExperimentGeometry


class RayTracingSimulation(QObject):
    """
    Ray tracing simulation for axisymmetric refractive index distributions.
    Uses 4th order Runge‑Kutta integration with fully parallel ray processing.
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, parameters: SimulationParameters):
        super().__init__()
        self.params = parameters
        self.n_func = parameters.refractive_func
        self.grid = None
        self.n_values = None
        self.ray_results = []  # list of dicts with 'path', 'r_end', 't_end'
        self._stop_requested = False

    def run(self):
        """Run the simulation (to be called from thread)."""
        try:
            self.progress.emit(0, "Initializing simulation...")
            self._initialize_grid()
            self.progress.emit(20, f"Tracing {self.params.num_rays} rays with {self.params.num_workers} workers...")
            self._trace_rays_parallel_optimized()
            if self._stop_requested:
                return
            self.progress.emit(80, "Calculating results...")
            results = self._calculate_results()
            self.progress.emit(100, "Simulation complete")
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(f"Simulation error: {str(e)}")

    def stop(self):
        """Request simulation stop."""
        self._stop_requested = True

    def _initialize_grid(self):
        """Initialize simulation grid and refractive index values."""
        nx, ny = self.params.grid_size
        x_min, x_max = self.params.bounds[0]
        y_min, y_max = self.params.bounds[1]
        x_grid = np.linspace(x_min, x_max, nx)
        y_grid = np.linspace(y_min, y_max, ny)
        X, Y = np.meshgrid(x_grid, y_grid, indexing='ij')
        self.n_values = self.n_func(X, Y)
        self.grid = {
            'x_grid': x_grid,
            'y_grid': y_grid,
            'X': X,
            'Y': Y,
            'dx': (x_max - x_min) / (nx - 1),
            'dy': (y_max - y_min) / (ny - 1),
            'bounds': self.params.bounds,
            'grid_size': self.params.grid_size
        }

    def _trace_rays_parallel_optimized(self):
        """Trace multiple rays in parallel."""
        x_min, x_max = self.params.bounds[0]
        x_starts = np.linspace(x_min + 0.1, x_max - 0.1, self.params.num_rays)
        if self._stop_requested:
            return

        # Prepare shared data (only what is needed by worker)
        worker_data = {
            'n_values': self.n_values,
            'grid': {
                'x_grid': self.grid['x_grid'],
                'y_grid': self.grid['y_grid'],
                'dx': self.grid['dx'],
                'dy': self.grid['dy'],
                'bounds': self.grid['bounds'],
                'grid_size': self.grid['grid_size']
            },
            'params': {
                'bounds': self.params.bounds,
                'grid_size': self.params.grid_size,
                'ds': self.params.ds,
                'max_steps': self.params.max_steps,
                'ray_start_y': self.params.ray_start_y
            }
        }
        if self.params.geometry is not None:
            worker_data['geometry'] = self.params.geometry.to_dict()

        self.ray_results = []
        completed_rays = 0
        total_rays = len(x_starts)

        with ProcessPoolExecutor(max_workers=self.params.num_workers) as executor:
            future_to_index = {}
            for idx, x_start in enumerate(x_starts):
                if self._stop_requested:
                    break
                future = executor.submit(trace_single_ray_worker, x_start, worker_data)
                future_to_index[future] = idx

            for future in as_completed(future_to_index):
                if self._stop_requested:
                    future.cancel()
                    continue
                try:
                    result = future.result(timeout=60)
                    if result is not None:
                        self.ray_results.append(result)
                    completed_rays += 1
                    progress = 20 + int((completed_rays / total_rays) * 60)
                    update_frequency = max(1, total_rays // 20)
                    if completed_rays % update_frequency == 0 or completed_rays == total_rays:
                        self.progress.emit(
                            progress,
                            f"Rays traced: {completed_rays}/{total_rays} ({progress}%)"
                        )
                except Exception as e:
                    warnings.warn(f"Ray tracing failed: {str(e)}")
                    continue

        if not self._stop_requested:
            self.progress.emit(80, f"Completed: {len(self.ray_results)} of {total_rays} rays")

    def _calculate_results(self) -> Dict:
        """
        Calculate simulation results.
        If geometry is used, displacements are computed on the sensor plane via lens formula,
        and sensor coordinates (x_sensor) are computed using magnification.
        """
        if not self.ray_results or self._stop_requested:
            return {}

        # Sort by starting x
        self.ray_results.sort(key=lambda d: d['path'][0, 0])

        x_starts = np.array([d['path'][0, 0] for d in self.ray_results])
        paths = [d['path'] for d in self.ray_results]

        if self.params.geometry is not None:
            # Use lens formula to compute displacement on sensor
            geom = self.params.geometry
            # Safeguard against unfocused case
            if geom.a <= geom.focal_length:
                warnings.warn("Cannot focus (object too close). Using approximate displacement at lens.")
                x_ends = np.array([d['r_end'][0] for d in self.ray_results])
                displacements = x_ends - x_starts
            else:
                b = geom.b
                displacements = []
                for d in self.ray_results:
                    t = d['t_end']          # direction at lens (normalized)
                    # Angle relative to optical axis (downward = -y)
                    angle = np.arctan2(t[0], -t[1])   # positive for right deflection
                    disp = b * np.tan(angle)
                    displacements.append(disp)
                displacements = np.array(displacements)
                x_ends = x_starts + displacements   # for reference

            # Compute sensor coordinates (with positive magnification, ignoring inversion)
            M = geom.b / geom.a   # >0
            x_sensor = M * x_starts
        else:
            # Legacy mode: displacement is x_end - x_start at lower bound
            x_ends = np.array([d['r_end'][0] for d in self.ray_results])
            displacements = x_ends - x_starts
            x_sensor = x_starts.copy()

        y_zero_idx = np.argmin(np.abs(self.grid['y_grid']))
        n_profile = self.n_values[:, y_zero_idx]

        results = {
            'rays': paths,
            'x_starts': x_starts,
            'x_sensor': x_sensor,
            'displacements': displacements,
            'n_values': self.n_values,
            'grid': {
                'x_grid': self.grid['x_grid'],
                'y_grid': self.grid['y_grid'],
                'X': self.grid['X'],
                'Y': self.grid['Y'],
                'dx': self.grid['dx'],
                'dy': self.grid['dy'],
                'bounds': self.grid['bounds'],
                'grid_size': self.grid['grid_size']
            },
            'n_profile': n_profile,
            'function_type': self.n_func.__class__.__name__.replace('Function', ''),
            'function_params': self.n_func.params.tolist(),
            'ray_start_y': self.params.ray_start_y,
            'num_workers_used': self.params.num_workers,
            'geometry': self.params.geometry.to_dict() if self.params.geometry else None
        }
        return results

def trace_single_ray_worker(x_start: float, worker_data: Dict) -> Optional[Dict]:
    """
    Worker function for tracing a single ray.
    Optimized: propagates straight through homogeneous regions,
    performs RK4 only inside the gradient object.
    Returns a dictionary with:
        - 'path': array of (x, y) points up to the stopping plane (lens or lower bound)
        - 'r_end': final coordinates (at stopping plane)
        - 't_end': final direction (normalized)
    Returns None if the ray failed (e.g., exited through top or got stuck).
    """
    n_values = worker_data['n_values']
    grid = worker_data['grid']
    params = worker_data['params']
    geometry_dict = worker_data.get('geometry')

    # Unpack parameters
    bounds = params['bounds']
    grid_size = params['grid_size']
    ds = params['ds']
    max_steps = params['max_steps']
    ray_start_y = params['ray_start_y']

    # Unpack grid data
    x_min, x_max = bounds[0]
    y_min, y_max = bounds[1]
    dx = grid['dx']
    dy = grid['dy']
    x_grid0 = grid['x_grid'][0]
    y_grid0 = grid['y_grid'][0]

    # Geometry handling
    if geometry_dict:
        y_bg = geometry_dict['y_bg']
        y_lens = geometry_dict['y_lens']
        y_min_obj = geometry_dict['y_min_obj']
        y_max_obj = geometry_dict['y_max_obj']

        # Start at background
        r = np.array([x_start, y_bg], dtype=np.float64)
        t = np.array([0.0, -1.0], dtype=np.float64)  # initial direction downward
        path = [r.copy()]

        # ---- STAGE 1: Homogeneous region from background to object entry ----
        if y_bg > y_max_obj:
            # Straight propagation down to y_max_obj
            dy1 = y_bg - y_max_obj
            # Since t = [0, -1], moving down by dy1 brings y to y_max_obj
            r = r + t * dy1
            path.append(r.copy())
            # Direction unchanged

        # ---- STAGE 2: Inside gradient object (y from y_max_obj down to y_min_obj) ----
        # Local functions for interpolation and gradient
        def get_n(grid_x, grid_y, y_world):
            gx = max(0, min(grid_size[0] - 1, grid_x))
            gy = max(0, min(grid_size[1] - 1, grid_y))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                n = map_coordinates(n_values, [[gx], [gy]], order=1, mode='nearest')[0]
            return max(n, 0.0)

        def grad(grid_x, grid_y, y_world):
            if y_world < y_min_obj or y_world > y_max_obj:
                return 0.0, 0.0
            eps = 1e-3
            eps_x = eps / dx
            eps_y = eps / dy
            n_xp = get_n(grid_x + eps_x, grid_y, y_world)
            n_xm = get_n(grid_x - eps_x, grid_y, y_world)
            dn_dx = (n_xp - n_xm) / (2 * eps_x * dx)
            n_yp = get_n(grid_x, grid_y + eps_y, y_world + eps)
            n_ym = get_n(grid_x, grid_y - eps_y, y_world - eps)
            dn_dy = (n_yp - n_ym) / (2 * eps_y * dy)
            return dn_dx, dn_dy

        def derivatives(r_local, t_local):
            gx = (r_local[0] - x_grid0) / dx
            gy = (r_local[1] - y_grid0) / dy
            yw = r_local[1]
            n = get_n(gx, gy, yw)
            if n < 1e-6:
                return np.zeros(2), np.zeros(2)
            dnx, dny = grad(gx, gy, yw)
            dr = t_local
            dt = (1.0 / n) * np.array([dnx, dny])
            return dr, dt

        step = 0
        exited_bottom = False
        exited_top = False

        # RK4 loop while inside object and steps left
        while r[1] > y_min_obj and r[1] <= y_max_obj and step < max_steps:
            k1r, k1t = derivatives(r, t)
            r2 = r + 0.5 * ds * k1r
            t2 = t + 0.5 * ds * k1t
            k2r, k2t = derivatives(r2, t2)
            r3 = r + 0.5 * ds * k2r
            t3 = t + 0.5 * ds * k2t
            k3r, k3t = derivatives(r3, t3)
            r4 = r + ds * k3r
            t4 = t + ds * k3t
            k4r, k4t = derivatives(r4, t4)

            r_new = r + (ds / 6.0) * (k1r + 2 * k2r + 2 * k3r + k4r)
            t_new = t + (ds / 6.0) * (k1t + 2 * k2t + 2 * k3t + k4t)

            norm = np.linalg.norm(t_new)
            if norm > 1e-12:
                t_new /= norm
            else:
                break

            r = r_new
            t = t_new
            path.append(r.copy())

            # Check exit conditions after update
            if r[1] <= y_min_obj:
                exited_bottom = True
                break
            if r[1] >= y_max_obj:
                exited_top = True
                break

            step += 1

        # Handle ray termination based on exit side
        if exited_bottom:
            # Correct possible overshoot beyond y_min_obj
            if r[1] < y_min_obj:
                if len(path) >= 2:
                    r_prev = path[-2]
                    alpha = (y_min_obj - r_prev[1]) / (r[1] - r_prev[1])
                    r_exit = r_prev + alpha * (r - r_prev)
                    r = r_exit
                    path[-1] = r_exit
                else:
                    r[1] = y_min_obj
                    path.append(r.copy())
            # Proceed to Stage 3 (lens)
        elif exited_top:
            # Ray exited through top – it will never reach the lens
            return None
        else:
            # Exceeded max_steps without reaching either boundary – discard
            return None

        # ---- STAGE 3: Homogeneous region from object exit to lens ----
        if r[1] > y_lens:
            if abs(t[1]) > 1e-12:
                # Correct straight-line propagation to y_lens (t[1] is negative)
                s = (y_lens - r[1]) / t[1]   # positive when moving downward
                r = r + t * s
                path.append(r.copy())
            else:
                # t[1] ~ 0 (horizontal ray) – unlikely, but fallback
                r[1] = y_lens
                path.append(r.copy())

        r_end = r.copy()
        t_end = t.copy()

    else:
        # Legacy mode (no geometry): trace from ray_start_y to lower bound
        r = np.array([x_start, ray_start_y], dtype=np.float64)
        t = np.array([0.0, -1.0], dtype=np.float64)
        target_y = y_min
        path = [r.copy()]

        def get_n_legacy(grid_x, grid_y, y_world):
            gx = max(0, min(grid_size[0] - 1, grid_x))
            gy = max(0, min(grid_size[1] - 1, grid_y))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                n = map_coordinates(n_values, [[gx], [gy]], order=1, mode='nearest')[0]
            return max(n, 0.0)

        def grad_legacy(grid_x, grid_y, y_world):
            eps = 1e-3
            eps_x = eps / dx
            eps_y = eps / dy
            n_xp = get_n_legacy(grid_x + eps_x, grid_y, y_world)
            n_xm = get_n_legacy(grid_x - eps_x, grid_y, y_world)
            dn_dx = (n_xp - n_xm) / (2 * eps_x * dx)
            n_yp = get_n_legacy(grid_x, grid_y + eps_y, y_world + eps)
            n_ym = get_n_legacy(grid_x, grid_y - eps_y, y_world - eps)
            dn_dy = (n_yp - n_ym) / (2 * eps_y * dy)
            return dn_dx, dn_dy

        def derivatives_legacy(r_local, t_local):
            gx = (r_local[0] - x_grid0) / dx
            gy = (r_local[1] - y_grid0) / dy
            yw = r_local[1]
            n = get_n_legacy(gx, gy, yw)
            if n < 1e-6:
                return np.zeros(2), np.zeros(2)
            dnx, dny = grad_legacy(gx, gy, yw)
            dr = t_local
            dt = (1.0 / n) * np.array([dnx, dny])
            return dr, dt

        for step in range(max_steps):
            if r[1] <= target_y:
                break

            k1r, k1t = derivatives_legacy(r, t)
            r2 = r + 0.5 * ds * k1r
            t2 = t + 0.5 * ds * k1t
            k2r, k2t = derivatives_legacy(r2, t2)
            r3 = r + 0.5 * ds * k2r
            t3 = t + 0.5 * ds * k2t
            k3r, k3t = derivatives_legacy(r3, t3)
            r4 = r + ds * k3r
            t4 = t + ds * k3t
            k4r, k4t = derivatives_legacy(r4, t4)

            r_new = r + (ds / 6.0) * (k1r + 2 * k2r + 2 * k3r + k4r)
            t_new = t + (ds / 6.0) * (k1t + 2 * k2t + 2 * k3t + k4t)

            norm = np.linalg.norm(t_new)
            if norm > 1e-12:
                t_new /= norm
            else:
                break

            r = r_new
            t = t_new
            path.append(r.copy())

        # If we didn't reach target_y due to max_steps, extrapolate linearly
        if r[1] > target_y:
            if abs(t[1]) > 1e-12:
                dt_needed = (target_y - r[1]) / t[1]
                r_end = r + t * dt_needed
                path.append(r_end)
                r = r_end
            else:
                path.append(np.array([r[0], target_y]))
                r = path[-1]

        r_end = r.copy()
        t_end = t.copy()

    return {
        'path': np.array(path),
        'r_end': r_end,
        't_end': t_end
    }