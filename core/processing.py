"""
The core signal processing functions used by the application.
"""
import numpy as np
from scipy import signal

def apply_window(t, x, window_type="None", window_args=None, start_idx=0, stop_idx=None, zero_outside_window=True):
    """
    Apply a window to the complex time-domain signal.

    Args:
        t: Time axis array (ps).
        x: Complex signal array.
        window_type: Window function name ("None", "hann", "hamming", "tukey", ...).
        start_idx: Start index of the window region.
        stop_idx: Stop index  of the window region.
        window_args: Optional list/tuple of extra window parameters for the selected window type

    Returns:
        xw (np.ndarray): Windowed signal.
        w (np.ndarray): Window values applied to x[start_idx:stop_idx] (length = stop_idx-start_idx).
        start_idx (int): Clamped start index.
        stop_idx (int): Clamped stop index.
    """
    if stop_idx is None:
        stop_idx = len(x)

    start_idx = max(0, int(start_idx))
    stop_idx = min(len(x), int(stop_idx))
    if stop_idx < start_idx:
        stop_idx = start_idx

    window_len = stop_idx - start_idx

    if window_len == 0:
        return x.copy(), np.array([]), start_idx, stop_idx

    if window_type == "None":
        w = np.ones(window_len)
    else:
        window_args = [] if window_args is None else list(window_args)
        win_spec = window_type if len(window_args) == 0 else (window_type, *window_args)
        w = signal.get_window(win_spec, window_len)

    if zero_outside_window:
        xw = np.zeros_like(x)
        xw[start_idx:stop_idx] = x[start_idx:stop_idx] * w
    else:
        xw = x.copy()
        xw[start_idx:stop_idx] *= w

    return xw, w, start_idx, stop_idx

def compute_fft(t, x, window_type="None", window_args=None, start_idx=0, stop_idx=None):
    """
    Computes Fast Fourier Transform (FFT) of time-domain signal.
    
    Args:
        t : Time axis array (ps)
        x : Complex signal array
        window_type : Window function name ("None", "hann", "hamming", "tukey", ...).
        start_idx : Start index for windowing
        stop_idx : Stop index for windowing
        window_args: Optional list/tuple of extra window parameters
        
    Returns:
        A dictionary with:
         - "Freqs": Frequency axis (THz)
         - "FFT": Complex FFT output

    """
    xw, w, start_idx, stop_idx = apply_window(
        t,
        x,
        window_type=window_type,
        window_args=window_args,
        start_idx=start_idx,
        stop_idx=stop_idx,
        zero_outside_window=True,
    )

    dt = float(t[1] - t[0])
    X = np.fft.fft(xw)
    f = np.fft.fftfreq(len(xw), d=dt)

    half = len(xw) // 2
    return {
        "Freqs": f[:half],
        "FFT": X[:half],
    }

def normalize_fft (fft: dict, ref_fft: dict) -> dict:
    """
    Normalize an FFT to a reference FFT.

    Args:
        fft: dict with keys "Freqs", "FFT"
        ref_fft: dict with keys "Freqs", "FFT"
    Returns:
        dict with keys "Freqs", "FFT" (normalized)
    """
    X = fft["FFT"]
    X_ref = ref_fft["FFT"]
    # Avoid divide by 0
    floor = 1e-12
    X_ref_safe = np.where(np.abs(X_ref) < floor, floor + 0j, X_ref)
    return {"Freqs": fft["Freqs"], "FFT": X / X_ref_safe}

def compute_mag(fft_complex):
    """
    Computes magnitude of the complex FFT.
    
    Args:
        fft_complex : Complex FFT
        
    Returns:
        A dictionary with:
         - "Magnitude": abs(FFT)
         - "Magnitude (dB)": 20*log10(Magnitude)

    """
    mag = np.abs(fft_complex)
    mag_db = 20 * np.log10(np.maximum(mag, 1e-12))
    return {
        "Magnitude": mag,
        "Magnitude (dB)": mag_db,
    }

def compute_phase(fft_complex):
    """
    Computes phase of the complex FFT.
    
    Args:
        fft_complex : Complex FFT
        
    Returns:
        A dictionary with:
         - "Phase": angle(FFT) in radians

    """
    return {"Phase": np.angle(fft_complex)}

def unwrap_phase(phase_wrapped):
    """
    Unwrap the wrapped phase.
    
    Args:
        phase_wrapped : Wrapped phase
        
    Returns:
        A dictionary with:
         - "Unwrapped Phase": Continuous phase without 2pi jumps

    """
    return {"Unwrapped Phase": np.unwrap(phase_wrapped)}
    