"""Physical constants and unit conventions."""

import numpy as np

C0 = 299_792_458.0
MU0 = 4.0e-7 * np.pi
EPS0 = 1.0 / (MU0 * C0**2)
ETA0 = np.sqrt(MU0 / EPS0)


def wavelength_from_frequency(freq_hz: float) -> float:
    return C0 / freq_hz


def wavenumber(wavelength: float) -> float:
    return 2.0 * np.pi / wavelength
