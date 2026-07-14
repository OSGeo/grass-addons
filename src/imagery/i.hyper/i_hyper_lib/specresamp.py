#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spectral resampling for i.hyper.specresamp.

Supports Gaussian convolution, linear interpolation, and nearest neighbour
resampling of hyperspectral reflectance / radiance data.
"""

from __future__ import annotations

import numpy as np

_FWHM_TO_SIGMA = 1.0 / (2.0 * np.sqrt(2.0 * np.log(2.0)))


def _gen_range(start: float, end: float, step: float) -> np.ndarray:
    """Inclusive 1-D array from *start* to *end* with given *step*."""
    n = int(np.floor((end - start) / step)) + 1
    return start + np.arange(n, dtype=np.float64) * step


def parse_wavelength_ranges(
    wl_str: str, fwhm_str: str | None = None
) -> tuple[np.ndarray, np.ndarray | None]:
    """Parse wavelength ranges and optional per‑range FWHM.

    Parameters
    ----------
    wl_str : str
        Comma‑separated ranges ``'400-700,700-2500'``.
        Each piece may include an explicit step via ``'400-700/8.3'``.
        A bare number is treated as a single‑wavelength range.
    fwhm_str : str, optional
        Comma‑separated FWHM values, one per range.  When given the step for
        each range defaults to its FWHM value if no explicit ``/step`` was
        supplied.

    Returns
    -------
    out_wl : ndarray
        1‑D array of output centre wavelengths (nm).
    out_fwhm : ndarray or None
        1‑D array of per‑band FWHM values or *None*.
    """
    wl_pieces = [p.strip() for p in wl_str.split(",") if p.strip()]
    fwhm_pieces: list[str] = []
    if fwhm_str is not None:
        fwhm_pieces = [p.strip() for p in fwhm_str.split(",") if p.strip()]

    if fwhm_pieces and len(fwhm_pieces) != len(wl_pieces) and len(fwhm_pieces) != 1:
        raise ValueError(
            f"FWHM count ({len(fwhm_pieces)}) must be 1 or equal to "
            f"wavelength range count ({len(wl_pieces)})"
        )

    bands: list[float] = []
    fwhms: list[float] = []

    for i, piece in enumerate(wl_pieces):
        if not piece:
            continue

        has_step = "/" in piece
        if has_step:
            bounds, step_s = piece.split("/", 1)
            step = float(step_s.strip())
        else:
            bounds = piece
            step = None

        if "-" in bounds:
            start_s, end_s = bounds.split("-", 1)
            start = float(start_s.strip())
            end = float(end_s.strip())
        else:
            start = float(bounds)
            end = start

        if start < 0 or end < 0:
            raise ValueError(f"Negative wavelength in '{piece}'")
        if end < start:
            start, end = end, start

        fwhm_val = float(fwhm_pieces[i]) if fwhm_pieces else None
        if step is None:
            step = fwhm_val
        if step is None:
            step = 1.0
        if step <= 0:
            raise ValueError(f"Non‑positive step / FWHM in '{piece}'")

        gen = _gen_range(start, end, step)
        bands.extend(gen.tolist())
        if fwhm_val is not None:
            fwhms.extend([fwhm_val] * len(gen))

    out_wl = np.array(bands, dtype=np.float64)
    out_fwhm = np.array(fwhms, dtype=np.float64) if fwhms else None
    return out_wl, out_fwhm


def gaussian_weight_matrix(
    in_wl: np.ndarray, out_wl: np.ndarray, fwhm: np.ndarray | float
) -> np.ndarray:
    """Build *(n_out, n_in)* Gaussian weight matrix.

    Each output band is a Gaussian centred at ``out_wl[j]`` with sigma
    derived from *fwhm*.
    """
    fwhm_arr = np.atleast_1d(np.asarray(fwhm, dtype=np.float64))
    if len(fwhm_arr) == 1:
        fwhm_arr = np.full(len(out_wl), fwhm_arr[0])
    elif len(fwhm_arr) != len(out_wl):
        raise ValueError(
            f"FWHM length ({len(fwhm_arr)}) must be 1 or match "
            f"out_wl length ({len(out_wl)})"
        )
    sigma = fwhm_arr * _FWHM_TO_SIGMA

    diff = out_wl[:, np.newaxis] - in_wl[np.newaxis, :]
    w = np.exp(-0.5 * (diff / sigma[:, np.newaxis]) ** 2)
    return w


def resample_gaussian(
    spectra: np.ndarray, weight_matrix: np.ndarray
) -> np.ndarray:
    """Apply pre‑computed Gaussian weight matrix.

    Parameters
    ----------
    spectra : ndarray, shape *(n_pixels, n_in)*
    weight_matrix : ndarray, shape *(n_out, n_in)*

    Returns
    -------
    ndarray, shape *(n_pixels, n_out)*
    """
    row_sums = weight_matrix.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums > 0, row_sums, 1.0)
    w_norm = weight_matrix / row_sums
    return spectra @ w_norm.T


def resample_linear(
    in_wl: np.ndarray, spectra: np.ndarray, out_wl: np.ndarray
) -> np.ndarray:
    """Linear interpolation to *out_wl* for every spectrum.

    Wavelengths outside *in_wl* produce NaN.
    """
    result = np.empty((spectra.shape[0], len(out_wl)), dtype=spectra.dtype)
    for j, target in enumerate(out_wl):
        i = np.searchsorted(in_wl, target)
        if i == 0 or i == len(in_wl):
            result[:, j] = np.nan
        else:
            t = (target - in_wl[i - 1]) / (in_wl[i] - in_wl[i - 1])
            result[:, j] = (1.0 - t) * spectra[:, i - 1] + t * spectra[:, i]
    return result


def resample_nearest(
    in_wl: np.ndarray, spectra: np.ndarray, out_wl: np.ndarray
) -> np.ndarray:
    """Nearest‑neighbour assignment.

    Each output band takes the value of the input band closest in wavelength.
    """
    idx = np.argmin(
        np.abs(in_wl[np.newaxis, :] - out_wl[:, np.newaxis]), axis=1
    )
    return spectra[:, idx]


def resample(
    spectra: np.ndarray,
    in_wl: np.ndarray,
    out_wl: np.ndarray,
    method: str = "gaussian",
    fwhm: np.ndarray | float | None = None,
) -> np.ndarray:
    """Resample spectra from input to output wavelengths.

    Parameters
    ----------
    spectra : ndarray, shape *(n_pixels, n_in)*
    in_wl : ndarray, shape *(n_in,)*
    out_wl : ndarray, shape *(n_out,)*
    method : ``'gaussian'`` | ``'linear'`` | ``'nearest'``
    fwhm : ndarray or float, optional
        Required for ``method='gaussian'``.

    Returns
    -------
    ndarray, shape *(n_pixels, n_out)*
    """
    if method == "gaussian":
        if fwhm is None:
            raise ValueError("FWHM required for Gaussian method")
        wm = gaussian_weight_matrix(in_wl, out_wl, fwhm)
        return resample_gaussian(spectra, wm)
    if method == "linear":
        return resample_linear(in_wl, spectra, out_wl)
    if method == "nearest":
        return resample_nearest(in_wl, spectra, out_wl)
    raise ValueError(f"Unknown method: '{method}'")
