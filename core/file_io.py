"""
File input/ouput utilities.

Supports loading THz-TDS CSV files containing:
- time (ps)
- real signal
- imaginary signal
"""
import pandas as pd
import numpy as np

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
    df = pd.read_csv(filepath)
    df.columns = [str(c).strip().lower() for c in df.columns] # Normalize header
    df = df.rename(columns={    # Dict rename
        "t": "time",
        "time (ps)": "time",
        "time(ps)": "time",
        "delay": "time",
        "ps": "time",

        "re": "real",
        "ex": "real",
        "inphase": "real",
        "in phase": "real",

        "im": "imag",
        "imaginary": "imag",
        "ey": "imag",
        "quadrature": "imag",

        "cplx": "complex",
        "z": "complex",
        "e": "complex",
        "e field": "complex",
        "efield": "complex",
    })

    have_real = "real" in df.columns
    have_imag = "imag" in df.columns
    have_cplx = "complex" in df.columns

    if have_cplx and (not have_real or not have_imag):
        c = df["complex"].astype(complex)
        if not have_real:
            df["real"] = np.real(c)
        if not have_imag:
            df["imag"] = np.imag(c)

    if "complex" not in df.columns:
        if "imag" not in df.columns and "real" in df.columns:
            df["imag"] = 0.0
        df["complex"] = df["real"] + 1j * df["imag"]

    return df[["time", "real", "imag", "complex"]]