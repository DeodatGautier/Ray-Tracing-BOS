"""
utils/data_io.py - Data input/output utilities
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import warnings


class DataLoader:
    """Utility class for loading experimental data."""

    @staticmethod
    def load_data(file_path: str) -> Dict[str, np.ndarray]:
        """
        Load experimental data from various file formats.

        Args:
            file_path: Path to data file

        Returns:
            Dictionary with 'x' and 'delta' arrays
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type from extension
        ext = file_path.suffix.lower()

        if ext in ['.xlsx', '.xls']:
            return DataLoader._load_excel(file_path)
        elif ext in ['.csv', '.txt']:
            return DataLoader._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _load_excel(file_path: Path) -> Dict[str, np.ndarray]:
        """Load data from Excel file."""
        try:
            # Try different sheet names and header options
            for sheet_name in [0, None]:
                for header in [None, 0]:
                    try:
                        df = pd.read_excel(
                            file_path,
                            sheet_name=sheet_name,
                            header=header,
                            engine='openpyxl'
                        )

                        if df.shape[1] >= 2:
                            x = df.iloc[:, 0].values.astype(float)
                            delta = df.iloc[:, 1].values.astype(float)

                            # Sort by x values
                            sort_idx = np.argsort(x)
                            x = x[sort_idx]
                            delta = delta[sort_idx]

                            return {'x': x, 'delta': delta}

                    except Exception as e:
                        continue

            raise ValueError("Could not read valid data from Excel file")

        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")

    @staticmethod
    def _load_csv(file_path: Path) -> Dict[str, np.ndarray]:
        """Load data from CSV or text file."""
        try:
            # Try different delimiters and formats
            delimiters = [',', ';', '\t', ' ']

            for delimiter in delimiters:
                try:
                    df = pd.read_csv(
                        file_path,
                        delimiter=delimiter,
                        header=None,
                        engine='python'
                    )

                    if df.shape[1] >= 2:
                        x = df.iloc[:, 0].values.astype(float)
                        delta = df.iloc[:, 1].values.astype(float)

                        # Sort by x values
                        sort_idx = np.argsort(x)
                        x = x[sort_idx]
                        delta = delta[sort_idx]

                        return {'x': x, 'delta': delta}

                except Exception as e:
                    continue

            raise ValueError("Could not parse CSV file with common delimiters")

        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")


class DataExporter:
    """Utility class for exporting simulation results."""

    @staticmethod
    def export_results(file_path: str, results: Dict[str, Any]):
        """
        Export simulation results to file.

        Args:
            file_path: Output file path
            results: Simulation results dictionary
        """
        file_path = Path(file_path)

        # Determine format from extension
        ext = file_path.suffix.lower()

        if ext == '.json':
            DataExporter._export_json(file_path, results)
        elif ext == '.csv':
            DataExporter._export_csv(file_path, results)
        else:
            raise ValueError(f"Unsupported export format: {ext}")

    @staticmethod
    def _export_json(file_path: Path, results: Dict[str, Any]):
        """Export results to JSON file."""
        # Convert numpy arrays to lists for JSON serialization
        json_results = {}

        for key, value in results.items():
            if isinstance(value, np.ndarray):
                json_results[key] = value.tolist()
            elif hasattr(value, '__dict__'):
                json_results[key] = DataExporter._object_to_dict(value)
            else:
                json_results[key] = value

        with open(file_path, 'w') as f:
            json.dump(json_results, f, indent=2, default=str)

    @staticmethod
    def _export_csv(file_path: Path, results: Dict[str, Any]):
        """Export results to CSV file."""
        # Extract main data
        if 'rays' in results and len(results['rays']) > 0:
            # Export ray data
            rays_data = []

            for i, ray in enumerate(results['rays']):
                for point in ray:
                    rays_data.append([i, point[0], point[1]])

            df_rays = pd.DataFrame(rays_data, columns=['ray_id', 'x', 'y'])
            df_rays.to_csv(file_path.with_stem(f"{file_path.stem}_rays"), index=False)

        # Export deflection data
        if 'x_starts' in results and 'displacements' in results:
            df_deflection = pd.DataFrame({
                'x_start': results['x_starts'],
                'x_end': results['x_ends'] if 'x_ends' in results else np.zeros_like(results['x_starts']),
                'displacement': results['displacements']
            })
            df_deflection.to_csv(file_path.with_stem(f"{file_path.stem}_deflection"), index=False)

        # Export refractive index profile
        if 'n_profile' in results and 'grid' in results:
            x_grid = results['grid'].get('x_grid', [])
            if len(x_grid) > 0:
                df_profile = pd.DataFrame({
                    'x': x_grid,
                    'n': results['n_profile']
                })
                df_profile.to_csv(file_path.with_stem(f"{file_path.stem}_profile"), index=False)

    @staticmethod
    def _object_to_dict(obj: Any) -> Dict:
        """Convert object to dictionary for JSON serialization."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, np.ndarray):
                        result[key] = value.tolist()
                    elif hasattr(value, '__dict__'):
                        result[key] = DataExporter._object_to_dict(value)
                    else:
                        result[key] = value
            return result
        return str(obj)