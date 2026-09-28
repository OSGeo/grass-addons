"""Tests for the EMIT reader of i.hyper.import on small synthetic files.

The files mimic the layout of EMIT L1B radiance (RAD), L1B observation
geometry (OBS) and L2A reflectance NetCDF granules, so no multi-GB download
is needed.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")
pytest.importorskip("pyproj")

import grass.script as gs  # noqa: E402
from grass.exceptions import ScriptError  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "i_hyper_lib"))
import emit  # noqa: E402

SWATH = (20, 16)  # Swath lines, samples.
ORTHO = (24, 22)  # Orthorectified grid rows, cols.
NBANDS = 5
WEST, NORTH, RES = 55.0, 25.0, 0.001


def _write_granule(path, data_key, units=None):
    """Write a synthetic EMIT granule whose GLT maps ortho cells to swath
    pixels along a diagonal band, with fill cells around it, like a real
    rotated flight line."""
    rows, cols = ORTHO
    lines, samples = SWATH
    rr, cc = np.mgrid[0:rows, 0:cols]
    glt_y = rr - 2
    glt_x = cc - rr // 2 - 1
    valid = (glt_y >= 0) & (glt_y < lines) & (glt_x >= 0) & (glt_x < samples)
    rng = np.random.default_rng(42)
    cube = rng.uniform(1, 20, (lines, samples, NBANDS)).astype(np.float32)
    cube[0, 0, :] = -9999.0
    with h5py.File(path, "w") as f:
        f.attrs["geotransform"] = [WEST, RES, 0.0, NORTH, 0.0, -RES]
        f.attrs["time_coverage_start"] = "2024-08-25T06:44:23+0000"
        f.create_dataset("location/glt_y", data=np.where(valid, glt_y + 1, 0))
        f.create_dataset("location/glt_x", data=np.where(valid, glt_x + 1, 0))
        f.create_dataset("location/lat", data=np.full(SWATH, NORTH, np.float64))
        f.create_dataset("location/lon", data=np.full(SWATH, WEST, np.float64))
        wl = np.linspace(400, 2500, NBANDS).astype(np.float32)
        f.create_dataset("sensor_band_parameters/wavelengths", data=wl)
        f.create_dataset("sensor_band_parameters/fwhm", data=np.full(NBANDS, 8.5))
        dset = f.create_dataset(data_key, data=cube)
        dset.attrs["_FillValue"] = np.array([-9999.0], np.float32)
        if units:
            dset.attrs["units"] = np.bytes_(units)
    return path


@pytest.fixture
def raise_on_error():
    gs.set_raise_on_error(True)
    yield
    gs.set_raise_on_error(False)


def _ortho(prod, band):
    return emit._orthorectify_band(
        prod["data"][:, :, band], prod["glt_y"], prod["glt_x"]
    )


def test_crop_matches_full_read(tmp_path):
    """A region-limited read gives the same orthorectified values as a full
    read, from a smaller swath window."""
    path = _write_granule(tmp_path / "EMIT_L1B_RAD_001_x.nc", "radiance")
    box = (WEST + 5 * RES, NORTH - 15 * RES, WEST + 14 * RES, NORTH - 6 * RES)
    full = emit._read_emit_netcdf(str(path))
    crop = emit._read_emit_netcdf(str(path), crop_ll=box)

    # The crop covers the 9x9-cell box, with at most one extra cell per side
    # from floating-point rounding at the box edges.
    rows, cols = crop["ortho_rows"], crop["ortho_cols"]
    assert 9 <= rows <= 11
    assert 9 <= cols <= 11
    assert crop["west"] <= box[0]
    assert crop["east"] >= box[2]
    assert crop["south"] <= box[1]
    assert crop["north"] >= box[3]
    assert crop["data"].shape[0] < full["data"].shape[0]
    r0 = round((full["north"] - crop["north"]) / RES)
    c0 = round((crop["west"] - full["west"]) / RES)
    for band in range(NBANDS):
        expected = _ortho(full, band)[r0 : r0 + rows, c0 : c0 + cols]
        np.testing.assert_array_equal(_ortho(crop, band), expected)


def test_radiance_units_from_file(tmp_path):
    """Radiance units come from the file, not a hard-coded W/m^2/sr/nm."""
    path = _write_granule(
        tmp_path / "EMIT_L1B_RAD_001_x.nc", "radiance", units="uW/cm^2/SR/nm"
    )
    prod = emit._read_emit_netcdf(str(path))
    assert prod["data_key"] == "radiance"
    assert emit._radiometric_units(prod) == "uW/cm^2/SR/nm"


def test_reflectance_units(tmp_path):
    path = _write_granule(tmp_path / "EMIT_L2A_RFL_001_x.nc", "reflectance")
    prod = emit._read_emit_netcdf(str(path))
    assert emit._radiometric_units(prod) == "unitless (reflectance)"
    assert np.isnan(prod["data"][0, 0, 0])  # _FillValue became NULL.


def test_folder_prefers_radiance_over_obs(tmp_path):
    """OBS sorts before RAD in an L1B granule folder; RAD must be picked."""
    _write_granule(tmp_path / "EMIT_L1B_OBS_001_x.nc", "obs")
    rad = _write_granule(tmp_path / "EMIT_L1B_RAD_001_x.nc", "radiance")
    assert emit._resolve_nc(str(tmp_path)) == str(rad)


def test_obs_file_rejected(tmp_path, raise_on_error):
    path = _write_granule(tmp_path / "EMIT_L1B_OBS_001_x.nc", "obs")
    with pytest.raises(ScriptError, match="neither an EMIT L2A reflectance"):
        emit._read_emit_netcdf(str(path))


def test_region_outside_scene_rejected(tmp_path, raise_on_error):
    path = _write_granule(tmp_path / "EMIT_L1B_RAD_001_x.nc", "radiance")
    with pytest.raises(ScriptError, match="does not overlap"):
        emit._read_emit_netcdf(str(path), crop_ll=(10.0, 10.0, 10.1, 10.1))
