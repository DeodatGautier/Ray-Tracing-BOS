"""
core/refractive_index.py - Refractive index function implementations
with support for fixed parameters and zero shift (x0) as the 5th parameter.
All functions use self.params[4] for horizontal shift.
"""

import numpy as np
from typing import List, Optional
from abc import ABC, abstractmethod

from utils.constants import FunctionType


class RefractiveIndexFunction(ABC):
    """Abstract base class for refractive index functions."""

    def __init__(self, params: List[float], fixed_indices: Optional[List[int]] = None):
        """
        Parameters
        ----------
        params : list of float
            Full list of 5 parameters: [A, B, C, D, x0].
        fixed_indices : list of int, optional
            Indices of parameters that are fixed (not optimized).
        """
        if len(params) != 5:
            raise ValueError("Refractive index functions require exactly 5 parameters: A, B, C, D, x0")
        self.params = np.array(params, dtype=np.float64)
        self.fixed_indices = fixed_indices if fixed_indices is not None else []
        self.variable_mask = [i not in self.fixed_indices for i in range(5)]

    def get_variable_params(self) -> np.ndarray:
        """Return only the variable parameters (for optimization)."""
        return self.params[self.variable_mask]

    def update_variable_params(self, var_params: np.ndarray):
        """Update only the variable parameters."""
        var_idx = 0
        for i in range(5):
            if i not in self.fixed_indices:
                self.params[i] = var_params[var_idx]
                var_idx += 1

    @abstractmethod
    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Calculate refractive index at given coordinates."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get function description."""
        pass


class GaussianFunction(RefractiveIndexFunction):
    """Gaussian refractive index distribution."""

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        A, B, C, D = self.params[:4]
        x0 = self.params[4]
        rx = x - x0
        r = np.sqrt(rx ** 2 + y ** 2)
        return A + (B - A) * np.exp(-C * (r ** D))

    def get_description(self) -> str:
        return "Gaussian: n(r) = A + (B - A) * exp(-C * r^D)"


class LorentzianFunction(RefractiveIndexFunction):
    """Lorentzian refractive index distribution."""

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        A, B, C, D = self.params[:4]
        x0 = self.params[4]
        rx = x - x0
        r = np.sqrt(rx ** 2 + y ** 2)
        return A + (B - A) / (1 + C * (r ** D))

    def get_description(self) -> str:
        return "Lorentzian: n(r) = A + (B - A) / (1 + C * r^D)"


class StepFunction(RefractiveIndexFunction):
    """Step function refractive index distribution (smoothed with sigmoid)."""

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        A, B, C, D = self.params[:4]   # D controls steepness
        x0 = self.params[4]
        rx = x - x0
        r = np.sqrt(rx ** 2 + y ** 2)
        # Clip exponent argument to avoid overflow
        arg = D * (r - C)
        arg = np.clip(arg, -700, 700)
        return A + (B - A) / (1 + np.exp(arg))

    def get_description(self) -> str:
        return "Smoothed step: n(r) = A + (B-A)/(1+exp(D*(r-C))) (D controls steepness)"


class ParabolicFunction(RefractiveIndexFunction):
    """Parabolic refractive index distribution."""

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        A, B, C = self.params[:3]
        x0 = self.params[4]
        rx = x - x0
        r = np.sqrt(rx ** 2 + y ** 2)
        return np.where(r < C, A + (B - A) * (1 - (r / C) ** 2), A)

    def get_description(self) -> str:
        return "Parabolic: n(r) = A + (B - A) * (1 - (r/C)^2) if r < C else A"


class LinearXFunction(RefractiveIndexFunction):
    """Linear gradient along x: n(x) = A + B*(x - x0)"""

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        A, B, _, _ = self.params[:4]   # C, D unused
        x0 = self.params[4]
        return A + B * (x - x0)

    def get_description(self) -> str:
        return "Linear X: n(x) = A + B*(x - x0) (C, D unused)"


class RefractiveIndexType:
    """Container for refractive index function types."""

    FUNCTIONS = {
        FunctionType.GAUSSIAN: GaussianFunction,
        FunctionType.LORENTZIAN: LorentzianFunction,
        FunctionType.STEP: StepFunction,
        FunctionType.PARABOLIC: ParabolicFunction,
        FunctionType.LINEARX: LinearXFunction,   # new
    }

    DESCRIPTIONS = {
        FunctionType.GAUSSIAN: "Gaussian distribution",
        FunctionType.LORENTZIAN: "Lorentzian distribution",
        FunctionType.STEP: "Smoothed step function",
        FunctionType.PARABOLIC: "Parabolic distribution",
        FunctionType.LINEARX: "Linear gradient along X",
    }

    FORMULAS = {
        FunctionType.GAUSSIAN: "n(r) = A + (B - A) * exp(-C * r^D)",
        FunctionType.LORENTZIAN: "n(r) = A + (B - A) / (1 + C * r^D)",
        FunctionType.STEP: "n(r) = A + (B-A)/(1+exp(D*(r-C)))",
        FunctionType.PARABOLIC: "n(r) = A + (B - A) * (1 - (r/C)^2) if r &lt; C else A",
        FunctionType.LINEARX: "n(x) = A + B·(x − x₀)",
    }

    @classmethod
    def get_function(cls, func_type: str, params: List[float],
                     fixed_indices: Optional[List[int]] = None) -> RefractiveIndexFunction:
        """Get refractive index function by type, with optional fixed indices."""
        func_class = cls.FUNCTIONS.get(func_type)
        if func_class is None:
            raise ValueError(f"Unknown function type: {func_type}")
        return func_class(params, fixed_indices)

    @classmethod
    def get_description(cls, func_type: str) -> str:
        """Get description for function type."""
        return cls.DESCRIPTIONS.get(func_type, "Unknown function")

    @classmethod
    def get_formula(cls, func_type: str) -> str:
        """Get formula for function type."""
        return cls.FORMULAS.get(func_type, "")