"""
core package - Core functionality for ray tracing and optimization
"""

from .simulation import RayTracingSimulation, SimulationParameters
from .optimization import OptimizationWorker, OptimizationParameters
from .refractive_index import (
    RefractiveIndexFunction,
    RefractiveIndexType,
    GaussianFunction,
    LorentzianFunction,
    StepFunction,
    ParabolicFunction,
    LinearXFunction
)

__all__ = [
    'RayTracingSimulation',
    'SimulationParameters',
    'OptimizationWorker',
    'OptimizationParameters',
    'RefractiveIndexFunction',
    'RefractiveIndexType',
    'GaussianFunction',
    'LorentzianFunction',
    'StepFunction',
    'ParabolicFunction',
    'LinearXFunction'
]