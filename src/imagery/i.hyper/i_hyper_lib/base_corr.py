#!/usr/bin/env python
import numpy as np


def _baseline_correction(spec):
    s = np.asarray(spec, dtype=np.float32)
    if not np.any(np.isfinite(s)):
        return np.full_like(s, np.nan)
    baseline = np.nanmin(s)
    return s - baseline
