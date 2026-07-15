"""Python ctypes bindings for ``libatcorr.so`` (6SV2.1-based atmospheric correction).

This module loads ``libatcorr.so`` from the GRASS add-on installation directory
(``$GISBASE/lib/``) or from the build tree.  It exposes the full public C API
as Python functions backed by NumPy arrays.

Public API
----------
- :class:`LutConfig`         — LUT grid specification and scene geometry.
- :class:`LutArrays`         — LUT output arrays shaped ``[n_aod, n_h2o, n_wl]``.
- :func:`compute_lut`        — Build the 3-D atmospheric correction LUT.
- :func:`lut_slice`          — Bilinear interpolation at a fixed (AOD, H₂O) point.
- :func:`invert`             — Lambertian BOA reflectance inversion.
- :func:`solar_E0`           — Thuillier solar irradiance spectrum.
- :func:`earth_sun_dist2`    — Seasonal Earth–Sun distance.
- :func:`apply_srf_correction` — SRF gas-transmittance correction via libRadtran.
- :func:`retrieve_pressure_isa` — ISA surface pressure from elevation.
- :func:`retrieve_h2o_940`   — H₂O column from 940 nm band depth.
- :func:`retrieve_h2o_triplet` — H₂O column from any (lo/feat/hi) triplet.
- :func:`retrieve_h2o_consensus` — Per-pixel median consensus across triplets.
- :func:`retrieve_o3_chappuis` — O₃ column from Chappuis band depth.
- :func:`retrieve_aod_ddv`   — AOD from MODIS dark-target DDV.
- :func:`retrieve_pressure_o2a` — Surface pressure from O₂-A band depth.
- :func:`retrieve_quality_mask` — Cloud/shadow/water/snow bitmask.
- :func:`retrieve_aod_maiac` — Patch-median AOD spatial regularisation.
- :func:`oe_invert_aod_h2o`  — Joint AOD + H₂O optimal-estimation retrieval.
- :func:`spectral_smooth_tikhonov` — In-place Tikhonov second-difference smoother.
- :func:`mcd43_disaggregate` — MCD43 7-band → hyperspectral kernel weight disaggregation.
- :func:`retrieve_dasf`      — DASF canopy structure factor from 710–790 nm NIR plateau.

Quick-start example::

    import numpy as np
    from atcorr import LutConfig, compute_lut, lut_slice, invert

    cfg = LutConfig(
        wl=np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32),
        aod=np.array([0.0, 0.2, 0.6],          dtype=np.float32),
        h2o=np.array([1.0, 3.0],               dtype=np.float32),
        sza=35.0, vza=5.0, raa=90.0,
        altitude_km=1000.0,   # satellite orbit
        atmo_model=1,         # US Standard 1962
        aerosol_model=1,      # continental
    )
    lut  = compute_lut(cfg)        # LutArrays [3, 2, 4]
    sl   = lut_slice(cfg, lut, aod_val=0.15, h2o_val=2.0)  # 1-D [4]
    rho  = invert(rho_toa, sl.R_atm, sl.T_down, sl.T_up, sl.s_alb)
"""

import ctypes
import os
import numpy as np

# ── Load shared library ───────────────────────────────────────────────────────
# The library is now named grass_sixsv (built by lib6sv/) following the GRASS
# convention.  An unversioned symlink libgrass_sixsv.so is created by Shlib.make
# alongside the versioned file libgrass_sixsv.<MAJOR>.<MINOR>.so.
_here      = os.path.dirname(os.path.abspath(__file__))
_gisbase   = os.environ.get("GISBASE", "")
_addonbase = os.environ.get("GRASS_ADDON_BASE", "")
_lib_candidates = [
    # 1. System / g.extension install under $GISBASE (preferred at runtime)
    os.path.join(_gisbase,   "lib", "libgrass_sixsv.so"),
    # 2. Per-user g.extension install under $GRASS_ADDON_BASE
    os.path.join(_addonbase, "lib", "libgrass_sixsv.so"),
    # 3. Build tree: lib6sv is a sibling of the directory containing this file
    #    (dev/lib6sv/python/atcorr.py  →  dev/lib6sv/OBJ.*/libgrass_sixsv.so)
    *[os.path.join(_here, "..", p, "libgrass_sixsv.so")
      for p in ("OBJ.x86_64-pc-linux-gnu", "OBJ.x86_64-linux-gnu", "build")],
]
_lib = None
for _path in _lib_candidates:
    if os.path.exists(_path):
        _lib = ctypes.CDLL(_path)
        break
if _lib is None:
    raise ImportError(
        "libgrass_sixsv.so not found. "
        "Build lib6sv/ with 'make' first, then 'make install'.\n"
        f"Searched: {_lib_candidates}"
    )


# ── C struct mirrors ──────────────────────────────────────────────────────────
class _LutConfigC(ctypes.Structure):
    # BrdfParams union: largest member = ocean (5 floats = 20 bytes)
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
        # Custom Mie fields (Phase 4)
        ("mie_r_mode",       ctypes.c_float),
        ("mie_sigma_g",      ctypes.c_float),
        ("mie_m_real",       ctypes.c_float),
        ("mie_m_imag",       ctypes.c_float),
        # BRDF fields (Phase 5): brdf_type (int) + brdf_params (union, 5 floats)
        ("brdf_type",        ctypes.c_int),
        ("brdf_params",      ctypes.c_float * 5),
        # Polarization (Phase 6): 0=scalar RT, 1=Stokes(I,Q,U)
        ("enable_polar",     ctypes.c_int),
    ]


class _LutArraysC(ctypes.Structure):
    _fields_ = [
        ("R_atm",      ctypes.POINTER(ctypes.c_float)),
        ("T_down",     ctypes.POINTER(ctypes.c_float)),
        ("T_up",       ctypes.POINTER(ctypes.c_float)),
        ("s_alb",      ctypes.POINTER(ctypes.c_float)),
        ("T_down_dir", ctypes.POINTER(ctypes.c_float)),  # NULL unless terrain requested
        ("R_atmQ",     ctypes.POINTER(ctypes.c_float)),  # NULL unless enable_polar=1
        ("R_atmU",     ctypes.POINTER(ctypes.c_float)),  # NULL unless enable_polar=1
    ]


# ── Function signatures ───────────────────────────────────────────────────────
_lib.atcorr_compute_lut.argtypes = [
    ctypes.POINTER(_LutConfigC),
    ctypes.POINTER(_LutArraysC),
]
_lib.atcorr_compute_lut.restype = ctypes.c_int

_lib.atcorr_version.argtypes = []
_lib.atcorr_version.restype  = ctypes.c_char_p

_lib.sixs_E0.argtypes = [ctypes.c_float]
_lib.sixs_E0.restype  = ctypes.c_float

_lib.sixs_earth_sun_dist2.argtypes = [ctypes.c_int]
_lib.sixs_earth_sun_dist2.restype  = ctypes.c_double

_lib.atcorr_lut_slice.argtypes = [
    ctypes.POINTER(_LutConfigC),
    ctypes.POINTER(_LutArraysC),
    ctypes.c_float,                          # aod_val
    ctypes.c_float,                          # h2o_val
    ctypes.POINTER(ctypes.c_float),          # Rs   [n_wl]
    ctypes.POINTER(ctypes.c_float),          # Tds  [n_wl]
    ctypes.POINTER(ctypes.c_float),          # Tus  [n_wl]
    ctypes.POINTER(ctypes.c_float),          # ss   [n_wl]
    ctypes.POINTER(ctypes.c_float),          # Tdds [n_wl] or NULL
]
_lib.atcorr_lut_slice.restype = None


def version() -> str:
    """Return the libatcorr version string (e.g. ``'1.0.0'``)."""
    return _lib.atcorr_version().decode()


def solar_E0(wl_um):
    """Solar irradiance E0 in W/(m² µm) from 6SV2.1 Thuillier spectrum.

    Parameters
    ----------
    wl_um : float or array-like
        Wavelength in µm.
    """
    wl_arr = np.asarray(wl_um, dtype=np.float32)
    scalar = wl_arr.ndim == 0
    wl_arr = np.atleast_1d(wl_arr)
    out = np.array([_lib.sixs_E0(float(w)) for w in wl_arr], dtype=np.float32)
    return float(out[0]) if scalar else out


def earth_sun_dist2(doy: int) -> float:
    """Squared Earth–Sun distance d² [AU²] for a given day of year.

    Parameters
    ----------
    doy : int
        Day of year [1, 365].

    Returns
    -------
    float
        d² in AU² (< 1 near perihelion DOY≈3, > 1 near aphelion DOY≈185).
    """
    return _lib.sixs_earth_sun_dist2(int(doy))


# ── Public Python API ─────────────────────────────────────────────────────────
class LutConfig:
    """Configuration for LUT computation.

    Parameters
    ----------
    wl            : 1D array of wavelengths (µm), float32
    aod           : 1D array of AOD at 550 nm values, float32
    h2o           : 1D array of column water vapour (g/cm²), float32
    sza           : solar zenith angle (degrees)
    vza           : view zenith angle (degrees)
    raa           : relative azimuth angle (degrees)
    altitude_km   : sensor altitude in km (>900 = satellite)
    atmo_model    : atmosphere model (1=US62, 2=MIDSUM, ...)
    aerosol_model : aerosol model (0=none, 1=continental, 2=maritime, 3=urban)
    surface_pressure : surface pressure hPa (0 = use standard atmosphere)
    ozone_du      : ozone column Dobson units (0 = standard atmosphere)
    """
    def __init__(self, wl, aod, h2o,
                 sza=30.0, vza=5.0, raa=90.0,
                 altitude_km=1000.0,
                 atmo_model=1, aerosol_model=1,
                 surface_pressure=0.0, ozone_du=300.0,
                 enable_polar=0):
        self.wl   = np.asarray(wl,  dtype=np.float32)
        self.aod  = np.asarray(aod, dtype=np.float32)
        self.h2o  = np.asarray(h2o, dtype=np.float32)
        self.sza  = float(sza)
        self.vza  = float(vza)
        self.raa  = float(raa)
        self.altitude_km      = float(altitude_km)
        self.atmo_model       = int(atmo_model)
        self.aerosol_model    = int(aerosol_model)
        self.surface_pressure = float(surface_pressure)
        self.ozone_du         = float(ozone_du)
        self.enable_polar     = int(enable_polar)


class LutArrays:
    """Output from compute_lut: numpy arrays shaped [n_aod, n_h2o, n_wl].

    R_atmQ and R_atmU are the Q and U Stokes components of the atmospheric
    path reflectance.  They are None unless enable_polar=1 was set in LutConfig.
    """
    def __init__(self, R_atm, T_down, T_up, s_alb, R_atmQ=None, R_atmU=None):
        self.R_atm  = R_atm
        self.T_down = T_down
        self.T_up   = T_up
        self.s_alb  = s_alb
        self.R_atmQ = R_atmQ
        self.R_atmU = R_atmU


def compute_lut(cfg: LutConfig) -> LutArrays:
    """Compute a full 3-D atmospheric correction LUT via DISCOM.

    Allocates output arrays and calls :c:func:`atcorr_compute_lut` (OpenMP
    parallelised over the AOD grid).

    Parameters
    ----------
    cfg : LutConfig
        LUT grid specification and scene geometry.

    Returns
    -------
    LutArrays
        ``R_atm``, ``T_down``, ``T_up``, ``s_alb`` shaped ``[n_aod, n_h2o, n_wl]``.
        ``R_atmQ`` and ``R_atmU`` are populated when ``cfg.enable_polar=1``,
        ``None`` otherwise.

    Raises
    ------
    RuntimeError
        If the C library returns a non-zero error code.
    """
    n_aod = len(cfg.aod)
    n_h2o = len(cfg.h2o)
    n_wl  = len(cfg.wl)
    n     = n_aod * n_h2o * n_wl

    # Allocate output arrays
    R_atm  = np.zeros(n, dtype=np.float32)
    T_down = np.ones(n,  dtype=np.float32)
    T_up   = np.ones(n,  dtype=np.float32)
    s_alb  = np.zeros(n, dtype=np.float32)

    # Polarization Q/U arrays (only when enable_polar=1)
    enable_polar = getattr(cfg, 'enable_polar', 0)
    R_atmQ = np.zeros(n, dtype=np.float32) if enable_polar else None
    R_atmU = np.zeros(n, dtype=np.float32) if enable_polar else None

    # Build C structs
    c_cfg = _LutConfigC(
        wl               = cfg.wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        n_wl             = n_wl,
        aod              = cfg.aod.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        n_aod            = n_aod,
        h2o              = cfg.h2o.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        n_h2o            = n_h2o,
        sza              = cfg.sza,
        vza              = cfg.vza,
        raa              = cfg.raa,
        altitude_km      = cfg.altitude_km,
        atmo_model       = cfg.atmo_model,
        aerosol_model    = cfg.aerosol_model,
        surface_pressure = cfg.surface_pressure,
        ozone_du         = cfg.ozone_du,
        enable_polar     = enable_polar,
    )
    c_out = _LutArraysC(
        R_atm      = R_atm.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down     = T_down.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_up       = T_up.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        s_alb      = s_alb.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down_dir = None,  # not requested in Python API
        R_atmQ     = R_atmQ.ctypes.data_as(ctypes.POINTER(ctypes.c_float)) if R_atmQ is not None else None,
        R_atmU     = R_atmU.ctypes.data_as(ctypes.POINTER(ctypes.c_float)) if R_atmU is not None else None,
    )

    ret = _lib.atcorr_compute_lut(ctypes.byref(c_cfg), ctypes.byref(c_out))
    if ret != 0:
        raise RuntimeError(f"atcorr_compute_lut failed with code {ret}")

    shape = (n_aod, n_h2o, n_wl)
    return LutArrays(
        R_atm  = R_atm.reshape(shape),
        T_down = T_down.reshape(shape),
        T_up   = T_up.reshape(shape),
        s_alb  = s_alb.reshape(shape),
        R_atmQ = R_atmQ.reshape(shape) if R_atmQ is not None else None,
        R_atmU = R_atmU.reshape(shape) if R_atmU is not None else None,
    )


def lut_slice(cfg: LutConfig, arrays: LutArrays,
              aod_val: float, h2o_val: float) -> LutArrays:
    """Bilinear interpolation of the LUT at a fixed (aod_val, h2o_val).

    Returns a LutArrays object whose four arrays are 1-D [n_wl] spectral
    curves at the requested atmospheric state.  Useful for pre-computing
    scene-average correction parameters before pixel-level inversion.
    """
    n_wl = len(cfg.wl)
    Rs   = np.zeros(n_wl, dtype=np.float32)
    Tds  = np.zeros(n_wl, dtype=np.float32)
    Tus  = np.zeros(n_wl, dtype=np.float32)
    ss   = np.zeros(n_wl, dtype=np.float32)

    n_aod = len(cfg.aod)
    n_h2o = len(cfg.h2o)
    n     = n_aod * n_h2o * n_wl

    # Flatten LutArrays to 1-D for the C call
    Ra  = arrays.R_atm.ravel().astype(np.float32)
    Td  = arrays.T_down.ravel().astype(np.float32)
    Tu  = arrays.T_up.ravel().astype(np.float32)
    sa  = arrays.s_alb.ravel().astype(np.float32)
    assert len(Ra) == n

    c_cfg = _LutConfigC(
        wl=cfg.wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_wl=n_wl,
        aod=cfg.aod.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_aod=n_aod,
        h2o=cfg.h2o.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_h2o=n_h2o,
        sza=cfg.sza, vza=cfg.vza, raa=cfg.raa,
        altitude_km=cfg.altitude_km,
        atmo_model=cfg.atmo_model, aerosol_model=cfg.aerosol_model,
        surface_pressure=cfg.surface_pressure, ozone_du=cfg.ozone_du,
    )
    c_arr = _LutArraysC(
        R_atm     =Ra.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down    =Td.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_up      =Tu.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        s_alb     =sa.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down_dir=None,
    )
    _lib.atcorr_lut_slice(
        ctypes.byref(c_cfg), ctypes.byref(c_arr),
        ctypes.c_float(aod_val), ctypes.c_float(h2o_val),
        Rs.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        Tds.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        Tus.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ss.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        None,  # Tdds: not requested
    )
    return LutArrays(Rs, Tds, Tus, ss)


def invert(rho_toa, R_atm, T_down, T_up, s_alb):
    """Lambertian BOA reflectance inversion (Python/NumPy implementation).

    Equivalent to :c:func:`atcorr_invert` but operates on NumPy arrays.
    All inputs must be broadcastable to a common shape.

    Parameters
    ----------
    rho_toa : array-like
        TOA reflectance.
    R_atm : array-like
        Atmospheric path reflectance (LUT value).
    T_down : array-like
        Downward transmittance.
    T_up : array-like
        Upward transmittance.
    s_alb : array-like
        Spherical albedo.

    Returns
    -------
    numpy.ndarray
        Surface (BOA) reflectance.
    """
    y = (rho_toa - R_atm) / (T_down * T_up + 1e-10)
    return y / (1.0 + s_alb * y + 1e-10)


# ── SRF correction API ────────────────────────────────────────────────────────

class _SrfConfigC(ctypes.Structure):
    _fields_ = [
        ("fwhm_um",      ctypes.POINTER(ctypes.c_float)),
        ("threshold_um", ctypes.c_float),
    ]


_lib.atcorr_srf_compute.argtypes = [
    ctypes.POINTER(_SrfConfigC),
    ctypes.POINTER(_LutConfigC),
]
_lib.atcorr_srf_compute.restype = ctypes.c_void_p   # opaque SrfCorrection*

_lib.atcorr_srf_apply.argtypes = [
    ctypes.c_void_p,                    # SrfCorrection*
    ctypes.POINTER(_LutConfigC),
    ctypes.POINTER(_LutArraysC),
]
_lib.atcorr_srf_apply.restype = None

_lib.atcorr_srf_free.argtypes = [ctypes.c_void_p]
_lib.atcorr_srf_free.restype  = None


def apply_srf_correction(cfg: LutConfig, arrays: LutArrays,
                          fwhm_um, threshold_nm: float = 5.0) -> LutArrays:
    """Apply per-band Gaussian SRF gas-transmittance correction.

    Replaces the coarse 6SV gas parameterisation (10 cm⁻¹) with libRadtran
    reptran fine (~0.05 nm) convolved with a Gaussian SRF for bands where
    FWHM < threshold_nm.  T_down and T_up are modified in the arrays.

    Parameters
    ----------
    cfg           : LutConfig used to compute `arrays`.
    arrays        : LutArrays to correct in place (T_down, T_up modified).
    fwhm_um       : per-band FWHM in µm, 1-D array aligned with cfg.wl.
                    Pass None or zeros to correct all bands (delta-SRF).
    threshold_nm  : only correct bands with FWHM < threshold_nm (default 5).

    Returns
    -------
    arrays : same LutArrays with corrected T_down, T_up (modified in place).

    Notes
    -----
    Requires libRadtran (uvspec) in PATH or $LIBRADTRAN_DIR/bin.
    libRadtran data directory must be accessible via $LIBRADTRAN_DATA or the
    standard installation path /usr/local/share/libRadtran/data.
    """
    n_wl  = len(cfg.wl)
    n_aod = len(cfg.aod)
    n_h2o = len(cfg.h2o)
    n     = n_aod * n_h2o * n_wl

    fwhm_arr = (np.asarray(fwhm_um, dtype=np.float32)
                if fwhm_um is not None
                else np.zeros(n_wl, dtype=np.float32))
    if len(fwhm_arr) != n_wl:
        raise ValueError(f"fwhm_um length {len(fwhm_arr)} != n_wl {n_wl}")

    c_srf_cfg = _SrfConfigC(
        fwhm_um      = fwhm_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        threshold_um = float(threshold_nm) * 1e-3,   # nm → µm
    )
    c_cfg = _LutConfigC(
        wl=cfg.wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_wl=n_wl,
        aod=cfg.aod.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_aod=n_aod,
        h2o=cfg.h2o.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_h2o=n_h2o,
        sza=cfg.sza, vza=cfg.vza, raa=cfg.raa,
        altitude_km=cfg.altitude_km,
        atmo_model=cfg.atmo_model, aerosol_model=cfg.aerosol_model,
        surface_pressure=cfg.surface_pressure, ozone_du=cfg.ozone_du,
    )

    # Flatten LutArrays to 1-D C arrays
    Td = np.ascontiguousarray(arrays.T_down.ravel(), dtype=np.float32)
    Tu = np.ascontiguousarray(arrays.T_up.ravel(),   dtype=np.float32)
    Ra = np.ascontiguousarray(arrays.R_atm.ravel(),  dtype=np.float32)
    sa = np.ascontiguousarray(arrays.s_alb.ravel(),  dtype=np.float32)
    assert len(Td) == n

    c_arr = _LutArraysC(
        R_atm      =Ra.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down     =Td.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_up       =Tu.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        s_alb      =sa.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down_dir =None,
    )

    srf = _lib.atcorr_srf_compute(ctypes.byref(c_srf_cfg), ctypes.byref(c_cfg))
    if not srf:
        raise RuntimeError(
            "atcorr_srf_compute returned NULL — "
            "is uvspec installed? Check LIBRADTRAN_DIR / LIBRADTRAN_DATA."
        )

    _lib.atcorr_srf_apply(srf, ctypes.byref(c_cfg), ctypes.byref(c_arr))
    _lib.atcorr_srf_free(srf)

    shape = (n_aod, n_h2o, n_wl)
    return LutArrays(
        R_atm  = Ra.reshape(shape),
        T_down = Td.reshape(shape),
        T_up   = Tu.reshape(shape),
        s_alb  = sa.reshape(shape),
    )


# ── Retrieval functions ───────────────────────────────────────────────────────

# Function signatures for new retrieval functions
_lib.retrieve_pressure_o2a.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_740
    ctypes.POINTER(ctypes.c_float),  # L_760
    ctypes.POINTER(ctypes.c_float),  # L_780
    ctypes.c_int,                    # npix
    ctypes.c_float,                  # sza_deg
    ctypes.c_float,                  # vza_deg
    ctypes.POINTER(ctypes.c_float),  # out_pressure
]
_lib.retrieve_pressure_o2a.restype = None

_lib.retrieve_quality_mask.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_blue
    ctypes.POINTER(ctypes.c_float),  # L_red
    ctypes.POINTER(ctypes.c_float),  # L_nir
    ctypes.POINTER(ctypes.c_float),  # L_swir (may be NULL)
    ctypes.c_int,                    # npix
    ctypes.c_int,                    # doy
    ctypes.c_float,                  # sza_deg
    ctypes.POINTER(ctypes.c_uint8),  # out_mask
]
_lib.retrieve_quality_mask.restype = None

_lib.retrieve_aod_maiac.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # aod_data (in-place)
    ctypes.c_int,                    # nrows
    ctypes.c_int,                    # ncols
    ctypes.c_int,                    # patch_sz
]
_lib.retrieve_aod_maiac.restype = None

_lib.oe_invert_aod_h2o.argtypes = [
    ctypes.POINTER(_LutConfigC),     # cfg
    ctypes.POINTER(_LutArraysC),     # lut
    ctypes.POINTER(ctypes.c_float),  # rho_toa_vis [npix × n_vis]
    ctypes.c_int,                    # npix
    ctypes.c_int,                    # n_vis
    ctypes.POINTER(ctypes.c_float),  # vis_wl [n_vis]
    ctypes.POINTER(ctypes.c_float),  # L_865 (or NULL)
    ctypes.POINTER(ctypes.c_float),  # L_940 (or NULL)
    ctypes.POINTER(ctypes.c_float),  # L_1040 (or NULL)
    ctypes.c_float,                  # sza_deg
    ctypes.c_float,                  # vza_deg
    ctypes.c_float,                  # aod_prior
    ctypes.c_float,                  # h2o_prior
    ctypes.c_float,                  # sigma_aod
    ctypes.c_float,                  # sigma_h2o
    ctypes.c_float,                  # sigma_spec
    ctypes.c_float,                  # fwhm_940_um
    ctypes.POINTER(ctypes.c_float),  # out_aod
    ctypes.POINTER(ctypes.c_float),  # out_h2o
]
_lib.oe_invert_aod_h2o.restype = None

# ── Basic retrieval function signatures ───────────────────────────────────────
_lib.retrieve_pressure_isa.argtypes = [ctypes.c_float]
_lib.retrieve_pressure_isa.restype  = ctypes.c_float

_lib.retrieve_h2o_940.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_865
    ctypes.POINTER(ctypes.c_float),  # L_940
    ctypes.POINTER(ctypes.c_float),  # L_1040
    ctypes.c_float,                  # fwhm_um  (0 = broadband default)
    ctypes.c_int,                    # npix
    ctypes.c_float,                  # sza_deg
    ctypes.c_float,                  # vza_deg
    ctypes.POINTER(ctypes.c_float),  # out_wvc
]
_lib.retrieve_h2o_940.restype = None

_lib.retrieve_o3_chappuis.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_540
    ctypes.POINTER(ctypes.c_float),  # L_600
    ctypes.POINTER(ctypes.c_float),  # L_680
    ctypes.c_int,                    # npix
    ctypes.c_float,                  # sza_deg
    ctypes.c_float,                  # vza_deg
]
_lib.retrieve_o3_chappuis.restype = ctypes.c_float

_lib.retrieve_aod_ddv.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_470
    ctypes.POINTER(ctypes.c_float),  # L_660
    ctypes.POINTER(ctypes.c_float),  # L_860
    ctypes.POINTER(ctypes.c_float),  # L_2130
    ctypes.c_int,                    # npix
    ctypes.c_int,                    # doy
    ctypes.c_float,                  # sza_deg
    ctypes.POINTER(ctypes.c_float),  # out_aod
]
_lib.retrieve_aod_ddv.restype = ctypes.c_float

_lib.retrieve_h2o_triplet.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # L_lo
    ctypes.POINTER(ctypes.c_float),  # L_feat
    ctypes.POINTER(ctypes.c_float),  # L_hi
    ctypes.c_float,                  # wl_lo_um
    ctypes.c_float,                  # wl_feat_um
    ctypes.c_float,                  # wl_hi_um
    ctypes.c_float,                  # K_ref
    ctypes.c_float,                  # fwhm_ref_um
    ctypes.c_float,                  # fwhm_um (0 = use K_ref)
    ctypes.c_float,                  # D_min
    ctypes.c_float,                  # D_max
    ctypes.c_int,                    # npix
    ctypes.c_float,                  # sza_deg
    ctypes.c_float,                  # vza_deg
    ctypes.POINTER(ctypes.c_float),  # out_wvc
    ctypes.POINTER(ctypes.c_uint8),  # out_valid (may be NULL)
]
_lib.retrieve_h2o_triplet.restype = None

_lib.retrieve_h2o_consensus.argtypes = [
    ctypes.c_int,                                        # n_methods
    ctypes.POINTER(ctypes.POINTER(ctypes.c_float)),     # wvc_arrays
    ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),     # valid_arrays
    ctypes.c_int,                                        # npix
    ctypes.POINTER(ctypes.c_float),                      # out_wvc
]
_lib.retrieve_h2o_consensus.restype = ctypes.c_int


def retrieve_pressure_isa(elev_m):
    """Surface pressure [hPa] from elevation (m) using ISA barometric formula.

    Valid range: 0–11 000 m; clamped at boundaries.
    """
    return float(_lib.retrieve_pressure_isa(ctypes.c_float(float(elev_m))))


def retrieve_h2o_940(L_865, L_940, L_1040, sza_deg, vza_deg, fwhm_um=0.0):
    """Per-pixel water vapour column [g/cm²] from 940 nm band depth.

    Parameters
    ----------
    L_865, L_940, L_1040 : 1-D float32 arrays [npix]
        TOA radiance at ~865, 940, 1040 nm.
    sza_deg, vza_deg : float
    fwhm_um : float, optional
        FWHM of the 940 nm band in µm.  Triggers FWHM-dependent K₉₄₀ scaling:
        K = 0.036 × (50 nm / FWHM_nm)^0.60.  Default 0 uses K=0.036 (MODIS).

    Returns
    -------
    wvc : float32 array [npix]  in g/cm² ∈ [0.1, 8.0]
    """
    L_865  = np.ascontiguousarray(L_865,  dtype=np.float32)
    L_940  = np.ascontiguousarray(L_940,  dtype=np.float32)
    L_1040 = np.ascontiguousarray(L_1040, dtype=np.float32)
    npix   = len(L_865)
    out    = np.empty(npix, dtype=np.float32)
    _lib.retrieve_h2o_940(
        L_865.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_940.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_1040.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.c_float(float(fwhm_um)),
        npix, float(sza_deg), float(vza_deg),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    return out


def retrieve_h2o_triplet(L_lo, L_feat, L_hi,
                          wl_lo_um, wl_feat_um, wl_hi_um,
                          K_ref, fwhm_ref_um, sza_deg, vza_deg,
                          fwhm_um=0.0, D_min=0.05, D_max=0.90):
    """Per-pixel H₂O [g/cm²] from any (lo, feat, hi) wavelength triplet.

    Parameters
    ----------
    L_lo, L_feat, L_hi : 1-D float32 arrays [npix]
        TOA radiance at the continuum-lo, feature, and continuum-hi bands.
    wl_lo_um, wl_feat_um, wl_hi_um : float
        Band centre wavelengths [µm].
    K_ref : float
        Broadband reference absorption coefficient [cm²/g].
    fwhm_ref_um : float
        FWHM of the reference sensor [µm].
    sza_deg, vza_deg : float
    fwhm_um : float, optional
        Actual sensor FWHM [µm]; 0 = use K_ref directly.
    D_min, D_max : float, optional
        Valid band-depth range; pixels outside are marked invalid.

    Returns
    -------
    wvc : float32 array [npix]  WVC [g/cm²]
    valid : uint8 array [npix]  1=valid, 0=excluded
    """
    L_lo   = np.ascontiguousarray(L_lo,   dtype=np.float32)
    L_feat = np.ascontiguousarray(L_feat, dtype=np.float32)
    L_hi   = np.ascontiguousarray(L_hi,   dtype=np.float32)
    npix   = len(L_lo)
    out_wvc   = np.empty(npix, dtype=np.float32)
    out_valid = np.zeros(npix, dtype=np.uint8)
    _lib.retrieve_h2o_triplet(
        L_lo.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_feat.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_hi.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.c_float(float(wl_lo_um)),
        ctypes.c_float(float(wl_feat_um)),
        ctypes.c_float(float(wl_hi_um)),
        ctypes.c_float(float(K_ref)),
        ctypes.c_float(float(fwhm_ref_um)),
        ctypes.c_float(float(fwhm_um)),
        ctypes.c_float(float(D_min)),
        ctypes.c_float(float(D_max)),
        ctypes.c_int(npix),
        ctypes.c_float(float(sza_deg)),
        ctypes.c_float(float(vza_deg)),
        out_wvc.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        out_valid.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    return out_wvc, out_valid


def retrieve_h2o_consensus(wvc_list, valid_list, npix):
    """Per-pixel median consensus across multiple H₂O retrieval estimates.

    Parameters
    ----------
    wvc_list : list of float32 arrays [npix]
        WVC estimates from each method.
    valid_list : list of uint8 arrays [npix]
        Validity flags from each method (1=valid).
    npix : int

    Returns
    -------
    out_wvc : float32 array [npix]  consensus WVC [g/cm²]
    n_agreed : int  number of pixels where ≥2 estimates agreed
    """
    n_methods = len(wvc_list)
    wvc_list   = [np.ascontiguousarray(w, dtype=np.float32)  for w in wvc_list]
    valid_list = [np.ascontiguousarray(v, dtype=np.uint8)    for v in valid_list]

    fp_float = ctypes.POINTER(ctypes.c_float)
    fp_uint8 = ctypes.POINTER(ctypes.c_uint8)

    wvc_ptrs   = (fp_float * n_methods)(*[w.ctypes.data_as(fp_float) for w in wvc_list])
    valid_ptrs = (fp_uint8 * n_methods)(*[v.ctypes.data_as(fp_uint8) for v in valid_list])

    out_wvc = np.empty(npix, dtype=np.float32)
    n_agreed = _lib.retrieve_h2o_consensus(
        ctypes.c_int(n_methods),
        wvc_ptrs,
        valid_ptrs,
        ctypes.c_int(npix),
        out_wvc.ctypes.data_as(fp_float),
    )
    return out_wvc, int(n_agreed)


def retrieve_o3_chappuis(L_540, L_600, L_680, sza_deg, vza_deg):
    """Scene-mean O₃ column [DU] from Chappuis band depth at 600 nm.

    Returns scene mean in [50, 800] DU; fallback 300 DU if no signal.
    """
    L_540 = np.ascontiguousarray(L_540, dtype=np.float32)
    L_600 = np.ascontiguousarray(L_600, dtype=np.float32)
    L_680 = np.ascontiguousarray(L_680, dtype=np.float32)
    npix  = len(L_540)
    return float(_lib.retrieve_o3_chappuis(
        L_540.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_600.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_680.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        npix, float(sza_deg), float(vza_deg),
    ))


def retrieve_aod_ddv(L_470, L_660, L_860, L_2130, doy, sza_deg):
    """Scene-mean AOD@550nm and per-pixel AOD from MODIS DDV method.

    Parameters
    ----------
    L_470, L_660, L_860, L_2130 : 1-D float32 arrays [npix]
    doy : int  Day of year.
    sza_deg : float

    Returns
    -------
    scene_mean : float  Scene-mean AOD at 550 nm (0.15 if no DDV pixels).
    aod_px     : float32 array [npix]
    """
    L_470  = np.ascontiguousarray(L_470,  dtype=np.float32)
    L_660  = np.ascontiguousarray(L_660,  dtype=np.float32)
    L_860  = np.ascontiguousarray(L_860,  dtype=np.float32)
    L_2130 = np.ascontiguousarray(L_2130, dtype=np.float32)
    npix   = len(L_470)
    out    = np.empty(npix, dtype=np.float32)
    scene_mean = float(_lib.retrieve_aod_ddv(
        L_470.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_660.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_860.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_2130.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        npix, int(doy), float(sza_deg),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    ))
    return scene_mean, out


# Bitmask constants
MASK_CLOUD  = 0x01
MASK_SHADOW = 0x02
MASK_WATER  = 0x04
MASK_SNOW   = 0x08


def retrieve_pressure_o2a(L_740, L_760, L_780, sza_deg, vza_deg):
    """Per-pixel surface pressure from O₂-A band depth at 760 nm.

    Parameters
    ----------
    L_740, L_760, L_780 : 1-D float32 arrays [npix]
        TOA radiance at ~740, 760, 780 nm.
    sza_deg, vza_deg : float
        Solar and view zenith angles.

    Returns
    -------
    pressure : float32 array [npix]  in hPa ∈ [200, 1100]
    """
    L_740 = np.ascontiguousarray(L_740, dtype=np.float32)
    L_760 = np.ascontiguousarray(L_760, dtype=np.float32)
    L_780 = np.ascontiguousarray(L_780, dtype=np.float32)
    npix  = len(L_740)
    out   = np.empty(npix, dtype=np.float32)
    _lib.retrieve_pressure_o2a(
        L_740.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_760.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_780.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        npix, float(sza_deg), float(vza_deg),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    return out


def retrieve_quality_mask(L_blue, L_red, L_nir, doy, sza_deg, L_swir=None):
    """Pre-correction quality bitmask (cloud/shadow/water/snow).

    Parameters
    ----------
    L_blue, L_red, L_nir : 1-D float32 arrays [npix]
        TOA radiance at ~470, 660, 860 nm.
    doy : int
        Day of year.
    sza_deg : float
        Solar zenith angle.
    L_swir : 1-D float32 array [npix] or None
        TOA radiance at ~1600 nm (for NDSI/snow test).

    Returns
    -------
    mask : uint8 array [npix]
        Bitmask: MASK_CLOUD=0x01, MASK_SHADOW=0x02, MASK_WATER=0x04, MASK_SNOW=0x08
    """
    L_blue = np.ascontiguousarray(L_blue, dtype=np.float32)
    L_red  = np.ascontiguousarray(L_red,  dtype=np.float32)
    L_nir  = np.ascontiguousarray(L_nir,  dtype=np.float32)
    npix   = len(L_blue)
    out    = np.zeros(npix, dtype=np.uint8)

    swir_ptr = None
    if L_swir is not None:
        L_swir  = np.ascontiguousarray(L_swir, dtype=np.float32)
        swir_ptr = L_swir.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

    _lib.retrieve_quality_mask(
        L_blue.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_red.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        L_nir.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        swir_ptr,
        npix, int(doy), float(sza_deg),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
    )
    return out


def retrieve_aod_maiac(aod_data, nrows, ncols, patch_sz=32):
    """MAIAC-inspired patch AOD spatial regularization (in-place).

    Parameters
    ----------
    aod_data : float32 array [nrows × ncols]
        Per-pixel AOD from retrieve_aod_ddv(); modified in place.
    nrows, ncols : int
    patch_sz : int
        Patch size in pixels (default 32).
    """
    aod_flat = np.ascontiguousarray(aod_data.ravel(), dtype=np.float32)
    _lib.retrieve_aod_maiac(
        aod_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        int(nrows), int(ncols), int(patch_sz),
    )
    aod_data[:] = aod_flat.reshape(aod_data.shape)


def oe_invert_aod_h2o(cfg, lut_arrays, rho_toa_vis, vis_wl,
                       sza_deg, vza_deg,
                       aod_prior, h2o_prior,
                       sigma_aod=0.5, sigma_h2o=1.0, sigma_spec=0.01,
                       fwhm_940_um=0.0,
                       L_865=None, L_940=None, L_1040=None):
    """Joint per-pixel AOD + H₂O MAP retrieval via grid-search OE.

    Parameters
    ----------
    cfg : LutConfig
    lut_arrays : LutArrays
    rho_toa_vis : float32 array [npix, n_vis]
        TOA reflectance at aerosol-diagnostic bands.
    vis_wl : float32 array [n_vis]
        Wavelengths of VIS diagnostic bands (µm).
    sza_deg, vza_deg : float
    aod_prior, h2o_prior : float
        Scene-mean prior state.
    sigma_aod, sigma_h2o, sigma_spec : float
        Prior and observation uncertainties.
    L_865, L_940, L_1040 : float32 array [npix] or None
        H₂O constraint bands (NIR radiance).

    Returns
    -------
    aod_px : float32 array [npix]
    h2o_px : float32 array [npix]
    """
    rho_vis = np.ascontiguousarray(rho_toa_vis, dtype=np.float32)
    npix    = rho_vis.shape[0]
    n_vis   = rho_vis.shape[1]
    vis_wl_ = np.ascontiguousarray(vis_wl, dtype=np.float32)

    n_wl  = len(cfg.wl)
    n_aod = len(cfg.aod)
    n_h2o = len(cfg.h2o)
    n     = n_aod * n_h2o * n_wl

    c_cfg = _LutConfigC(
        wl=cfg.wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_wl=n_wl,
        aod=cfg.aod.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_aod=n_aod,
        h2o=cfg.h2o.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), n_h2o=n_h2o,
        sza=cfg.sza, vza=cfg.vza, raa=cfg.raa,
        altitude_km=cfg.altitude_km,
        atmo_model=cfg.atmo_model, aerosol_model=cfg.aerosol_model,
        surface_pressure=cfg.surface_pressure, ozone_du=cfg.ozone_du,
    )

    Ra = np.ascontiguousarray(lut_arrays.R_atm.ravel(), dtype=np.float32)
    Td = np.ascontiguousarray(lut_arrays.T_down.ravel(), dtype=np.float32)
    Tu = np.ascontiguousarray(lut_arrays.T_up.ravel(),   dtype=np.float32)
    sa = np.ascontiguousarray(lut_arrays.s_alb.ravel(),  dtype=np.float32)
    c_arr = _LutArraysC(
        R_atm  =Ra.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down =Td.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_up   =Tu.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        s_alb  =sa.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        T_down_dir=None,
    )

    def _fptr(arr):
        if arr is None: return None
        a = np.ascontiguousarray(arr, dtype=np.float32)
        return a.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), a

    p865,  _k865  = _fptr(L_865)  if L_865  is not None else (None, None)
    p940,  _k940  = _fptr(L_940)  if L_940  is not None else (None, None)
    p1040, _k1040 = _fptr(L_1040) if L_1040 is not None else (None, None)

    out_aod = np.empty(npix, dtype=np.float32)
    out_h2o = np.empty(npix, dtype=np.float32)

    _lib.oe_invert_aod_h2o(
        ctypes.byref(c_cfg), ctypes.byref(c_arr),
        rho_vis.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        npix, n_vis,
        vis_wl_.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        p865, p940, p1040,
        float(sza_deg), float(vza_deg),
        float(aod_prior), float(h2o_prior),
        float(sigma_aod), float(sigma_h2o), float(sigma_spec),
        float(fwhm_940_um),
        out_aod.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        out_h2o.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    return out_aod, out_h2o


# ── FlexBRDF: Tikhonov smoother + MCD43 disaggregation ───────────────────────

_lib.spectral_smooth_tikhonov.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # f (in-place)
    ctypes.c_int,                    # n
    ctypes.c_float,                  # alpha
]
_lib.spectral_smooth_tikhonov.restype = None

_lib.mcd43_disaggregate.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # fiso_7[7]
    ctypes.POINTER(ctypes.c_float),  # fvol_7[7]
    ctypes.POINTER(ctypes.c_float),  # fgeo_7[7]
    ctypes.POINTER(ctypes.c_float),  # wl_target[n_wl]
    ctypes.c_int,                    # n_wl
    ctypes.c_float,                  # alpha
    ctypes.POINTER(ctypes.c_float),  # fiso_wl[n_wl] (out)
    ctypes.POINTER(ctypes.c_float),  # fvol_wl[n_wl] (out)
    ctypes.POINTER(ctypes.c_float),  # fgeo_wl[n_wl] (out)
]
_lib.mcd43_disaggregate.restype = None

_lib.retrieve_dasf.argtypes = [
    ctypes.POINTER(ctypes.c_float),  # refl [n_dasf × npix], band-major
    ctypes.POINTER(ctypes.c_float),  # wl_dasf [n_dasf]
    ctypes.c_int,                    # n_dasf
    ctypes.c_int,                    # npix
    ctypes.POINTER(ctypes.c_float),  # out_dasf [npix]
]
_lib.retrieve_dasf.restype = None


def spectral_smooth_tikhonov(f, alpha: float):
    """Tikhonov second-difference spectral smoother (in-place copy).

    Solves ``(I + α²·D₂ᵀD₂)·x = f`` via O(5n) Cholesky band factorization.

    Parameters
    ----------
    f : array-like, shape (n,)
        Spectral signal to smooth (e.g. disaggregated kernel weights).
        A copy is made; the original is not modified.
    alpha : float
        Regularization strength.  0 = no smoothing; 0.05–0.20 typical for MCD43.

    Returns
    -------
    numpy.ndarray, shape (n,), float32
        Smoothed spectrum.
    """
    arr = np.ascontiguousarray(f, dtype=np.float32).copy()
    n   = len(arr)
    _lib.spectral_smooth_tikhonov(
        arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.c_int(n),
        ctypes.c_float(float(alpha)),
    )
    return arr


def mcd43_disaggregate(fiso_7, fvol_7, fgeo_7, wl_target, alpha: float = 0.10):
    """Disaggregate 7-band MCD43 kernel weights to a hyperspectral wavelength grid.

    Piecewise-linear interpolation between the 7 MODIS MCD43 band centres
    ({0.469, 0.555, 0.645, 0.858, 1.240, 1.640, 2.130} µm) followed by
    optional Tikhonov second-difference spectral smoothing.

    Parameters
    ----------
    fiso_7 : array-like, shape (7,)
        f_iso kernel weights at MODIS band centres (scale factor 0.001 applied).
    fvol_7 : array-like, shape (7,)
        f_vol kernel weights.
    fgeo_7 : array-like, shape (7,)
        f_geo kernel weights.
    wl_target : array-like, shape (n_wl,)
        Target wavelengths in µm (e.g. sensor centre wavelengths).
    alpha : float, optional
        Tikhonov regularization strength (default 0.10; 0 = off).

    Returns
    -------
    fiso_wl, fvol_wl, fgeo_wl : numpy.ndarray, shape (n_wl,), float32
        Disaggregated kernel weight spectra at each target wavelength.

    Examples
    --------
    >>> import numpy as np
    >>> from atcorr import mcd43_disaggregate
    >>> wl = np.linspace(0.40, 2.50, 421, dtype=np.float32)
    >>> fiso_7 = [0.112, 0.117, 0.095, 0.243, 0.155, 0.118, 0.085]
    >>> fvol_7 = [0.045, 0.040, 0.038, 0.131, 0.038, 0.022, 0.014]
    >>> fgeo_7 = [0.017, 0.014, 0.012, 0.052, 0.016, 0.009, 0.006]
    >>> fiso, fvol, fgeo = mcd43_disaggregate(fiso_7, fvol_7, fgeo_7, wl, alpha=0.10)
    >>> fiso.shape
    (421,)
    """
    fi7 = np.ascontiguousarray(fiso_7, dtype=np.float32)
    fv7 = np.ascontiguousarray(fvol_7, dtype=np.float32)
    fg7 = np.ascontiguousarray(fgeo_7, dtype=np.float32)
    wl  = np.ascontiguousarray(wl_target, dtype=np.float32)
    n_wl = len(wl)

    fiso_wl = np.empty(n_wl, dtype=np.float32)
    fvol_wl = np.empty(n_wl, dtype=np.float32)
    fgeo_wl = np.empty(n_wl, dtype=np.float32)

    _lib.mcd43_disaggregate(
        fi7.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        fv7.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        fg7.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.c_int(n_wl),
        ctypes.c_float(float(alpha)),
        fiso_wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        fvol_wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        fgeo_wl.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    return fiso_wl, fvol_wl, fgeo_wl


def retrieve_dasf(refl, wl_dasf):
    """Per-pixel DASF from corrected BRF in the 710–790 nm NIR plateau.

    Directional Area Scattering Factor (Knyazikhin et al. 2013 PNAS):
    ρ(λ) ≈ DASF × ω_L(λ)  →  DASF = Σ[ρ·ω_L] / Σ[ω_L²]

    Leaf albedo ω_L(λ) is taken from the internal PROSPECT-D table
    (Féret et al. 2017, Cab=40 µg/cm²) at 5 nm steps 705–795 nm.
    Bands outside this range (leaf_albedo_nir returns -1) are skipped.

    Parameters
    ----------
    refl : array-like, shape (n_dasf, npix) or (npix, n_dasf)
        BOA reflectance at bands within 710–790 nm, **band-major** order:
        refl[b, i] = band b of pixel i.  Use ``refl.T`` if your array is
        pixel-major.
    wl_dasf : array-like, shape (n_dasf,)
        Wavelengths of the supplied bands [µm].

    Returns
    -------
    dasf : float32 array, shape (npix,)
        DASF per pixel ∈ [0.01, 1.0]; NaN if fewer than 3 valid bands
        or NDVI < threshold (NDVI masking is applied in the GRASS module
        only; the standalone function returns NaN only for bad numerics).

    Examples
    --------
    >>> import numpy as np
    >>> from atcorr import retrieve_dasf
    >>> # 5 bands at 710-790 nm, 1000 pixels
    >>> wl = np.array([0.710, 0.730, 0.750, 0.770, 0.790], dtype=np.float32)
    >>> refl = np.full((5, 1000), 0.45, dtype=np.float32)
    >>> dasf = retrieve_dasf(refl, wl)
    >>> 0.01 <= float(np.nanmean(dasf)) <= 1.0
    True
    """
    refl_c  = np.ascontiguousarray(refl,    dtype=np.float32)
    wl_c    = np.ascontiguousarray(wl_dasf, dtype=np.float32)
    n_dasf  = refl_c.shape[0]
    npix    = refl_c.shape[1]
    out     = np.empty(npix, dtype=np.float32)

    _lib.retrieve_dasf(
        refl_c.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        wl_c.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.c_int(n_dasf),
        ctypes.c_int(npix),
        out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    return out
