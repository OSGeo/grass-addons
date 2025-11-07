#!/usr/bin/env python
#!/usr/bin/env python
import numpy as np
from scipy.spatial import ConvexHull

def _continuum_removal(spec):
    s = np.asarray(spec, dtype=np.float32)
    if np.any(np.isnan(s)):
        return np.full_like(s, np.nan)

    x = np.arange(s.size, dtype=np.float32)
    points = np.column_stack((x, s))
    try:
        hull = ConvexHull(points)
        x_h = points[hull.vertices, 0]
        y_h = points[hull.vertices, 1]

        # Sort hull vertices
        i = np.argsort(x_h)
        x_h, y_h = x_h[i], y_h[i]

        # Keep only upper hull (where continuum >= signal)
        # remove lower part of the convex hull
        upper_mask = np.gradient(y_h, x_h) >= 0
        if np.sum(upper_mask) < 2:
            upper_mask = np.ones_like(upper_mask, dtype=bool)

        x_h, y_h = x_h[upper_mask], y_h[upper_mask]

        # Interpolate continuum
        cont = np.interp(x, x_h, y_h)

        # Force continuum to be >= signal and > 0
        cont = np.maximum(cont, s)
        cont = np.maximum(cont, 1e-6)

        r = s / cont
        return np.clip(r, 0.0, 1.0).astype(np.float32)
    except Exception:
        return np.full_like(s, np.nan)
