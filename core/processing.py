"""
The core signal processing functions used by the application.
"""
import numpy as np
from scipy import signal

def apply_window(t, x, window_type="None", start_idx=0, stop_idx=None, tukey_alpha=0.5, zero_outside_window=True):
    """
    Apply a window to the complex time-domain signal.

    Args:
        t: Time axis array (ps).
        x: Complex signal array.
        window_type: Window function name ("None", "hann", "hamming", "tukey", ...).
        start_idx: Start index of the window region.
        stop_idx: Stop index  of the window region.
        tukey_alpha: Alpha parameter for Tukey window.

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

    if window_type == "tukey":
        w = signal.get_window(("tukey", tukey_alpha), window_len)
    elif window_type == "None":
        w = np.ones(window_len)
    else:
        w = signal.get_window(window_type, window_len)

    if zero_outside_window:
        xw = np.zeros_like(x)
        xw[start_idx:stop_idx] = x[start_idx:stop_idx] * w
    else:
        xw = x.copy()
        xw[start_idx:stop_idx] *= w

    return xw, w, start_idx, stop_idx

def compute_fft(t, x, window_type="None", start_idx=0, stop_idx=None, tukey_alpha=0.5):
    """
    Computes Fast Fourier Transform (FFT) of time-domain signal.
    
    Args:
        t : Time axis array (ps)
        x : Complex signal array
        window_type : Window function name ("None", "hann", "hamming", "tukey", ...).
        start_idx : Start index for windowing
        stop_idx : Stop index for windowing
        tukey_alpha : Alpha parameter for Tukey window
        
    Returns:
        A dictionary with:
         - "Freqs": Frequency axis (THz)
         - "FFT": Complex FFT output
         - "Magnitude": abs(FFT)
         - "Phase": angle(FFT) in radians
         - "Magnitude (dB)": 20*log10(Magnitude)
         - "Unwrapped Phase": Continuous phase without 2pi jumps

    """
    xw, w, start_idx, stop_idx = apply_window(
        t, x,
        window_type=window_type,
        start_idx=start_idx,
        stop_idx=stop_idx,
        tukey_alpha=tukey_alpha,
        zero_outside_window=True
    )
    
    dt = float(t[1] - t[0])
    X = np.fft.fft(xw)
    f = np.fft.fftfreq(len(xw), d=dt)

    mag = np.abs(X)
    phase = np.angle(X)
    phase_u = np.unwrap(phase)
    mag_db = 20 * np.log10(np.maximum(mag, 1e-12))

    half = len(xw) // 2
    return {
        "Freqs": f[:half],
        "FFT": X[:half],
        "Magnitude": mag[:half],
        "Phase": phase[:half],
        "Magnitude (dB)": mag_db[:half],
        "Unwrapped Phase": phase_u[:half]
    }