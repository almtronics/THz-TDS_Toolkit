"""
Shared dataset state across the UI.

DataManager is an in-memory storage used to:
- Load CSC datasets
- Enforce shared time axis across datasets
- Store per-dataset results, cached for plotting
"""
import os

import numpy as np

from .file_io import load_data

class DataManager:
    """
    Manages loaded datasets and shared application state.
    """
    def __init__(self) -> None:
        """
        Initialize an empty dataset.
        """
        # Each datasetis stored ar a dict:
        # [{'name': str, 'path': str, 'df': DataFrame, 'results': dict}, ...]
        self.datasets = []
        self.reference_path = None

    def set_reference(self, path) -> None:
        """
        Set which dataset path is treated as the user-selected reference.

        Args:
            path: Dataset path that should be considered the reference selection.
        """
        self.reference_path = path

    def get_reference(self) -> dict | None:
        """
        Return the currently selected reference dataset.

        Returns:
            The dataset dict matching reference_path.
        """
        if not self.reference_path:
            return None
        for ds in self.datasets:
            if ds.get("path") == self.reference_path:
                return ds
        return None

    def load_files(self, file_paths)-> list[tuple[str, str]]:
        """
        Parses a list of file paths and appends them to the dataset list.
        
        Args:
            file_paths: List of CSV file paths to load.
        Returns:
            List of (path, reason) for files that were skipped.
        """
        skipped = []  # list of skipped files (path, reason)
        for path in file_paths:
            try:
                df = load_data(path)
                if not self._time_axis_matches_reference(df):
                    skipped.append((path, "Time axis mismatch (does not match first dataset)"))
                    continue
                self.datasets.append({
                    "name": os.path.splitext(os.path.basename(path))[0],
                    "path": path,
                    "df": df,
                    "results": {}
                })
            except Exception as e:
                print(f"Error loading {path}: {e}")
        return skipped

    def get_all(self) -> list[dict]:
        """Returns all currently loaded datasets."""
        return self.datasets
    
    def clear(self) -> None:
        """Removes all datasets and clear the selected reference."""
        self.datasets = []
        self.reference_path = None

    def _time_axis_matches_reference(self, df_new, atol=1e-12) -> bool:
        """
        Checks that a dataset time axis matches the first loaded dataset.

        Args:
            df_new: New dataset dataframe.
            atol: Absolute tolerance used for float comparison.

        Returns:
            True if the time axis matches the reference or if no reference exists yet.
        """
        if not self.datasets:
            return True

        t_ref = self.datasets[0]["df"]["time"].to_numpy()
        t_new = df_new["time"].to_numpy()

        if len(t_ref) != len(t_new):
            return False

        return bool(np.allclose(t_ref, t_new, rtol=0.0, atol=atol))
    