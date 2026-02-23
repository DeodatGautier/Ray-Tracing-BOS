"""
utils/geometry.py - Geometry of the BOS experiment
Includes lens and sensor positions calculated via thin lens formula.
"""

from dataclasses import dataclass


@dataclass
class ExperimentGeometry:
    """
    Geometry parameters for BOS setup.
    All distances are in millimeters.

    The object (refractive index field) is assumed to be axisymmetric and
    located between y = -thickness/2 and y = +thickness/2.
    The background screen is at y = +thickness/2 + distance_bg.
    The lens (entrance pupil) is at y = -thickness/2 - distance_lens.
    The sensor plane is computed via the lens formula: 1/f = 1/a + 1/b,
    where a = distance from lens to background, b = distance from lens to sensor.

    Rays start at the background and propagate downward (–y direction).
    Integration stops at the lens plane; the displacement on the sensor
    is calculated from the ray angle and the lens formula.
    """

    distance_bg: float      # object to background screen (mm)
    distance_lens: float    # object to lens (mm)
    thickness: float        # object thickness along optical axis (mm)
    focal_length: float     # lens focal length (mm)

    @property
    def y_center(self) -> float:
        """Coordinate of object center (assumed at 0)."""
        return 0.0

    @property
    def y_bg(self) -> float:
        """Background screen y-coordinate (distance from object center)."""
        return self.distance_bg

    @property
    def y_lens(self) -> float:
        """Lens y-coordinate (distance from object center, negative for lens)."""
        return -self.distance_lens

    # For backward compatibility, we also provide y_cam (old name)
    @property
    def y_cam(self) -> float:
        """Alias for y_lens to keep old code working."""
        return self.y_lens

    @property
    def y_min_obj(self) -> float:
        """Lower boundary of object (exit side)."""
        return -self.thickness / 2

    @property
    def y_max_obj(self) -> float:
        """Upper boundary of object (entry side)."""
        return self.thickness / 2

    @property
    def a(self) -> float:
        """Distance from lens to background screen."""
        return self.y_bg - self.y_lens  # = distance_bg + distance_lens

    @property
    def b(self) -> float:
        """Distance from lens to sensor, computed by thin lens formula."""
        if self.a <= self.focal_length:
            # If object is too close, the formula would give negative or infinite.
            # In practice, we cannot focus; we return a large number as fallback.
            return 1e6
        return (self.focal_length * self.a) / (self.a - self.focal_length)

    @property
    def y_sensor(self) -> float:
        """Sensor plane y-coordinate."""
        return self.y_lens - self.b

    def to_dict(self) -> dict:
        """Convert to dict for passing to worker processes (pickle‑safe)."""
        return {
            'distance_bg': self.distance_bg,
            'distance_lens': self.distance_lens,
            'thickness': self.thickness,
            'focal_length': self.focal_length,
            'y_bg': self.y_bg,
            'y_lens': self.y_lens,
            'y_min_obj': self.y_min_obj,
            'y_max_obj': self.y_max_obj,
            'a': self.a,
            'b': self.b
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        return cls(
            distance_bg=data['distance_bg'],
            distance_lens=data['distance_lens'],
            thickness=data['thickness'],
            focal_length=data['focal_length']
        )