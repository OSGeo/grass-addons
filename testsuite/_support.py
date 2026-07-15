"""Shared test infrastructure for the lib6sv standalone testsuite.

Loads ``libsixsv.so`` (built by ``make lib`` in this directory) and exposes
ctypes wrappers for every function needed by the test suite.  The library is
located by searching, in order:

1. ``LIB_SIXSV`` environment variable (set automatically by ``make test``).
2. ``./libsixsv.so`` in the testsuite directory.
3. ``../OBJ.*/libgrass_sixsv.so`` — GRASS build tree (sibling OBJ directory).

Also provides helpers for the OpenMP runtime (``omp_get_max_threads``, etc.)
by loading ``libgomp`` / ``libomp`` via ``ctypes.util.find_library``.
"""

import ctypes
import ctypes.util
import os
import sys

import numpy as np

_HERE   = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)

# Ensure this directory is importable (for _support itself in sub-modules)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


# ── Load the shared library ───────────────────────────────────────────────────

def _find_lib():
    candidates = [
        os.environ.get("LIB_SIXSV", ""),
        os.path.join(_HERE, "libsixsv.so"),
        *sorted(
            os.path.join(_PARENT, d, "libgrass_sixsv.so")
            for d in os.listdir(_PARENT)
            if d.startswith("OBJ.")
        ),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    raise ImportError(
        "libsixsv.so not found. Run `make lib` in testsuite/ first.\n"
        f"Searched: {[p for p in candidates if p]}"
    )


lib = ctypes.CDLL(_find_lib())


# ── OpenMP runtime helpers ────────────────────────────────────────────────────
# Try both GCC (libgomp) and Clang (libomp / libiomp5).

_omp = None
for _omp_name in ("gomp", "omp", "iomp5"):
    _omp_path = ctypes.util.find_library(_omp_name)
    if _omp_path:
        try:
            _omp = ctypes.CDLL(_omp_path)
            break
        except OSError:
            pass


def omp_get_max_threads():
    """Return omp_get_max_threads(), or None if the runtime is unavailable."""
    if _omp is None:
        return None
    _omp.omp_get_max_threads.restype = ctypes.c_int
    return int(_omp.omp_get_max_threads())


def omp_set_num_threads(n):
    """Call omp_set_num_threads(n).  No-op if the runtime is unavailable."""
    if _omp is None:
        return
    _omp.omp_set_num_threads.argtypes = [ctypes.c_int]
    _omp.omp_set_num_threads(ctypes.c_int(int(n)))


def omp_get_num_devices():
    """Return the number of OpenMP offload devices (0 = CPU only, >0 = GPU).

    Returns 0 if the OpenMP runtime pre-dates target offload (OpenMP < 4.5).
    """
    if _omp is None:
        return 0
    try:
        _omp.omp_get_num_devices.restype = ctypes.c_int
        return int(_omp.omp_get_num_devices())
    except AttributeError:
        return 0


# ── C struct mirrors (matching include/atcorr.h) ─────────────────────────────

class _LutConfigC(ctypes.Structure):
    _fields_ = [
        ("wl",               ctypes.POINTER(ctypes.c_float)),
        ("n_wl",             ctypes.c_int),
        ("aod",              ctypes.POINTER(ctypes.c_float)),
        ("n_aod",            ctypes.c_int),
        ("h2o",              ctypes.POINTER(ctypes.c_float)),
        ("n_h2o",            ctypes.c_int),
        ("sza",              ctypes.c_float),
        ("vza",              ctypes.c_float),
        ("raa",              ctypes.c_float),
        ("altitude_km",      ctypes.c_float),
        ("atmo_model",       ctypes.c_int),
        ("aerosol_model",    ctypes.c_int),
        ("surface_pressure", ctypes.c_float),
        ("ozone_du",         ctypes.c_float),
        ("mie_r_mode",       ctypes.c_float),
        ("mie_sigma_g",      ctypes.c_float),
        ("mie_m_real",       ctypes.c_float),
        ("mie_m_imag",       ctypes.c_float),
        ("brdf_type",        ctypes.c_int),
        ("brdf_params",      ctypes.c_float * 5),
        ("enable_polar",     ctypes.c_int),
    ]


class _LutArraysC(ctypes.Structure):
    _fields_ = [
        ("R_atm",      ctypes.POINTER(ctypes.c_float)),
        ("T_down",     ctypes.POINTER(ctypes.c_float)),
        ("T_up",       ctypes.POINTER(ctypes.c_float)),
        ("s_alb",      ctypes.POINTER(ctypes.c_float)),
        ("T_down_dir", ctypes.POINTER(ctypes.c_float)),
        ("R_atmQ",     ctypes.POINTER(ctypes.c_float)),
        ("R_atmU",     ctypes.POINTER(ctypes.c_float)),
    ]


_NULL_FLOAT_PTR = ctypes.cast(None, ctypes.POINTER(ctypes.c_float))


def _fptr(arr):
    return arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))


# ── Python-level LutConfig / LutArrays wrappers ───────────────────────────────

class LutConfig:
    """Python mirror of the C ``LutConfig`` struct.

    Parameters
    ----------
    wl, aod, h2o : array-like of float32
        Wavelength [µm], AOD, and water-vapour column [g/cm²] grids.
    sza, vza, raa : float
        Solar zenith, view zenith, relative azimuth [degrees].
    altitude_km : float
        Sensor altitude in km (>900 = satellite).
    atmo_model : int
        Atmosphere model (1 = US62, 2 = MIDSUM, …).
    aerosol_model : int
        Aerosol model (0 = none, 1 = continental, 2 = maritime, …).
    surface_pressure : float
        Surface pressure [hPa]; 0 = standard atmosphere.
    ozone_du : float
        Ozone column [Dobson units]; 0 = standard.
    enable_polar : int
        0 = scalar RT, 1 = vector Stokes(I,Q,U).
    """

    def __init__(self, *, wl, aod, h2o,
                 sza=30.0, vza=0.0, raa=0.0, altitude_km=1000.0,
                 atmo_model=1, aerosol_model=1,
                 surface_pressure=0.0, ozone_du=0.0,
                 enable_polar=0, **_):
        # Keep Python arrays alive for the duration of this object
        self.wl  = np.asarray(wl,  dtype=np.float32)
        self.aod = np.asarray(aod, dtype=np.float32)
        self.h2o = np.asarray(h2o, dtype=np.float32)

        c = _LutConfigC()
        c.wl    = _fptr(self.wl);  c.n_wl  = len(self.wl)
        c.aod   = _fptr(self.aod); c.n_aod = len(self.aod)
        c.h2o   = _fptr(self.h2o); c.n_h2o = len(self.h2o)
        c.sza             = float(sza)
        c.vza             = float(vza)
        c.raa             = float(raa)
        c.altitude_km     = float(altitude_km)
        c.atmo_model      = int(atmo_model)
        c.aerosol_model   = int(aerosol_model)
        c.surface_pressure = float(surface_pressure)
        c.ozone_du        = float(ozone_du)
        c.enable_polar    = int(enable_polar)
        self._c = c


class LutArrays:
    """Python mirror of the C ``LutArrays`` struct — backed by NumPy arrays."""

    def __init__(self, n_aod, n_h2o, n_wl, polar=False):
        shape = (n_aod, n_h2o, n_wl)
        self.R_atm  = np.zeros(shape, dtype=np.float32)
        self.T_down = np.ones(shape,  dtype=np.float32)
        self.T_up   = np.ones(shape,  dtype=np.float32)
        self.s_alb  = np.zeros(shape, dtype=np.float32)
        self.R_atmQ = np.zeros(shape, dtype=np.float32) if polar else None
        self.R_atmU = np.zeros(shape, dtype=np.float32) if polar else None

        c = _LutArraysC()
        c.R_atm      = _fptr(self.R_atm)
        c.T_down     = _fptr(self.T_down)
        c.T_up       = _fptr(self.T_up)
        c.s_alb      = _fptr(self.s_alb)
        c.T_down_dir = _NULL_FLOAT_PTR
        c.R_atmQ     = _fptr(self.R_atmQ) if polar else _NULL_FLOAT_PTR
        c.R_atmU     = _fptr(self.R_atmU) if polar else _NULL_FLOAT_PTR
        self._c = c


class LutSlice:
    """Per-wavelength slice returned by :func:`lut_slice`."""
    __slots__ = ("R_atm", "T_down", "T_up", "s_alb")


# ── atcorr_compute_lut ────────────────────────────────────────────────────────

lib.atcorr_compute_lut.argtypes = [ctypes.POINTER(_LutConfigC),
                                    ctypes.POINTER(_LutArraysC)]
lib.atcorr_compute_lut.restype  = ctypes.c_int


def compute_lut(cfg: LutConfig) -> LutArrays:
    """Build the 3-D [AOD × H₂O × λ] atmospheric correction LUT."""
    polar = bool(cfg._c.enable_polar)
    lut   = LutArrays(cfg._c.n_aod, cfg._c.n_h2o, cfg._c.n_wl, polar=polar)
    rc    = lib.atcorr_compute_lut(ctypes.byref(cfg._c), ctypes.byref(lut._c))
    if rc != 0:
        raise RuntimeError(f"atcorr_compute_lut returned error code {rc}")
    return lut


# ── atcorr_lut_slice ──────────────────────────────────────────────────────────

lib.atcorr_lut_slice.argtypes = [
    ctypes.POINTER(_LutConfigC),
    ctypes.POINTER(_LutArraysC),
    ctypes.c_float, ctypes.c_float,
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
]
lib.atcorr_lut_slice.restype = None


def lut_slice(cfg: LutConfig, lut: LutArrays,
              aod_val: float, h2o_val: float) -> LutSlice:
    """Bilinear interpolation of the LUT at a single (AOD, H₂O) point."""
    nw  = cfg._c.n_wl
    Rs  = np.empty(nw, dtype=np.float32)
    Tds = np.empty(nw, dtype=np.float32)
    Tus = np.empty(nw, dtype=np.float32)
    ss  = np.empty(nw, dtype=np.float32)
    lib.atcorr_lut_slice(
        ctypes.byref(cfg._c), ctypes.byref(lut._c),
        ctypes.c_float(aod_val), ctypes.c_float(h2o_val),
        _fptr(Rs), _fptr(Tds), _fptr(Tus), _fptr(ss),
        _NULL_FLOAT_PTR,
    )
    sl        = LutSlice()
    sl.R_atm  = Rs
    sl.T_down = Tds
    sl.T_up   = Tus
    sl.s_alb  = ss
    return sl


# ── Lambertian inversion (static inline in atcorr.h — re-implemented here) ───

def invert(rho_toa, R_atm, T_down, T_up, s_alb):
    """Lambertian BOA reflectance inversion: ρ_boa = y / (1 + s·y)."""
    rho_toa = np.asarray(rho_toa, dtype=np.float64)
    y = (rho_toa - R_atm) / (T_down * T_up + 1e-10)
    return (y / (1.0 + s_alb * y + 1e-10)).astype(np.float32)


# ── sixs_E0 ───────────────────────────────────────────────────────────────────

lib.sixs_E0.argtypes = [ctypes.c_float]
lib.sixs_E0.restype  = ctypes.c_float


def solar_E0(wl):
    """Thuillier solar irradiance [W m⁻² µm⁻¹] for scalar or 1-D wl [µm]."""
    if np.ndim(wl) == 0:
        return float(lib.sixs_E0(ctypes.c_float(float(wl))))
    wl = np.asarray(wl, dtype=np.float32)
    return np.array([float(lib.sixs_E0(ctypes.c_float(w))) for w in wl],
                    dtype=np.float32)


# ── sixs_earth_sun_dist2 ──────────────────────────────────────────────────────

lib.sixs_earth_sun_dist2.argtypes = [ctypes.c_int]
lib.sixs_earth_sun_dist2.restype  = ctypes.c_double


def earth_sun_dist2(doy):
    """Squared Earth–Sun distance [AU²] for day-of-year doy ∈ [1, 365]."""
    return float(lib.sixs_earth_sun_dist2(ctypes.c_int(int(doy))))


# ── sixs_chand ────────────────────────────────────────────────────────────────

lib.sixs_chand.argtypes = [ctypes.c_float] * 4
lib.sixs_chand.restype  = ctypes.c_float


def chand(xphi, xmuv, xmus, xtau):
    """Chandrasekhar Rayleigh reflectance."""
    return float(lib.sixs_chand(
        ctypes.c_float(xphi), ctypes.c_float(xmuv),
        ctypes.c_float(xmus), ctypes.c_float(xtau),
    ))


# ── sixs_odrayl ───────────────────────────────────────────────────────────────

lib.sixs_init_atmosphere.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.sixs_init_atmosphere.restype  = None

lib.sixs_odrayl.argtypes = [ctypes.c_void_p, ctypes.c_float,
                              ctypes.POINTER(ctypes.c_float)]
lib.sixs_odrayl.restype  = None

# Shared context for single-threaded helper calls (US62 standard atmosphere)
_ctx = ctypes.create_string_buffer(8192)
lib.sixs_init_atmosphere(_ctx, ctypes.c_int(1))


def odrayl(wl):
    """Rayleigh optical depth at wavelength wl [µm] under US62 atmosphere."""
    tray = ctypes.c_float(0.0)
    lib.sixs_odrayl(_ctx, ctypes.c_float(wl), ctypes.byref(tray))
    return float(tray.value)


# ── sixs_csalbr ───────────────────────────────────────────────────────────────

lib.sixs_csalbr.argtypes = [ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
lib.sixs_csalbr.restype  = None


def csalbr(xtau):
    """Rayleigh spherical albedo for optical depth xtau."""
    xalb = ctypes.c_float(0.0)
    lib.sixs_csalbr(ctypes.c_float(xtau), ctypes.byref(xalb))
    return float(xalb.value)


# ── sixs_gauss ────────────────────────────────────────────────────────────────

lib.sixs_gauss.argtypes = [ctypes.c_float, ctypes.c_float,
                             ctypes.POINTER(ctypes.c_float),
                             ctypes.POINTER(ctypes.c_float),
                             ctypes.c_int]
lib.sixs_gauss.restype  = None


def gauss(x1, x2, n):
    """Gauss-Legendre quadrature nodes and weights on [x1, x2]."""
    xa = (ctypes.c_float * n)()
    wa = (ctypes.c_float * n)()
    lib.sixs_gauss(ctypes.c_float(x1), ctypes.c_float(x2),
                   xa, wa, ctypes.c_int(n))
    return list(xa), list(wa)


# ── spatial_box_filter ────────────────────────────────────────────────────────

lib.spatial_box_filter.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int, ctypes.c_int,
    ctypes.c_int,
]
lib.spatial_box_filter.restype = None


def spatial_box_filter(data: np.ndarray, filter_half: int) -> np.ndarray:
    """Separable box filter (NaN-safe).  Returns a new array."""
    data = np.asarray(data, dtype=np.float32)
    assert data.ndim == 2, "data must be 2-D"
    nrows, ncols = data.shape
    out = np.empty_like(data)
    lib.spatial_box_filter(
        _fptr(data), _fptr(out),
        ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_int(filter_half),
    )
    return out


# ── spatial_gaussian_filter ───────────────────────────────────────────────────

lib.spatial_gaussian_filter.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int, ctypes.c_int,
    ctypes.c_float,
]
lib.spatial_gaussian_filter.restype = None


def spatial_gaussian_filter(data: np.ndarray, sigma: float) -> np.ndarray:
    """Separable Gaussian filter (NaN-safe, in-place).  Returns filtered copy."""
    data = np.asarray(data, dtype=np.float32).copy()
    assert data.ndim == 2, "data must be 2-D"
    nrows, ncols = data.shape
    lib.spatial_gaussian_filter(
        _fptr(data),
        ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_float(sigma),
    )
    return data
