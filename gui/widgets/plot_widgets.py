"""
gui/widgets/plot_widgets.py - Modern scientific visualization with rational minimalism.
"""

import numpy as np
from typing import Dict
from scipy.interpolate import interp1d, CubicSpline
from scipy.stats import norm

from .base_plot_widget import BasePlotWidget
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable

plt.style.use('default')

# Modern color palette inspired by scientific visualization tools
COLORS = {
    # Primary colors for data
    'primary_blue': '#0066CC',    # Mathematica/C++ blue
    'primary_green': '#00A86B',   # Mathematica green
    'primary_red': '#CC3333',     # Mathematica red
    'primary_orange': '#FF6B00',  # Mathematica orange
    'primary_purple': '#9933CC',  # Mathematica purple

    # Neutral tones
    'dark_gray': '#2C3E50',
    'medium_gray': '#7F8C8D',
    'light_gray': '#BDC3C7',
    'background': '#F9F9F9',
    'grid': '#E8E8E8',

    # Semantic colors
    'success': '#27AE60',
    'warning': '#F39C12',
    'error': '#E74C3C',
    'info': '#3498DB',

    # Dark mode compatible
    'text': '#2C3E50',
    'axis': '#34495E',
}

# Enhanced color maps
def create_scientific_cmap(name='coolwarm_enhanced'):
    """Create enhanced scientific colormaps with better perceptual uniformity."""
    if name == 'coolwarm_enhanced':
        # Enhanced coolwarm with better contrast
        colors = [
            (0.0, '#1A237E'),      # Deep blue
            (0.25, '#3949AB'),     # Blue
            (0.5, '#E8EAF6'),      # Light neutral
            (0.75, '#F06292'),     # Pink
            (1.0, '#B71C1C')       # Deep red
        ]
    elif name == 'sequential_blue':
        # Sequential blue for scalar fields
        colors = [
            (0.0, '#FFFFFF'),      # White
            (0.2, '#E3F2FD'),      # Very light blue
            (0.4, '#90CAF9'),      # Light blue
            (0.6, '#42A5F5'),      # Medium blue
            (0.8, '#1976D2'),      # Dark blue
            (1.0, '#0D47A1')       # Deep blue
        ]
    elif name == 'diverging':
        # Diverging colormap for signed data
        colors = [
            (0.0, '#2166AC'),      # Deep blue
            (0.25, '#67A9CF'),     # Medium blue
            (0.5, '#F7F7F7'),      # Neutral white
            (0.75, '#EF8A62'),     # Light red
            (1.0, '#B2182B')       # Deep red
        ]
    else:
        # Default viridis-like
        colors = [
            (0.0, '#440154'),      # Deep purple
            (0.3, '#31688E'),      # Blue
            (0.6, '#35B779'),      # Green
            (0.8, '#FDE725')       # Yellow
        ]

    return LinearSegmentedColormap.from_list(name, colors)

# Create colormaps
CMAP_COOLWARM = create_scientific_cmap('coolwarm_enhanced')
CMAP_SEQUENTIAL = create_scientific_cmap('sequential_blue')
CMAP_DIVERGING = create_scientific_cmap('diverging')
CMAP_VIRIDIS = plt.cm.viridis

# Configure global matplotlib settings
plt.rcParams.update({
    # Font settings
    'font.family': ['DejaVu Sans', 'Arial', 'sans-serif'],
    'font.size': 9,
    'font.weight': 'normal',

    # Axes settings
    'axes.facecolor': 'white',
    'axes.edgecolor': COLORS['axis'],
    'axes.linewidth': 0.8,
    'axes.grid': True,
    'axes.grid.axis': 'both',
    'axes.grid.which': 'major',
    'axes.labelcolor': COLORS['text'],
    'axes.labelsize': 9,
    'axes.labelweight': 'medium',
    'axes.titlesize': 10,
    'axes.titleweight': 'semibold',
    'axes.titlecolor': COLORS['dark_gray'],
    'axes.spines.top': False,
    'axes.spines.right': False,

    # Line settings
    'lines.linewidth': 1.2,
    'lines.markersize': 4,
    'lines.markeredgewidth': 0.5,

    # Grid settings
    'grid.color': COLORS['grid'],
    'grid.linewidth': 0.5,
    'grid.alpha': 0.6,
    'grid.linestyle': ':',

    # Tick settings
    'xtick.color': COLORS['axis'],
    'ytick.color': COLORS['axis'],
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 3.5,
    'ytick.major.size': 3.5,
    'xtick.minor.size': 2.0,
    'ytick.minor.size': 2.0,

    # Legend settings
    'legend.fontsize': 8,
    'legend.frameon': True,
    'legend.framealpha': 0.9,
    'legend.facecolor': 'white',
    'legend.edgecolor': COLORS['light_gray'],
    'legend.borderpad': 0.4,
    'legend.labelspacing': 0.3,

    # Figure settings
    'figure.facecolor': 'white',
    'figure.edgecolor': 'white',
    'figure.dpi': 100,
    'figure.titlesize': 11,
    'figure.titleweight': 'semibold',

    # Savefig settings
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'savefig.transparent': False,

    # Errorbar settings
    'errorbar.capsize': 2,

    # Mathtext settings
    'mathtext.default': 'regular',
    'mathtext.fontset': 'dejavusans',
})

def apply_minimal_style(ax, title=None, xlabel=None, ylabel=None, zlabel=None):
    """Apply consistent minimal style to axes."""
    if title:
        ax.set_title(title, pad=10, fontsize=10, fontweight='semibold')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, fontweight='medium')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, fontweight='medium')
    if zlabel:
        ax.set_zlabel(zlabel, fontsize=9, fontweight='medium')

    # Ensure spines are visible but minimal
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color(COLORS['axis'])

    # Set aspect ratio for 2D plots
    if not hasattr(ax, 'get_zlim'):  # Not 3D
        ax.set_aspect('auto')

def create_colorbar(fig, mappable, ax, label=None, orientation='vertical'):
    """Create minimal colorbar."""
    cbar = fig.colorbar(mappable, ax=ax, orientation=orientation,
                       shrink=0.8, pad=0.02, aspect=30)
    cbar.outline.set_linewidth(0.5)
    cbar.outline.set_edgecolor(COLORS['light_gray'])

    if label:
        cbar.set_label(label, fontsize=8, fontweight='medium', labelpad=5)

    cbar.ax.tick_params(labelsize=7, width=0.5)
    return cbar

class TopDownWidget(BasePlotWidget):
    """
    2D Top View with Scientific Minimalism.
    """

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(10, 7))
        self.ax = None

    def update_plot(self, results: Dict):
        """Update 2D top-down view with simulation results."""
        try:
            self.figure.clear()
            self.figure.set_facecolor('white')

            if 'rays' not in results or len(results['rays']) == 0:
                # Create empty plot with message
                self.ax = self.figure.add_subplot(111)
                self.ax.text(0.5, 0.5, 'No simulation data',
                           transform=self.ax.transAxes,
                           ha='center', va='center',
                           fontsize=11, color=COLORS['medium_gray'])
                self.ax.set_axis_off()
                self.canvas.draw()
                return

            # Create 2D plot
            self.ax = self.figure.add_subplot(111)

            # Plot refractive index field as background
            if 'n_values' in results and 'grid' in results:
                self._plot_refractive_index_background(results)

            # Plot ray trajectories from top-down view
            self._plot_ray_trajectories_topdown(results)

            # Apply minimal style
            apply_minimal_style(self.ax,
                              title='Top-Down View of Ray Trajectories',
                              xlabel='X Position (mm)',
                              ylabel='Y Position (mm)')

            # Adjust layout
            self.figure.tight_layout(pad=2.0)
            self.canvas.draw()

        except Exception as e:
            print(f"Error in top-down plot: {e}")

    def _plot_refractive_index_background(self, results: Dict):
        """Plot refractive index as background colormap."""
        try:
            n_values = results['n_values']
            grid = results['grid']
            X = grid['X']
            Y = grid['Y']

            # Create colormap background
            im = self.ax.imshow(n_values.T,  # Transpose for correct orientation
                               extent=[X.min(), X.max(), Y.min(), Y.max()],
                               origin='lower',
                               cmap=CMAP_SEQUENTIAL,
                               alpha=0.6,
                               aspect='auto')

            # Add subtle contour lines
            contour_levels = 10
            CS = self.ax.contour(X, Y, n_values.T,
                                levels=contour_levels,
                                colors='white',
                                linewidths=0.3,
                                alpha=0.3)

            # Add colorbar
            cbar = self.figure.colorbar(im, ax=self.ax, shrink=0.8)
            cbar.set_label('Refractive Index', fontsize=8, fontweight='medium')
            cbar.ax.tick_params(labelsize=7)

        except Exception as e:
            print(f"Error in background plot: {e}")

    def _plot_ray_trajectories_topdown(self, results: Dict):
        """Plot ray trajectories from top-down perspective."""
        rays = results['rays']

        # Show rays
        total_rays = len(rays)
        if total_rays == 0:
            return

        # Select rays for visualization
        num_rays_to_show = min(60, total_rays)
        if total_rays <= num_rays_to_show:
            indices = list(range(total_rays))
        else:
            step = max(1, total_rays // num_rays_to_show)
            indices = list(range(0, total_rays, step))

        # Ensure we don't exceed desired number
        if len(indices) > num_rays_to_show:
            indices = indices[:num_rays_to_show]

        # Color progression
        colors = plt.cm.plasma(np.linspace(0.2, 0.8, len(indices)))

        # Plot entry and exit lines with DIFFERENT styles
        y_start = results.get('ray_start_y', 10.0)
        y_end = -y_start  # Assuming symmetric bounds

        # Entry line - solid green line
        self.ax.axhline(y=y_start, color=COLORS['primary_green'],
                       linestyle='-', linewidth=1.2, alpha=0.7, label='Entry plane')

        # Exit line - dashed red line
        self.ax.axhline(y=y_end, color=COLORS['primary_red'],
                       linestyle='--', linewidth=1.2, alpha=0.7, label='Exit plane')

        # Plot rays
        for idx, color in zip(indices, colors):
            ray = rays[idx]
            if len(ray) > 10:
                try:
                    x = ray[:, 0]
                    y = ray[:, 1]

                    # Plot ray with smooth line
                    self.ax.plot(x, y,
                               color=color,
                               linewidth=0.8,
                               alpha=0.6,
                               solid_capstyle='round')

                    # Add start and end markers for first 5 rays only (to avoid clutter)
                    if idx in indices[:5]:
                        self.ax.plot(x[0], y[0], '^',
                                   color=color,
                                   markersize=4,
                                   markeredgecolor='white',
                                   markeredgewidth=0.5)
                        self.ax.plot(x[-1], y[-1], 'v',
                                   color=color,
                                   markersize=4,
                                   markeredgecolor='white',
                                   markeredgewidth=0.5)

                except Exception:
                    continue

        # Add legend
        if len(indices) > 0:
            # Ray legend entry
            self.ax.plot([], [], color=colors[0], linewidth=0.8,
                        label=f'Ray trajectories ({len(indices)} shown)')
            self.ax.legend(loc='upper right', fontsize=8)


class PlotWidget2D(BasePlotWidget):
    """2D visualization with scientific minimalism."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(11, 8))

    def update_plot(self, results: Dict):
        """Update 2D plots with clean scientific styling."""
        try:
            self.figure.clear()
            self.figure.set_facecolor('white')

            if 'rays' not in results or len(results['rays']) == 0:
                # Create empty plot
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No simulation data',
                       transform=ax.transAxes,
                       ha='center', va='center',
                       fontsize=11, color=COLORS['medium_gray'])
                ax.set_axis_off()
                self.canvas.draw()
                return

            # Create subplots with adjusted spacing
            self.axes = self.figure.subplots(2, 2,
                                           gridspec_kw={'hspace': 0.45, 'wspace': 0.25})
            self.axes = self.axes.flatten()

            # Plot 1: Ray trajectories - show MORE rays
            self._plot_ray_trajectories(results, self.axes[0])

            # Plot 2: Refractive index profile
            self._plot_refractive_index_profile(results, self.axes[1])

            # Plot 3: Ray deflection (using sensor coordinates)
            self._plot_ray_deflection(results, self.axes[2])

            # Plot 4: Refractive index contour
            self._plot_refractive_index_contour(results, self.axes[3])

            # Set overall title
            self.figure.suptitle('Ray Tracing Analysis',
                               fontsize=11,
                               fontweight='semibold',
                               color=COLORS['dark_gray'],
                               y=0.98)

            self.figure.tight_layout(rect=[0, 0, 1, 0.96])
            self.canvas.draw()

        except Exception as e:
            print(f"Error in 2D plot: {e}")

    def _plot_ray_trajectories(self, results: Dict, ax):
        """Plot ray trajectories with minimal style - show MORE rays."""
        rays = results['rays']

        # Background refractive index (subtle)
        if 'n_values' in results and 'grid' in results:
            try:
                X = results['grid']['X']
                Y = results['grid']['Y']
                n_values = results['n_values']

                # Simplified contour background
                skip = max(1, X.shape[0] // 60)
                X_sub = X[::skip, ::skip]
                Y_sub = Y[::skip, ::skip]
                n_sub = n_values[::skip, ::skip]

                # Light contour fill
                contour = ax.contourf(X_sub, Y_sub, n_sub,
                                     levels=15,
                                     cmap=CMAP_SEQUENTIAL,
                                     alpha=0.2,
                                     antialiased=True)

            except Exception:
                pass

        # Plot rays
        max_rays_to_plot = min(40, len(rays))
        step = max(1, len(rays) // max_rays_to_plot)

        for i in range(0, len(rays), step):
            ray = rays[i]
            if len(ray) > 1:
                x = ray[:, 0]
                y = ray[:, 1]

                # Color based on impact parameter
                color = plt.cm.plasma(i / max(1, len(rays)))
                ax.plot(x, y, color=color, linewidth=0.6, alpha=0.6)

        apply_minimal_style(ax,
                          title='Ray Trajectories',
                          xlabel='X Position (mm)',
                          ylabel='Y Position (mm)')

        # Add entry and exit lines
        y_start = results.get('ray_start_y', 10.0)
        y_end = -y_start  # Assuming symmetric bounds

        ax.axhline(y=y_start, color=COLORS['primary_green'],
                  linestyle='-', linewidth=1.0, alpha=0.5)
        ax.axhline(y=y_end, color=COLORS['primary_red'],
                  linestyle='--', linewidth=1.0, alpha=0.5)

        # Add subtle grid
        ax.grid(True, alpha=0.3, linestyle=':')

    def _plot_refractive_index_profile(self, results: Dict, ax):
        """Plot refractive index radial profile."""
        if 'n_profile' in results and 'grid' in results:
            x_grid = results['grid']['x_grid']
            n_profile = results['n_profile']

            # Main plot with subtle styling
            ax.plot(x_grid, n_profile,
                   color=COLORS['primary_blue'],
                   linewidth=1.5,
                   alpha=0.9,
                   marker='o',
                   markersize=2,
                   markevery=20)

            # Fill area for emphasis
            ax.fill_between(x_grid, n_profile,
                           color=COLORS['primary_blue'],
                           alpha=0.1)

            # Mark key features
            if len(n_profile) > 0:
                idx_max = np.argmax(n_profile)
                idx_min = np.argmin(n_profile)

                if idx_max < len(x_grid):
                    ax.plot(x_grid[idx_max], n_profile[idx_max], '^',
                           color=COLORS['primary_red'],
                           markersize=6,
                           markeredgecolor='white',
                           markeredgewidth=1.0,
                           label=f'max: {n_profile[idx_max]:.3f}')

                if idx_min < len(x_grid):
                    ax.plot(x_grid[idx_min], n_profile[idx_min], 'v',
                           color=COLORS['primary_green'],
                           markersize=6,
                           markeredgecolor='white',
                           markeredgewidth=1.0,
                           label=f'min: {n_profile[idx_min]:.3f}')

                if 'idx_max' in locals() or 'idx_min' in locals():
                    ax.legend(loc='best', fontsize=7)

            apply_minimal_style(ax,
                              title='Radial Profile',
                              xlabel='Radial Position (mm)',
                              ylabel='Refractive Index')

            # Set y-limits with small margin
            y_min, y_max = np.min(n_profile), np.max(n_profile)
            margin = (y_max - y_min) * 0.05
            ax.set_ylim(y_min - margin, y_max + margin)

    def _plot_ray_deflection(self, results: Dict, ax):
        """Plot ray deflection profile using sensor coordinates."""
        if 'x_starts' in results and 'displacements' in results:
            # Use sensor coordinates if available, fallback to x_starts
            x = results.get('x_sensor', results['x_starts'])
            displacements = results['displacements']

            # Scatter plot with color mapping
            sc = ax.scatter(x, displacements,
                          c=np.abs(displacements),  # Color by magnitude
                          cmap='viridis',
                          s=15,
                          alpha=0.7,
                          edgecolors='white',
                          linewidth=0.3)

            # Zero reference line
            ax.axhline(y=0, color=COLORS['medium_gray'],
                      linestyle='--',
                      linewidth=0.8,
                      alpha=0.5,
                      zorder=0)

            apply_minimal_style(ax,
                              title='Deflection Profile',
                              xlabel='Sensor X (mm)',
                              ylabel='Deflection (mm)')

            # Colorbar
            cbar = create_colorbar(self.figure, sc, ax, '|Δx| (mm)', 'vertical')

    def _plot_refractive_index_contour(self, results: Dict, ax):
        """Plot refractive index contour map."""
        if 'n_values' in results and 'grid' in results:
            X = results['grid']['X']
            Y = results['grid']['Y']
            n_values = results['n_values']

            # Reduce resolution for performance and clarity
            skip = max(1, X.shape[0] // 80)
            X_sub = X[::skip, ::skip]
            Y_sub = Y[::skip, ::skip]
            n_sub = n_values[::skip, ::skip]

            # Contour plot with clean styling
            contour = ax.contourf(X_sub, Y_sub, n_sub,
                                 levels=20,
                                 cmap=CMAP_COOLWARM,
                                 alpha=0.85,
                                 antialiased=True)

            # Subtle contour lines
            ax.contour(X_sub, Y_sub, n_sub,
                      levels=10,
                      colors='white',
                      alpha=0.3,
                      linewidths=0.3)

            # Mark center
            ax.plot(0, 0, 'o',
                   color='white',
                   markersize=5,
                   markeredgecolor=COLORS['dark_gray'],
                   markeredgewidth=1.0)

            apply_minimal_style(ax,
                              title='Refractive Index Map',
                              xlabel='X Position (mm)',
                              ylabel='Y Position (mm)')

            # Colorbar
            create_colorbar(self.figure, contour, ax, 'Refractive Index', 'vertical')

            # Set equal aspect
            ax.set_aspect('equal', adjustable='datalim')


class ComparisonPlotWidget(BasePlotWidget):
    """Comparison widget with essential scientific analysis."""

    def __init__(self, parent=None):
        super().__init__(parent, figsize=(10, 8))

    def update_plot(self, simulation_results: Dict, experimental_data: Dict):
        """Update comparison plots with scientific minimalism."""
        try:
            self.figure.clear()
            self.figure.set_facecolor('white')

            if not simulation_results or not experimental_data:
                # Empty state
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'Load experimental data for comparison',
                       transform=ax.transAxes,
                       ha='center', va='center',
                       fontsize=11, color=COLORS['medium_gray'])
                ax.set_axis_off()
                self.canvas.draw()
                return

            # Create subplots
            self.axes = self.figure.subplots(2, 1,
                                           height_ratios=[2, 1],
                                           gridspec_kw={'hspace': 0.25})

            # Plot 1: Data comparison with smooth simulation curve
            self._plot_data_comparison(simulation_results, experimental_data, self.axes[0])

            # Plot 2: Residual analysis
            self._plot_residual_analysis(simulation_results, experimental_data, self.axes[1])

            # Overall title
            self.figure.suptitle('Experimental vs Simulation Analysis',
                               fontsize=11,
                               fontweight='semibold',
                               color=COLORS['dark_gray'],
                               y=0.98)

            self.figure.tight_layout(rect=[0, 0, 1, 0.96])
            self.canvas.draw()

        except Exception as e:
            print(f"Error in comparison plot: {e}")

    def _plot_data_comparison(self, sim_results: Dict, exp_data: Dict, ax):
        """Plot comparison of experimental and simulated data using sensor coordinates."""
        x_exp = exp_data.get('x', [])
        delta_exp = exp_data.get('delta', [])

        if 'x_starts' in sim_results and 'displacements' in sim_results:
            # Use sensor coordinates if available, fallback to x_starts
            x_sim = sim_results.get('x_sensor', sim_results['x_starts'])
            delta_sim = sim_results['displacements']

            if len(x_sim) > 1 and len(x_exp) > 0:
                # Sort simulation data for interpolation
                sort_idx = np.argsort(x_sim)
                x_sim_sorted = x_sim[sort_idx]
                delta_sim_sorted = delta_sim[sort_idx]

                # Interpolate simulation data to experimental points for R² calculation
                interp_func = interp1d(x_sim_sorted, delta_sim_sorted, kind='cubic',
                                      bounds_error=False, fill_value='extrapolate')
                delta_sim_interp = interp_func(x_exp)

                # Plot experimental data with error bars if available
                if 'error' in exp_data:
                    exp_error = exp_data['error']
                    ax.errorbar(x_exp, delta_exp, yerr=exp_error,
                               fmt='o',
                               color=COLORS['primary_blue'],
                               ecolor=COLORS['light_gray'],
                               elinewidth=1.0,
                               capsize=2.0,
                               capthick=1.0,
                               markersize=4,
                               label='Experimental ± 1σ',
                               alpha=0.8)
                else:
                    ax.plot(x_exp, delta_exp, 'o',
                           color=COLORS['primary_blue'],
                           markersize=4,
                           markeredgecolor='white',
                           markeredgewidth=0.5,
                           label='Experimental',
                           alpha=0.8)

                # Plot SMOOTH simulation curve using cubic spline
                if len(x_sim_sorted) >= 4:  # Need at least 4 points for cubic spline
                    try:
                        # Create cubic spline for smooth curve
                        cs = CubicSpline(x_sim_sorted, delta_sim_sorted)
                        x_fine = np.linspace(x_sim_sorted.min(), x_sim_sorted.max(), 200)
                        y_fine = cs(x_fine)

                        ax.plot(x_fine, y_fine, '-',
                               color=COLORS['primary_red'],
                               linewidth=1.8,
                               alpha=0.9,
                               label='Simulation (cubic spline)',
                               zorder=2)
                    except Exception:
                        # Fallback to linear interpolation
                        ax.plot(x_sim_sorted, delta_sim_sorted, '-',
                               color=COLORS['primary_red'],
                               linewidth=1.5,
                               alpha=0.9,
                               label='Simulation',
                               zorder=2)
                else:
                    # Linear interpolation for few points
                    ax.plot(x_sim_sorted, delta_sim_sorted, '-',
                           color=COLORS['primary_red'],
                           linewidth=1.5,
                           alpha=0.9,
                           label='Simulation',
                           zorder=2)

                # Calculate and display metrics
                r2 = self._calculate_r2(delta_exp, delta_sim_interp)
                rmse = np.sqrt(np.mean((delta_exp - delta_sim_interp) ** 2))

                # Add metrics box
                metrics_text = f'R² = {r2:.4f}\nRMSE = {rmse:.3f} mm'
                props = dict(boxstyle='round', facecolor='white',
                           edgecolor=COLORS['light_gray'], alpha=0.8)
                ax.text(0.98, 0.02, metrics_text,
                       transform=ax.transAxes,
                       verticalalignment='bottom',
                       horizontalalignment='right',
                       fontsize=8,
                       bbox=props)

                apply_minimal_style(ax,
                                  title='Data Comparison',
                                  xlabel='Sensor X (mm)',
                                  ylabel='Deflection (mm)')

                ax.legend(loc='best', fontsize=8)
                ax.grid(True, alpha=0.2)

    def _plot_residual_analysis(self, sim_results: Dict, exp_data: Dict, ax):
        """Plot residual analysis using sensor coordinates."""
        x_exp = exp_data.get('x', [])
        delta_exp = exp_data.get('delta', [])

        if 'x_starts' in sim_results and 'displacements' in sim_results:
            # Use sensor coordinates if available, fallback to x_starts
            x_sim = sim_results.get('x_sensor', sim_results['x_starts'])
            delta_sim = sim_results['displacements']

            if len(x_sim) > 1 and len(x_exp) > 0:
                # Interpolate and calculate residuals
                interp_func = interp1d(x_sim, delta_sim, kind='cubic',
                                      bounds_error=False, fill_value='extrapolate')
                delta_sim_interp = interp_func(x_exp)
                residuals = delta_sim_interp - delta_exp

                # Create two subplots
                divider = make_axes_locatable(ax)
                ax_left = ax
                ax_right = divider.append_axes("right", size="35%", pad=0.15)

                # Left: Residuals vs Position
                ax_left.scatter(x_exp, residuals,
                              color=COLORS['primary_purple'],
                              s=20,
                              alpha=0.7,
                              edgecolors='white',
                              linewidth=0.3)

                # Zero line
                ax_left.axhline(y=0, color=COLORS['medium_gray'],
                              linestyle='--',
                              linewidth=0.8,
                              alpha=0.5)

                apply_minimal_style(ax_left,
                                  title='Residuals',
                                  xlabel='Sensor X (mm)',
                                  ylabel='Residual (mm)')

                ax_left.grid(True, alpha=0.2)

                # Right: Histogram with normal distribution
                ax_right.hist(residuals,
                            bins=15,
                            color=COLORS['primary_green'],
                            alpha=0.6,
                            edgecolor='white',
                            linewidth=0.5,
                            orientation='horizontal',
                            density=True)

                # Fit normal distribution
                mu, std = norm.fit(residuals)
                xmin, xmax = ax_right.get_ylim()
                y = np.linspace(xmin, xmax, 100)
                p = norm.pdf(y, mu, std)

                # Plot normal distribution
                ax_right.plot(p, y,
                            color=COLORS['dark_gray'],
                            linewidth=1.5,
                            label=f'Normal fit\nμ = {mu:.4f} mm\nσ = {std:.4f} mm')

                # Mean and ±1σ lines
                ax_right.axhline(y=mu, color=COLORS['primary_red'],
                               linestyle='-',
                               linewidth=1.0,
                               alpha=0.7)
                ax_right.axhline(y=mu + std, color=COLORS['light_gray'],
                               linestyle=':',
                               linewidth=0.8,
                               alpha=0.5)
                ax_right.axhline(y=mu - std, color=COLORS['light_gray'],
                               linestyle=':',
                               linewidth=0.8,
                               alpha=0.5)

                apply_minimal_style(ax_right,
                                  title='Distribution',
                                  xlabel='Density')

                ax_right.set_ylabel('')
                ax_right.legend(loc='upper right', fontsize=7)
                ax_right.yaxis.set_ticklabels([])

                # Add statistics text
                stats_text = f'N = {len(residuals)}'
                props = dict(boxstyle='round', facecolor='white',
                           edgecolor=COLORS['light_gray'], alpha=0.8)
                ax_right.text(0.02, 0.98, stats_text,
                            transform=ax_right.transAxes,
                            verticalalignment='top',
                            horizontalalignment='left',
                            fontsize=7,
                            bbox=props)

    def _calculate_r2(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate R² score."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

        if ss_tot == 0:
            return 0.0
        return 1 - (ss_res / ss_tot)