"""
File input/ouput utilities.

Supports loading THz-TDS CSV files containing:
- time (ps)
- real signal
- imaginary signal
"""
import pandas as pd

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load THz-TDS data from CSV.

    Args:
        filepath (str): Absolute path to the .csv file.

    Returns:
      pd.DataFrame: A pandas DataFrame containing:
        - 'time': Time axis (ps)
        - 'real': Real part of the signal
        - 'imag': Imaginary part of the signal
        - 'complex': Complex (real + j*imag)

    """
    col_names = ["time", "real", "imag"]
    df = pd.read_csv(filepath, header=0, names=col_names, usecols=[0, 1, 2])

    df["complex"] = df["real"] + 1j * df["imag"]
    return df