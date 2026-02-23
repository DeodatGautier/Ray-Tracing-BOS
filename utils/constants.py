"""
utils/constants.py - Application constants
"""

# Function types
class FunctionType:
    GAUSSIAN = "gaussian"
    LORENTZIAN = "lorentzian"
    STEP = "step"
    PARABOLIC = "parabolic"
    LINEARX = "linearx"

# Default simulation parameters
DEFAULT_GRID_SIZE = (256, 256)
DEFAULT_BOUNDS = 10.0
DEFAULT_NUM_RAYS = 121
DEFAULT_STEP_SIZE = 0.008
DEFAULT_MAX_STEPS = 8000
DEFAULT_RAY_START_Y = 10.0

# Default optimization parameters
DEFAULT_LEARNING_RATE = 0.00001
DEFAULT_EPSILON = 1e-5
DEFAULT_MAX_ITERATIONS = 60

# UI constants
UI_GROUPBOX_MIN_HEIGHT = 100
UI_EXPERIMENTAL_DATA_HEIGHT = 180
UI_RESULTS_HEIGHT = 120
UI_PARAMETERS_HEIGHT = 120
UI_STATISTICS_HEIGHT = 100

# File extensions
EXCEL_EXTENSIONS = ['.xlsx', '.xls']
CSV_EXTENSIONS = ['.csv', '.txt']
ALL_DATA_EXTENSIONS = EXCEL_EXTENSIONS + CSV_EXTENSIONS

# Parameter descriptions
PARAMETER_DESCRIPTIONS = {
    FunctionType.GAUSSIAN: [
        "Refractive index at infinity",
        "Refractive index at center",
        "Decay rate",
        "Power"
    ],
    FunctionType.LORENTZIAN: [
        "Refractive index at infinity",
        "Refractive index at center",
        "Width parameter",
        "Power"
    ],
    FunctionType.STEP: [
        "Refractive index outside",
        "Refractive index inside",
        "Radius",
        "Steepness (large = sharp)"
    ],
    FunctionType.PARABOLIC: [
        "Refractive index at edge",
        "Refractive index at center",
        "Radius",
        "Unused"
    ],
    FunctionType.LINEARX: [
        "Refractive index at x = x0",
        "Gradient coefficient (dn/dx)",
        "Unused",
        "Unused"
    ],
}