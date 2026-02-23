"""
build.py - Build script for Ray Tracing BOS using Nuitka.
Run this script from the project root directory (where main.py is located).
"""

import os
import sys
import subprocess
import shutil
import argparse
import importlib.util
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
RESOURCE_DIR = PROJECT_ROOT / "resources"
ICON_FILE = RESOURCE_DIR / "icon.ico"
OUTPUT_NAME = "RayTracingBOS"

# ----------------------------------------------------------------------
# Dependency check
# ----------------------------------------------------------------------
def check_nuitka():
    """Verify that Nuitka is installed."""
    spec = importlib.util.find_spec("nuitka")
    if spec is None:
        print("ERROR: Nuitka is not installed.")
        print("Please install it with: pip install nuitka")
        return False
    return True

def check_compiler():
    """Quick check if a C compiler is available (optional)."""
    if shutil.which("cl") is not None:
        return True
    if shutil.which("gcc") is not None:
        return True
    print("Warning: Could not find a C compiler. Nuitka might fail.")
    print("Make sure you have Visual Studio Build Tools or MinGW installed.")
    return False

# ----------------------------------------------------------------------
# Build function
# ----------------------------------------------------------------------
def clean_build():
    """Remove previous build and output files."""
    dirs = ["build", "RayTracingBOS.dist", "RayTracingBOS.build"]
    for d in dirs:
        path = PROJECT_ROOT / d
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path)
    for exe in PROJECT_ROOT.glob("*.exe"):
        if exe.name.startswith(OUTPUT_NAME):
            print(f"Removing {exe}...")
            exe.unlink()

def run_nuitka(args):
    """Run Nuitka with the constructed command line, using python -m nuitka."""
    cmd = [sys.executable, "-m", "nuitka"]

    # Basic options
    cmd.append("--standalone")
    if args.onefile:
        cmd.append("--onefile")
    if not args.console:
        cmd.append("--windows-disable-console")

    # Plugins
    cmd.append("--enable-plugin=pyqt5")

    # Resources
    if RESOURCE_DIR.exists():
        cmd.append(f"--include-data-dir={RESOURCE_DIR}=resources")
    else:
        print(f"Warning: Resource directory {RESOURCE_DIR} not found.")

    # Icon
    if ICON_FILE.exists():
        cmd.append(f"--windows-icon-from-ico={ICON_FILE}")
    else:
        print(f"Warning: Icon file {ICON_FILE} not found.")

    # Output
    cmd.extend(["--output-dir=build", f"--output-file={args.name}.exe"])

    # Debug / verbose
    if args.debug:
        cmd.append("--verbose")

    # Main script
    cmd.append(str(MAIN_SCRIPT))

    print("Running Nuitka with command:")
    print(" ".join(cmd))
    print("-" * 60)

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Build Ray Tracing BOS with Nuitka.")
    parser.add_argument("--onefile", action="store_true", default=True,
                        help="Build a single executable file (default: True)")
    parser.add_argument("--console", action="store_true",
                        help="Keep console window open (for debugging)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable verbose Nuitka output")
    parser.add_argument("--name", type=str, default=OUTPUT_NAME,
                        help=f"Output executable name (default: {OUTPUT_NAME})")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build directories before building")
    args = parser.parse_args()

    print("=" * 60)
    print("Ray Tracing BOS - Nuitka Build Script")
    print("=" * 60)

    os.chdir(PROJECT_ROOT)

    # Check dependencies
    if not check_nuitka():
        sys.exit(1)
    check_compiler()  # just a warning

    # Clean if requested
    if args.clean:
        clean_build()

    # Run build
    success = run_nuitka(args)

    if success:
        print("\n" + "=" * 60)
        print("Build successful!")
        exe_path = PROJECT_ROOT / f"{args.name}.exe"
        if exe_path.exists():
            print(f"Executable created at: {exe_path}")
        else:
            print("Executable should be in the current directory.")
        print("=" * 60)
    else:
        print("\nBuild failed. Check the output above for errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()