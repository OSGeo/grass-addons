#!/usr/bin/env python3
import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d


# called by i.hyper.preproc
def _savgol_preserve_nan(spec, win, poly, deriv, interp_nodata):
    s = np.asarray(spec, dtype=np.float32)
    nanmask = ~np.isfinite(s)

    if interp_nodata:
        v = np.asarray(s, dtype=np.float32)
        m = np.isfinite(v)
        if m.sum() >= 2:
            xi = np.arange(v.size, dtype=np.float32)
            f = interp1d(
                xi[m], v[m], kind="linear", fill_value="extrapolate", assume_sorted=True
            )
            s = f(xi).astype(np.float32)
        s[nanmask] = np.nan

    out = np.full_like(s, np.nan, dtype=np.float32)
    valid = np.isfinite(s)
    if valid.sum() >= win:
        out[valid] = savgol_filter(
            s[valid], win, poly, deriv=deriv, mode="interp"
        ).astype(np.float32)
    else:
        out[valid] = s[valid]
    return out
