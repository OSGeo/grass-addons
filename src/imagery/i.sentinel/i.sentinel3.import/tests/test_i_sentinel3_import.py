"""Tests for i.sentinel3.import using a synthetic Sentinel-3 SLSTR L2 LST scene.

The scene is written with netCDF4 into a zip file that mimics the layout of an
ESA product, so no downloaded data is required.
"""

import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from importlib import util as importlib_util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError, ScriptError
from grass.script import array as garray

netCDF4 = pytest.importorskip("netCDF4")
osr = pytest.importorskip("osgeo.osr")
osr.UseExceptions()

SCRIPT = Path(__file__).parent.parent / "i.sentinel3.import.py"

SCENE = (
    "S3B_SL_2_LST____20250309T110154_20250309T110454_20250310T155924"
    "_0179_104_094_1800_ESA_O_NT_004"
)
SIZE = 12
FLAGS = {"c": False, "d": False, "k": False, "r": False}
FILE_ATTRS = {
    "title": "SLSTR Level 2 LST",
    "start_time": "2025-03-09T11:01:54.000000Z",
    "stop_time": "2025-03-09T11:04:54.000000Z",
    "history": "synthetic",
    "resolution": "[ 1000 1000 ]",
    "product_name": SCENE,
    "absolute_orbit_number": np.int32(1),
}


def write_nc(path, variables, **attrs):
    """Write a NetCDF file; variables map a name to (array, variable attributes)."""
    with netCDF4.Dataset(path, "w") as nc:
        nc.setncatts({**FILE_ATTRS, **attrs})
        for name, (data, var_attrs) in variables.items():
            data = np.asarray(data)
            dimensions = []
            for size in data.shape:
                if f"d{size}" not in nc.dimensions:
                    nc.createDimension(f"d{size}", size)
                dimensions.append(f"d{size}")
            var_attrs = dict(var_attrs)
            variable = nc.createVariable(
                name,
                var_attrs.pop("dtype", data.dtype),
                dimensions,
                fill_value=var_attrs.pop("fill_value", None),
            )
            variable.setncatts(var_attrs)
            variable[:] = data


def make_zip(directory, name, nc_files):
    """Zip NetCDF files like an ESA product; nc_files maps file name to variables."""
    directory.mkdir(parents=True, exist_ok=True)
    zip_path = directory / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for file_name, variables in nc_files.items():
            nc_path = directory / file_name
            write_nc(nc_path, variables)
            zip_file.write(nc_path, f"{name}.SEN3/{file_name}")
            nc_path.unlink()
    return zip_path


def make_scene(directory, name=SCENE, x_origin=400000, y_origin=6700000):
    """Create a synthetic LST scene with a 1 km grid aligned to EPSG:25833."""
    rows, cols = np.indices((SIZE, SIZE))
    x = x_origin + 500.0 + 1000.0 * cols
    y = y_origin + 500.0 + 1000.0 * rows

    utm = osr.SpatialReference()
    utm.ImportFromEPSG(25833)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    for srs in (utm, wgs84):
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    points = osr.CoordinateTransformation(utm, wgs84).TransformPoints(
        np.column_stack((x.ravel(), y.ravel())),
    )
    lon, lat = (np.array(points)[:, axis].reshape(x.shape) for axis in (0, 1))

    lst = (280.0 + 0.5 * rows + 0.25 * cols).astype("float32")
    exception = np.zeros(x.shape, dtype="uint8")
    exception[3, 3] = 3
    cloud = ((rows * SIZE + cols) % 8).astype("uint16")
    ndvi = (0.01 * cols).astype("float32")
    elevation = 100.0 + 10.0 * rows + cols
    fill = {"fill_value": np.float32(-32768.0)}

    zip_path = make_zip(
        directory,
        name,
        {
            "geodetic_in.nc": {
                "latitude_in": (lat, {}),
                "longitude_in": (lon, {}),
                "elevation_in": (
                    elevation,
                    {
                        "units": "m",
                        "dtype": "int16",
                        "scale_factor": 1.0,
                        "add_offset": 0.0,
                        "valid_min": np.int16(-450),
                        "valid_max": np.int16(9000),
                        "fill_value": np.int16(-32768),
                    },
                ),
            },
            "LST_in.nc": {
                "LST": (
                    lst,
                    {
                        "units": "K",
                        "dtype": "int16",
                        "scale_factor": 0.01,
                        "add_offset": 290.0,
                        "valid_min": np.int16(-15000),
                        "valid_max": np.int16(15000),
                        "fill_value": np.int16(-32768),
                    },
                ),
                "LST_uncertainty": (
                    np.full(x.shape, 0.5, dtype="float32"),
                    {"units": "K", **fill},
                ),
                "exception": (exception, {}),
            },
            "flags_in.nc": {
                "cloud_in": (
                    cloud,
                    {
                        "flag_masks": np.array([1, 2, 4], dtype="uint16"),
                        "flag_meanings": "visible threshold_1.37 threshold_1.6",
                    },
                ),
            },
            "LST_ancillary_ds.nc": {"NDVI": (ndvi, {"units": "1"})},
        },
    )
    return SimpleNamespace(
        zip=zip_path,
        name=name,
        root=Path(f"{name}.SEN3"),
        region={
            "w": x_origin,
            "e": x_origin + 1000 * SIZE,
            "s": y_origin,
            "n": y_origin + 1000 * SIZE,
            "res": 1000,
        },
        lst=lst,
        cloud=cloud,
        ndvi=ndvi,
        elevation=elevation,
    )


def set_region(**kwargs):
    gs.run_command("g.region", **kwargs)


def read_array(name):
    """Read a raster map south-up to match the arrays used to create the scene."""
    return np.array(garray.array(mapname=name, null=np.nan))[::-1]


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    project = tmp_path_factory.mktemp("s3_project") / "project"
    gs.create_project(project, epsg="25833")
    with gs.setup.init(project):
        gs.set_raise_on_error(True)
        yield
        gs.set_raise_on_error(False)


@pytest.fixture(scope="module")
def s3(session):
    """The script loaded as a module, with the dependencies it imports lazily."""
    spec = importlib_util.spec_from_file_location("i_sentinel3_import", SCRIPT)
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.np = np
    module.osr = osr
    module.Dataset = netCDF4.Dataset
    module.TMP_FILE.mkdir(parents=True, exist_ok=True)
    return module


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    return make_scene(tmp_path_factory.mktemp("scene"))


@pytest.fixture
def scene_region(session, scene):
    set_region(**scene.region)


@pytest.fixture(scope="module")
def tool(session, tmp_path_factory):
    """Install the script like g.extension does, so that g.parser can run it."""
    installed = tmp_path_factory.mktemp("addon") / "i.sentinel3.import"
    lines = SCRIPT.read_text(encoding="utf-8").splitlines(keepends=True)
    installed.write_text(f"#!{sys.executable}\n" + "".join(lines[1:]), encoding="utf-8")
    installed.chmod(0o755)
    return str(installed)


# Pure helpers


def test_np_as_scalar(s3):
    assert s3.np_as_scalar(np.float32(1.5)) == pytest.approx(1.5)
    assert isinstance(s3.np_as_scalar(np.int16(3)), int)
    assert s3.np_as_scalar(np.array([5])) == 5
    assert s3.np_as_scalar(np.array([1, 2])) == "[1 2]"
    assert s3.np_as_scalar("abc") == "abc"


@pytest.mark.parametrize(
    ("dtype", "expected"),
    [
        ("bool", {"min": 0, "max": 1, "resolution": 1}),
        ("uint8", {"min": 0, "max": 255, "resolution": 1}),
        ("int16", {"min": -32768, "max": 32767, "resolution": 1}),
    ],
)
def test_get_dtype_range_integer(s3, dtype, expected):
    assert s3.get_dtype_range(dtype) == expected


def test_get_dtype_range_float(s3):
    info = np.finfo("float32")
    assert s3.get_dtype_range("float32") == {
        "min": info.min,
        "max": info.max,
        "resolution": 2.0 * info.resolution,
    }


def test_get_dtype_range_unsupported(s3):
    with pytest.raises(ScriptError):
        s3.get_dtype_range("complex64")


def test_consolidate_metadata_dicts(s3):
    result = s3.consolidate_metadata_dicts(
        [
            {"map": {"title": "a", "orbit": "1"}},
            {"map": {"title": "a", "orbit": "2"}},
            {"map": {"title": "a", "orbit": "3"}, "other": {"x": 1}},
            {"map": {"orbit": "2"}},
        ],
    )
    assert result["map"] == {"title": "a", "orbit": ["1", "2", "3"]}
    assert result["other"] == {"x": 1}


def test_extend_region(s3):
    region = {"n": 10, "s": 0, "e": 10, "w": 0}
    result = s3.extend_region(region, {"n": 12, "s": 2, "e": 8, "w": -1})
    assert result == {"n": 12, "s": 0, "e": 10, "w": -1}


def test_adjust_region(s3):
    region = {"n": 1234.0, "s": -50.0, "e": 2500.0, "w": 100.0}
    region.update(nsres=1000.0, ewres=1000.0)
    result = s3.adjust_region(region)
    assert (result["n"], result["s"], result["e"], result["w"]) == (
        2000,
        -1000,
        3000,
        -1000,
    )


CURRENT = {
    "n": 10000,
    "s": 0,
    "e": 10000,
    "w": 0,
    "nsres": 1000,
    "ewres": 1000,
    "rows": 10,
}
STRIPE = {"n": 8500, "s": 2500, "e": 12000, "w": -500, "nsres": 500, "ewres": 500}


def test_intersect_region_aligned_to_current(s3):
    assert s3.intersect_region(CURRENT, STRIPE) == {
        "n": 10000,
        "s": 1000,
        "e": 11000,
        "w": -1000,
        "nsres": 1000,
        "ewres": 1000,
    }


def test_intersect_region_aligned_to_stripe(s3):
    assert s3.intersect_region(CURRENT, STRIPE, align_current=False) == {
        "n": 9000,
        "s": 2000,
        "e": 10500,
        "w": -500,
        "nsres": 500,
        "ewres": 500,
    }


def test_intersect_region_keeps_pixel_grid_of_current_region(s3):
    current = {**CURRENT, "n": 10250, "s": 250, "e": 10250, "w": 250}
    stripe = {
        "n": 20000,
        "s": -5000,
        "e": 20000,
        "w": -5000,
        "nsres": 500,
        "ewres": 500,
    }
    result = s3.intersect_region(current, stripe)
    for key in "nsew":
        assert (result[key] - 250) % 1000 == 0
    assert result["s"] < 250 < 10250 < result["n"]


def test_check_region_validity(s3):
    s3.check_region_validity("an", {"n": 2, "s": 1, "e": 2, "w": 1})
    with pytest.raises(SystemExit):
        s3.check_region_validity("an", {"n": 1, "s": 1, "e": 2, "w": 1})


def test_get_grass_metadata(s3):
    assert s3._get_grass_metadata({"a": ["x", "y"]}, "a") == "x,y"
    assert s3._get_grass_metadata({"a": "x"}, "a") == "x"
    assert s3._get_grass_metadata({}, "a") is None


# File names


def test_parse_s3_file_name(s3):
    assert s3.parse_s3_file_name(f"{SCENE}.zip") == {
        "mission_id": "S3B",
        "instrument": "SL",
        "level": "2",
        "product": "LST",
        "start_time": datetime(2025, 3, 9, 11, 1, 54),
        "end_time": datetime(2025, 3, 9, 11, 4, 54),
        "ingestion_time": datetime(2025, 3, 10, 15, 59, 24),
        "duration": "0179",
        "cycle": "104",
        "relative_orbit": "094",
        "frame": "1800",
        "producer": "ESA",
        "product_class": "O",
        "timeliness": "NT",
        "baseline_collection": "004",
    }


def test_parse_s3_file_name_invalid(s3):
    with pytest.raises(ScriptError):
        s3.parse_s3_file_name(SCENE.replace("20250309T110154", "2025030Tabcdef"))


def test_extract_file_info_single_scene(s3, capfd):
    basename, info = s3.extract_file_info([Path(f"{SCENE}.zip")])
    assert basename == (
        "S3B_SL_2_LST_20250309110154_20250309110454_104_094_ESA_O_NT_004"
    )
    assert info["end_time"] == datetime(2025, 3, 9, 11, 4, 54)
    assert not capfd.readouterr().err


def test_extract_file_info_custom_basename(s3):
    basename, _info = s3.extract_file_info([Path(f"{SCENE}.zip")], basename="mine")
    assert basename == "mine"


def test_extract_file_info_merges_scenes(s3, capfd):
    other = SCENE.replace("S3B", "S3A").replace("_104_", "_103_")
    other = other.replace(
        "20250309T110154_20250309T110454", "20250309T105854_20250309T110154"
    )
    basename, info = s3.extract_file_info([Path(f"{SCENE}.zip"), Path(f"{other}.zip")])
    assert info["start_time"] == datetime(2025, 3, 9, 10, 58, 54)
    assert info["end_time"] == datetime(2025, 3, 9, 11, 4, 54)
    assert basename.startswith("S3__SL_2_LST_20250309105854_20250309110454_")
    assert "_103_094_" in basename
    err = capfd.readouterr().err
    assert "cycle" in err
    assert "Sentinel-3A and Sentinel-3B" in err


def test_extract_file_info_rejects_different_relative_orbits(s3):
    other = SCENE.replace("_094_", "_093_")
    with pytest.raises(ScriptError, match="relative orbits"):
        s3.extract_file_info([Path(f"{SCENE}.zip"), Path(f"{other}.zip")])


@pytest.mark.parametrize("baseline", ["003", "004", "005"])
def test_extract_file_info_tested_baseline_is_silent(s3, capfd, baseline):
    scene = SCENE.replace("NT_004", f"NT_{baseline}")
    s3.extract_file_info([Path(f"{scene}.zip")])
    assert not capfd.readouterr().err


def test_extract_file_info_warns_for_untested_baseline(s3, capfd):
    scene = SCENE.replace("NT_004", "NT_006")
    s3.extract_file_info([Path(f"{scene}.zip")])
    assert "baseline 006 has not been tested" in capfd.readouterr().err


def test_extract_file_info_warns_for_missing_baseline(s3, capfd):
    scene = SCENE.replace("_NT_004", "_NT")
    s3.extract_file_info([Path(f"{scene}.zip")])
    assert "Could not determine the processing baseline" in capfd.readouterr().err


# S3Band and S3Product


def test_s3band_lst(s3):
    band = s3.S3Band("S3SL2LST", "LST")
    assert band.band_type == "bands"
    assert band.suffix == "in"
    assert band.full_name == "LST"
    assert band.nc_file == "LST_in.nc"
    assert band.exception == "exception"
    assert band.resolution == pytest.approx(1000.0)
    assert band.radiance_adjustment is None
    assert band.solar_flux is None


def test_s3band_radiance(s3):
    band = s3.S3Band("S3SL1RBT", "S1")
    assert band.suffix == "an"
    assert band.full_name == "S1_radiance_an"
    assert band.nc_file == "S1_radiance_an.nc"
    assert band.exception == "S1_exception_an"
    assert band.resolution == pytest.approx(500.0)
    assert band.radiance_adjustment == pytest.approx(0.97)
    assert band.solar_flux == {
        "default": 1837.39,
        "band": "S1_solar_irradiance_an",
        "nc_file": "S1_quality_an.nc",
    }
    assert band.adjust_radiance(np.array([100.0])) == pytest.approx([97.0])


def test_s3band_oblique_view(s3):
    band = s3.S3Band("S3SL1RBT", "S1", view="o")
    assert band.suffix == "ao"
    assert band.radiance_adjustment == pytest.approx(0.94)


def test_s3band_brightness_temperature_is_not_adjusted(s3):
    band = s3.S3Band("S3SL1RBT", "F1")
    assert band.full_name == "F1_BT_fn"
    values = np.array([300.0])
    assert band.adjust_radiance(values) is values


def test_s3band_flag_and_ancillary(s3):
    flag = s3.S3Band("S3SL2LST", "cloud")
    assert (flag.band_type, flag.full_name, flag.nc_file) == (
        "flags",
        "cloud_in",
        "flags_in.nc",
    )
    assert flag.exception is None
    ancillary = s3.S3Band("S3SL2LST", "NDVI")
    assert ancillary.band_type == "ancillary"
    assert (ancillary.full_name, ancillary.nc_file) == ("NDVI", "LST_ancillary_ds.nc")


@pytest.mark.parametrize("product_type", ["S3SL2LST", "S3SL1RBT"])
def test_s3band_unknown_band(s3, product_type):
    with pytest.raises(ScriptError, match="not available"):
        s3.S3Band(product_type, "nope")


@pytest.mark.parametrize(
    ("product_type", "suffix"), [("S3SL2LST", "in"), ("S3SL1RBT", "an")]
)
def test_s3band_elevation(s3, product_type, suffix):
    band = s3.S3Band(product_type, "elevation")
    assert band.band_type == "ancillary"
    assert band.full_name == f"elevation_{suffix}"
    assert band.nc_file == f"geodetic_{suffix}.nc"


def test_s3product_map_names(s3):
    product = s3.S3Product("S3SL1RBT", bands="S1,S7", flag_bands="cloud")
    assert product.get_map_names("b") == [
        "b_S1_radiance_an",
        "b_S7_BT_in",
        "b_cloud_an",
    ]
    assert product.get_map_names("b", reflectance=True) == [
        "b_S1_reflectance_an",
        "b_S7_BT_in",
        "b_cloud_an",
    ]


def test_s3product_stripe_content(s3):
    product = s3.S3Product(
        "S3SL2LST",
        bands=["LST", "LST_uncertainty"],
        flag_bands=["cloud", "bayes"],
        ancillary_bands=["NDVI"],
    )
    assert product.requested_stripe_content == {
        "in": {
            "containers": {
                "LST_in.nc": ["LST", "LST_uncertainty"],
                "flags_in.nc": ["cloud", "bayes"],
                "LST_ancillary_ds.nc": ["NDVI"],
            },
            "geocoding": {
                "nc_file": "geodetic_in.nc",
                "bands": {
                    "lat": "latitude_in",
                    "lon": "longitude_in",
                    "elevation": "elevation_in",
                },
            },
        },
    }


def test_s3product_band_stripes(s3):
    product = s3.S3Product("S3SL1RBT", bands="S1,S7", flag_bands="cloud")
    assert product.get_band_stripes() == {
        "S1_radiance_an": "an",
        "S7_BT_in": "in",
        "cloud_an": "an",
    }
    assert set(product.get_band_stripes().values()) <= set(
        product.requested_stripe_content
    )


def test_s3product_accepts_comma_separated_strings(s3):
    product = s3.S3Product("S3SL2LST", bands="LST,LST_uncertainty", flag_bands="")
    assert list(product.bands) == ["LST", "LST_uncertainty"]
    assert product.flag_bands is None


def test_s3product_all_bands(s3):
    product = s3.S3Product("S3SL2LST", bands="all", flag_bands="all")
    assert list(product.bands) == ["LST", "LST_uncertainty"]
    assert "cloud" in product.flag_bands


LST_ANCILLARY = [
    "biome",
    "fraction",
    "NDVI",
    "TCWV",
    "LST_uncertainty_locATM",
    "LST_uncertainty_locGEO",
    "LST_uncertainty_locSF",
    "LST_uncertainty_locT",
    "LST_uncertainty_random",
    "LST_uncertainty_sys",
]


def test_s3product_elevation_is_only_added_with_flag(s3):
    product = s3.S3Product("S3SL2LST", bands="LST", ancillary_bands="all")
    assert list(product.ancillary_bands) == LST_ANCILLARY
    product = s3.S3Product("S3SL2LST", bands="LST", elevation=True)
    assert list(product.ancillary_bands) == ["elevation"]
    product = s3.S3Product(
        "S3SL2LST", bands="LST", ancillary_bands="NDVI", elevation=True
    )
    assert list(product.ancillary_bands) == ["NDVI", "elevation"]
    product = s3.S3Product(
        "S3SL2LST", bands="LST", ancillary_bands="all", elevation=True
    )
    assert list(product.ancillary_bands) == [
        *LST_ANCILLARY,
        "elevation",
    ]
    product = s3.S3Product("S3SL1RBT", bands="S7", ancillary_bands="all")
    assert not product.ancillary_bands
    product = s3.S3Product("S3SL1RBT", bands="S7", elevation=True)
    assert list(product.ancillary_bands) == ["elevation"]


@pytest.mark.parametrize(
    ("product_type", "band"), [("S3SL2LST", "LST"), ("S3SL1RBT", "S7")]
)
def test_s3product_rejects_elevation_as_ancillary_band(s3, product_type, band):
    with pytest.raises(ScriptError, match="elevation is not available"):
        s3.S3Product(product_type, bands=band, ancillary_bands="elevation")


def test_s3product_unknown_band(s3):
    with pytest.raises(ScriptError, match="not available"):
        s3.S3Product("S3SL2LST", bands="LST,nope")


def test_s3product_unavailable_view(s3):
    with pytest.raises(ScriptError, match="not available"):
        s3.S3Product("S3SL2LST", view="o", bands="LST")


def test_s3product_view_is_passed_to_bands(s3):
    product = s3.S3Product("S3SL1RBT", view="o", bands="S1")
    assert product.bands["S1"].suffix == "ao"
    assert "ao" in product.requested_stripe_content


@pytest.mark.filterwarnings("ignore:Mean of empty slice")
def test_get_solar_flux(s3, tmp_path):
    band = s3.S3Band("S3SL1RBT", "S1")
    nan = np.array([np.nan, np.nan], dtype="float32")
    measured = np.array([1800.0, 1900.0], dtype="float32")
    for name, values, expected in (
        ("measured", measured, 1850.0),
        ("nan", nan, 1837.39),
    ):
        zip_path = make_zip(
            tmp_path / name,
            name,
            {"S1_quality_an.nc": {"S1_solar_irradiance_an": (values, {})}},
        )
        with zipfile.ZipFile(zip_path) as zip_file:
            assert band.get_solar_flux(zip_file, Path(f"{name}.SEN3")) == pytest.approx(
                expected,
            )


# NetCDF handling


def open_variable(path, data, **attrs):
    write_nc(path, {"v": (data, attrs)})
    return netCDF4.Dataset(path)


FILE_METADATA = {
    "start_time": datetime(2025, 3, 9, 11, 1, 54),
    "end_time": datetime(2025, 3, 9, 11, 4, 54),
}


def band_metadata(s3, variable, name="LST", fmt="%.12f", **kwargs):
    return s3.get_band_metadata(
        (name, name),
        variable,
        fmt,
        file_metadata=FILE_METADATA,
        basename="base",
        **kwargs,
    )


@pytest.mark.parametrize(
    "time_string",
    ["2025-03-09T11:01:54.123456Z", "2025-03-09T11:01:54.123456+00:00"],
)
def test_parse_timestr(s3, time_string):
    assert s3.parse_timestr(time_string) == datetime(
        2025, 3, 9, 11, 1, 54, 123456, tzinfo=timezone.utc
    )


def test_get_file_metadata(s3, tmp_path):
    write_nc(tmp_path / "a.nc", {}, history=" a \n", unrelated="ignored")
    with netCDF4.Dataset(tmp_path / "a.nc") as dataset:
        metadata = s3.get_file_metadata(dataset)
    assert metadata["history"] == "a"
    assert metadata["title"] == "SLSTR Level 2 LST"
    assert metadata["absolute_orbit_number"] == 1
    assert metadata["start_time"] == datetime(
        2025, 3, 9, 11, 1, 54, tzinfo=timezone.utc
    )
    assert metadata["end_time"] == datetime(2025, 3, 9, 11, 4, 54, tzinfo=timezone.utc)
    assert "unrelated" not in metadata


def test_get_file_metadata_without_history(s3, tmp_path):
    write_nc(tmp_path / "a.nc", {})
    with netCDF4.Dataset(tmp_path / "a.nc", "a") as dataset:
        dataset.delncattr("history")
        assert "history" not in s3.get_file_metadata(dataset)


def test_get_band_metadata_float_with_fill_value(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc",
        np.zeros((2, 2), dtype="float32"),
        units="K",
        fill_value=np.float32(-32768.0),
    ) as dataset:
        metadata, fmt = band_metadata(s3, dataset["v"])
    assert fmt == "%.12f,%.12f"
    assert metadata["datatype"] == "FCELL"
    assert metadata["method"] == "mean"
    assert metadata["mapname"] == "base_LST"
    assert metadata["unit"] == "K"
    assert metadata["semantic_label"] == "S3_LST"
    first_valid = np.nextafter(np.float32(-32768.0), np.float32(np.inf))
    assert metadata["zrange"] == [first_valid, np.finfo("float32").max]
    assert metadata["fill_value"] == np.float32(-32768.0)
    assert metadata["start_time"] == "2025-03-09T11:01:54"
    # The metadata of the file is not modified
    assert FILE_METADATA["start_time"] == datetime(2025, 3, 9, 11, 1, 54)


def test_get_band_metadata_celsius(s3, tmp_path):
    pytest.importorskip("cf_units")
    with open_variable(
        tmp_path / "a.nc",
        np.zeros(2, dtype="float32"),
        units="K",
        valid_min=np.float32(200.0),
        valid_max=np.float32(350.0),
        fill_value=np.float32(-32768.0),
    ) as dataset:
        variable = dataset["v"]
        metadata = band_metadata(s3, variable, to_celsius=True)[0]
        assert metadata["unit"] == "degree_celsius"
        assert metadata["zrange"] == pytest.approx([200.0 - 273.15, 350.0 - 273.15])
        assert metadata["fill_value"] == pytest.approx(-32768.0 - 273.15)
        assert metadata["fill_value"] < metadata["zrange"][0]
        # A difference has the same value in kelvin and degree celsius
        metadata = band_metadata(s3, variable, name="LST_uncertainty", to_celsius=True)[
            0
        ]
        assert metadata["unit"] == "degree_celsius"
        assert metadata["zrange"] == [200.0, 350.0]
        assert metadata["fill_value"] == np.float32(-32768.0)
        # Other bands are not affected
        metadata = band_metadata(s3, variable, name="S1", to_celsius=True)[0]
        assert metadata["unit"] == "K"
        assert metadata["zrange"] == [200.0, 350.0]


def test_get_band_metadata_unsigned_integer(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc", np.zeros(2, dtype="uint8"), fill_value=np.uint8(255)
    ) as dataset:
        metadata, fmt = band_metadata(s3, dataset["v"], name="cloud_in")
    assert fmt == "%.12f,%i"
    assert metadata["datatype"] == "CELL"
    assert metadata["method"] == "max"
    assert metadata["zrange"] == [0, 254]


def test_get_band_metadata_unsigned_integer_without_fill_value(s3, tmp_path):
    # 0 is a valid value (e.g. biome "ocean"), the default fill value is 255
    with open_variable(tmp_path / "a.nc", np.zeros(2, dtype="uint8")) as dataset:
        metadata = band_metadata(s3, dataset["v"], name="biome")[0]
    assert metadata["zrange"] == [0, 254]
    assert metadata["fill_value"] == 255


def test_get_band_metadata_signed_integer_counter(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc",
        np.zeros(2, dtype="int8"),
        fill_value=np.int8(-1),
        valid_min=np.int8(0),
        valid_max=np.int8(7),
    ) as dataset:
        metadata, fmt = band_metadata(s3, dataset["v"], name="counter_water_in")
    assert fmt == "%.12f,%i"
    assert metadata["datatype"] == "CELL"
    assert metadata["zrange"] == [0, 7]


def test_get_band_metadata_valid_range(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc",
        np.zeros(2, dtype="float32"),
        valid_min=np.float32(0.0),
        valid_max=np.float32(100.0),
        fill_value=np.float32(-999.0),
    ) as dataset:
        assert band_metadata(s3, dataset["v"])[0]["zrange"] == [0.0, 100.0]


def test_get_band_metadata_without_fill_value(s3, tmp_path):
    with open_variable(tmp_path / "a.nc", np.zeros(2, dtype="float32")) as dataset:
        metadata = band_metadata(s3, dataset["v"])[0]
    assert metadata["fill_value"] == np.finfo("float32").min
    assert metadata["fill_value"] < metadata["zrange"][0]


@pytest.mark.parametrize(
    ("scale_factor", "offset", "packed_min", "packed_max"),
    [(0.01, 290.0, -2000, 2000), (-0.01, 300.0, -1000, 3000)],
)
def test_get_band_metadata_unpacks_valid_range_and_fill_value(
    s3, tmp_path, scale_factor, offset, packed_min, packed_max
):
    # Both parametrizations unpack to the range 270 to 310 (swapped for negative scales)
    with open_variable(
        tmp_path / "a.nc",
        np.full(2, 290.0),
        dtype="int16",
        scale_factor=scale_factor,
        add_offset=offset,
        valid_min=np.int16(packed_min),
        valid_max=np.int16(packed_max),
        fill_value=np.int16(-32768),
    ) as dataset:
        metadata = band_metadata(s3, dataset["v"])[0]
    assert metadata["datatype"] == "FCELL"
    assert metadata["zrange"] == pytest.approx([270.0, 310.0])
    assert metadata["fill_value"] == pytest.approx(-32768 * scale_factor + offset)
    assert not metadata["zrange"][0] <= metadata["fill_value"] <= metadata["zrange"][1]


def test_get_band_metadata_scaled_fill_value_only(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc",
        np.full(2, 290.0),
        dtype="int16",
        scale_factor=0.01,
        add_offset=290.0,
        fill_value=np.int16(-32768),
    ) as dataset:
        metadata = band_metadata(s3, dataset["v"])[0]
    fill = -32768 * 0.01 + 290.0
    assert metadata["fill_value"] == pytest.approx(fill)
    assert metadata["zrange"][0] == pytest.approx(fill, abs=1e-3)
    assert metadata["zrange"][0] > fill


def test_get_band_metadata_flag_masks_cover_all_combinations(s3, tmp_path):
    with open_variable(
        tmp_path / "a.nc",
        np.zeros(2, dtype="uint16"),
        flag_masks=np.array([1, 2, 4], dtype="uint16"),
    ) as dataset:
        metadata = band_metadata(s3, dataset["v"], name="cloud_in")[0]
    assert metadata["zrange"] == [0, 7]
    # The fill value is not a valid flag combination
    assert metadata["fill_value"] == 65535


def test_get_band_metadata_unsupported_datatype(s3, tmp_path):
    with open_variable(tmp_path / "a.nc", np.zeros(2, dtype="int64")) as dataset:
        with pytest.raises(ScriptError, match="Unsupported datatype"):
            band_metadata(s3, dataset["v"])


# Geocoding and ASCII export


GEOCODING = {
    "nc_file": "geodetic_in.nc",
    "bands": {"lat": "latitude_in", "lon": "longitude_in"},
}


def test_get_geocoding_without_region(s3, scene):
    with zipfile.ZipFile(scene.zip) as zip_file:
        nc_bands, mask, resolution, rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING
        )
    assert list(nc_bands) == ["lat", "lon"]
    assert not np.any(mask)
    assert resolution == ["1000", "1000"]
    assert rows == slice(None)
    assert 59 < nc_bands["lat"].min() < nc_bands["lat"].max() < 62


def test_get_geocoding_masks_pixels_outside_region(s3, scene, scene_region):
    bounds = gs.parse_command("g.region", flags="ugb")
    with zipfile.ZipFile(scene.zip) as zip_file:
        _bands, mask, _res, _rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING, region_bounds=bounds
        )
        assert not mask.all()
        # Shrink the region to the first half of the columns
        half = {**scene.region, "e": scene.region["w"] + 6000}
        set_region(**half)
        bounds = gs.parse_command("g.region", flags="ugb")
        _bands, half_mask, _res, _rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING, region_bounds=bounds
        )
    assert half_mask.sum() > mask.sum()
    assert not half_mask.all()


def test_get_geocoding_reads_only_rows_inside_region(s3, scene):
    set_region(**{**scene.region, "n": scene.region["s"] + 3000})
    bounds = gs.parse_command("g.region", flags="ugb")
    with zipfile.ZipFile(scene.zip) as zip_file:
        nc_bands, mask, _res, rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING, region_bounds=bounds
        )
        _bands, full_mask, _res, no_rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING, region_bounds=bounds, window=False
        )
    assert no_rows == slice(None)
    assert rows.stop - rows.start < SIZE
    assert nc_bands["lat"].shape == (rows.stop - rows.start, SIZE)
    # Windowing does not change which pixels are used
    assert mask.sum() == full_mask.sum() - full_mask[: rows.start].size - (
        full_mask[rows.stop :].size
    )


@pytest.mark.parametrize("chunk_size", [1, 5, 1000])
def test_get_row_window(s3, scene, chunk_size):
    set_region(**scene.region)
    bounds = gs.parse_command("g.region", flags="ugb")
    with zipfile.ZipFile(scene.zip) as zip_file:
        geodetic = zip_file.extract(
            (scene.root / "geodetic_in.nc").as_posix(), path=scene.zip.parent
        )
    with netCDF4.Dataset(geodetic) as dataset:
        lat, lon = dataset["latitude_in"], dataset["longitude_in"]
        assert s3.get_row_window(lat, lon, bounds, chunk_size) == slice(0, SIZE)
        far = {**bounds, "ll_s": "10", "ll_n": "11"}
        assert s3.get_row_window(lat, lon, far, chunk_size) is None


def test_get_geocoding_applies_sun_mask(s3, scene):
    sun_mask = np.zeros((SIZE, SIZE), dtype=bool)
    sun_mask[2, 4] = True
    with zipfile.ZipFile(scene.zip) as zip_file:
        _bands, mask, _res, _rows = s3.get_geocoding(
            zip_file, scene.root, GEOCODING, sun_mask=sun_mask
        )
    assert np.argwhere(mask).tolist() == [[2, 4]]


def test_get_geocoding_region_without_valid_pixels(s3, scene, capfd):
    far_away = make_scene(scene.zip.parent / "far", x_origin=800000, y_origin=7000000)
    set_region(**scene.region)
    bounds = gs.parse_command("g.region", flags="ugb")
    with zipfile.ZipFile(far_away.zip) as zip_file:
        result = s3.get_geocoding(zip_file, scene.root, GEOCODING, region_bounds=bounds)
    assert result == (None, None, None, None)
    assert "No valid pixels" in capfd.readouterr().err


def test_get_geocoding_missing_band(s3, scene, tmp_path):
    zip_path = make_zip(
        tmp_path,
        "broken",
        {"geodetic_in.nc": {"latitude_in": (np.zeros((2, 2)), {})}},
    )
    with zipfile.ZipFile(zip_path) as zip_file:
        with pytest.raises(ScriptError, match="longitude_in"):
            s3.get_geocoding(zip_file, Path("broken.SEN3"), GEOCODING)


def test_write_xyz(s3, tmp_path):
    nc_bands = {
        "lon": np.ma.masked_array([[1.0, 2.0], [3.0, 4.0]]),
        "lat": np.ma.masked_array([[5.0, 6.0], [7.0, 8.0]]),
        "val": np.ma.masked_array([[10, 20], [30, 40]], mask=[[0, 0], [0, 1]]),
    }
    mask = np.array([[False, True], [False, False]])
    output = tmp_path / "xyz.txt"

    bounds = s3.write_xyz(output, nc_bands, mask, fmt="%.1f,%.1f,%i", project=False)

    # Masked pixels are dropped, no-data values are filled
    assert output.read_text().splitlines() == [
        "1.0,5.0,10",
        "3.0,7.0,30",
        "4.0,8.0,999999",
    ]
    assert bounds == {"n": 8.0, "s": 5.0, "e": 4.0, "w": 1.0}

    # Further scenes are appended
    s3.write_xyz(output, nc_bands, mask, fmt="%.1f,%.1f,%i", project=False)
    assert len(output.read_text().splitlines()) == 6


def test_transform_coordinates(s3, session):
    # Input is (lon, lat); lon 15 is the central meridian of UTM zone 33
    result = s3.transform_coordinates(np.array([[15.0, 0.0], [15.0, 60.0]]))
    assert result[0].tolist() == pytest.approx([500000.0, 0.0], abs=1e-3)
    assert result[1, 0] == pytest.approx(500000.0, abs=1e-3)
    assert result[1, 1] == pytest.approx(6652000.0, abs=5000)


def test_transform_coordinates_northing_first_crs(s3, session, tmp_path):
    # EPSG:3006 is defined with northing before easting
    project = tmp_path / "sweref99"
    gs.create_project(project, epsg="3006")
    environment = os.environ.copy()
    try:
        with gs.setup.init(project):
            result = s3.transform_coordinates(np.array([[15.0, 60.0]]))
    finally:
        # Leaving the second session does not restore the first one
        os.environ.clear()
        os.environ.update(environment)
    assert result[0, 0] == pytest.approx(500000.0, abs=1e-3)
    assert result[0, 1] == pytest.approx(6652000.0, abs=5000)


# Import chain


def test_process_nc_file(s3, scene, tmp_path):
    product = s3.S3Product("S3SL2LST", bands="LST")
    nc_bands = {"lat": 0, "lon": 0, "elevation": 0}

    with zipfile.ZipFile(scene.zip) as zip_file:
        nc_bands, module_queue, meta, fmt = product.process_nc_file(
            zip_file,
            scene.root,
            ("LST_in.nc", ["LST"]),
            nc_bands,
            "base",
            {},
            FLAGS,
            tmp_path / "xyz.txt",
            fmt="%.12f,%.12f,%.12f",
        )

    assert fmt == "%.12f,%.12f,%.12f,%.12f"
    # Pixels flagged by the exception band are masked out
    lst = nc_bands["LST"]
    assert lst[0, 0] == scene.lst[0, 0]
    assert lst[3, 3] == pytest.approx(-32768 * 0.01 + 290.0)
    # Import chain is configured for the fourth column (after lat, lon, elevation)
    r_in_xyz, r_fill_stats = module_queue["LST"]
    assert r_in_xyz.name == "r.in.xyz"
    assert r_in_xyz.inputs["z"].value == 4
    assert r_in_xyz.inputs["type"].value == "FCELL"
    assert r_fill_stats.inputs["distance"].value == pytest.approx(2000.0)
    assert r_fill_stats.flags.s
    assert r_fill_stats.flags.m
    assert r_fill_stats.outputs["output"].value == "base_LST"
    assert meta["base_LST"]["semantic_label"] == "S3_LST"
    assert meta["base_LST"]["unit"] == "K"
    assert meta["base_LST"]["variable"] == "LST"
    assert meta["base_LST"]["title"] == "SLSTR Level 2 LST"


def test_process_nc_file_reflectance_unit_and_categories(s3, tmp_path):
    data = np.ones((2, 2), dtype="float32")
    zip_path = make_zip(
        tmp_path,
        "rbt",
        {
            "S1_radiance_an.nc": {
                "S1_radiance_an": (data, {"units": "mW.m-2.sr-1.nm-1"}),
                "S1_exception_an": (np.zeros((2, 2), dtype="uint8"), {}),
            },
            "S1_quality_an.nc": {"S1_solar_irradiance_an": (data * 1800, {})},
            "flags_an.nc": {
                "cloud_an": (
                    np.zeros((2, 2), dtype="uint8"),
                    {"flag_values": np.array([0, 10], dtype="uint8")},
                ),
            },
        },
    )
    product = s3.S3Product("S3SL1RBT", bands="S1", flag_bands="cloud")
    meta = {}
    with zipfile.ZipFile(zip_path) as zip_file:
        for container in (("S1_radiance_an.nc", ["S1"]), ("flags_an.nc", ["cloud"])):
            _bands, queue, info, _fmt = product.process_nc_file(
                zip_file,
                Path("rbt.SEN3"),
                container,
                {"lat": 0, "lon": 0, "elevation": 0},
                "base",
                {},
                {**FLAGS, "r": True},
                tmp_path / "xyz.txt",
                fmt="%.12f,%.12f,%.12f",
            )
            meta.update(info)
    assert meta["base_S1_radiance_an"]["unit"] == "1"
    assert meta["base_S1_radiance_an"]["units"] == "1"


def test_process_nc_file_ancillary_without_flag_bands(s3, scene, tmp_path):
    product = s3.S3Product("S3SL2LST", bands="LST", ancillary_bands="NDVI")

    with zipfile.ZipFile(scene.zip) as zip_file:
        _bands, module_queue, meta, _fmt = product.process_nc_file(
            zip_file,
            scene.root,
            ("LST_ancillary_ds.nc", ["NDVI"]),
            {"lat": 0, "lon": 0, "elevation": 0},
            "base",
            {},
            FLAGS,
            tmp_path / "xyz.txt",
            fmt="%.12f,%.12f,%.12f",
        )

    assert list(module_queue) == ["NDVI"]
    assert "base_NDVI" in meta


@pytest.mark.parametrize(
    ("bands", "message"),
    [("LST", "Band LST is not available"), ("all", None)],
)
def test_process_nc_file_skips_missing_band(s3, tmp_path, capfd, bands, message):
    zip_path = make_zip(tmp_path, "empty", {"LST_in.nc": {"other": (np.zeros(2), {})}})
    product = s3.S3Product("S3SL2LST", bands=bands)

    with zipfile.ZipFile(zip_path) as zip_file:
        _bands, queue, meta, fmt = product.process_nc_file(
            zip_file,
            Path("empty.SEN3"),
            ("LST_in.nc", ["LST"]),
            {},
            "base",
            {},
            FLAGS,
            tmp_path / "xyz.txt",
            fmt="%.12f",
        )
    assert not queue
    assert not meta
    assert fmt == "%.12f"
    err = capfd.readouterr().err
    # Missing bands that were requested with "all" are not reported as warnings
    assert ("WARNING" in err) == bool(message)
    if message:
        assert message in err


def test_process_nc_file_skips_missing_file(s3, tmp_path):
    zip_path = make_zip(tmp_path, "empty", {"LST_in.nc": {"other": (np.zeros(2), {})}})
    product = s3.S3Product("S3SL2LST", bands="LST", flag_bands="cloud")

    with zipfile.ZipFile(zip_path) as zip_file:
        result = product.process_nc_file(
            zip_file,
            Path("empty.SEN3"),
            ("flags_in.nc", ["cloud"]),
            {},
            "base",
            {},
            FLAGS,
            tmp_path / "xyz.txt",
            fmt="%.12f",
        )
    assert result == ({}, {}, {}, "%.12f")


def test_process_nc_file_reads_only_given_rows(s3, scene, tmp_path):
    product = s3.S3Product("S3SL2LST", bands="LST")
    with zipfile.ZipFile(scene.zip) as zip_file:
        nc_bands, *_ = product.process_nc_file(
            zip_file,
            scene.root,
            ("LST_in.nc", ["LST"]),
            {"lat": 0, "lon": 0, "elevation": 0},
            "base",
            {},
            FLAGS,
            tmp_path / "xyz.txt",
            fmt="%.12f,%.12f,%.12f",
            rows=slice(1, 3),
        )
    assert nc_bands["LST"].shape == (2, SIZE)
    assert nc_bands["LST"][0, 0] == scene.lst[1, 0]


def test_s3product_adapt_to_scene_uses_fallback_grid(s3):
    product = s3.S3Product("S3SL1RBT", bands="F1,F2")
    assert product.bands["F1"].full_name == "F1_BT_fn"
    assert "fn" in product.requested_stripe_content

    product.adapt_to_scene({"F1_BT_fn.nc", "F2_BT_in.nc"})
    assert product.bands["F1"].full_name == "F1_BT_fn"

    product.adapt_to_scene({"F1_BT_in.nc", "F2_BT_in.nc"})
    assert product.bands["F1"].full_name == "F1_BT_in"
    assert product.bands["F1"].resolution == pytest.approx(1000.0)
    assert list(product.requested_stripe_content) == ["in"]
    assert product.get_band_stripes() == {"F1_BT_in": "in", "F2_BT_in": "in"}


def test_s3product_baseline_specific_bands(s3):
    product = s3.S3Product(
        "S3SL2LST",
        bands="LST",
        flag_bands="counter_water,pointing",
        ancillary_bands="LST_uncertainty_locATM",
    )
    assert list(product.flag_bands) == ["counter_water", "pointing"]
    assert list(product.ancillary_bands) == ["LST_uncertainty_locATM"]
    assert s3.S3Product("S3SL1RBT", bands="S7", flag_bands="counter_water").flag_bands


@pytest.fixture
def xyz_grid(tmp_path, session):
    """A 10 x 10 km region and one point per cell with a value of 100."""
    set_region(n=10000, s=0, e=10000, w=0, res=1000)
    xyz = tmp_path / "xyz.txt"
    xyz.write_text(
        "\n".join(
            f"{500 + 1000 * col},{500 + 1000 * row},{100 + (row + col) % 2}"
            for row in range(10)
            for col in range(10)
        ),
        encoding="utf-8",
    )
    return xyz


def test_import_chain_with_reflectance(s3, xyz_grid, monkeypatch):
    monkeypatch.setattr(s3, "OVERWRITE", True)
    gs.run_command("r.mapcalc", expression="unit_zenith = 60.0", overwrite=True)
    monkeypatch.setattr(s3, "SUN_ZENITH_ANGLE", "unit_zenith")

    modules = s3.setup_import_multi_module(
        xyz_grid,
        "unit_S1_radiance_an",
        distance=2000.0,
        fill_flags="msk",
        val_col=3,
        data_type="FCELL",
        solar_flux=1000.0,
    )
    for module in modules:
        module.run()

    assert [module.name for module in modules] == [
        "r.in.xyz",
        "r.fill.stats",
        "r.mapcalc",
    ]
    reflectance = read_array("unit_S1_reflectance_an")
    # radiance * pi / solar flux / cos(zenith)
    assert reflectance.min() == pytest.approx(100 * np.pi / 1000 / 0.5, abs=0.01)
    assert reflectance.max() == pytest.approx(101 * np.pi / 1000 / 0.5, abs=0.01)


def test_import_chain_categorical_with_rules(s3, xyz_grid, monkeypatch):
    monkeypatch.setattr(s3, "OVERWRITE", True)
    modules = s3.setup_import_multi_module(
        xyz_grid,
        "unit_flags",
        distance=2000.0,
        fill_flags="mk",
        val_col=3,
        data_type="CELL",
        method="max",
        rules="100:clear\n101:cloud",
    )
    for module in modules:
        module.run()

    assert [module.name for module in modules] == [
        "r.in.xyz",
        "r.fill.stats",
        "r.category",
    ]
    assert set(np.unique(read_array("unit_flags"))) == {100, 101}
    categories = gs.read_command("r.category", map="unit_flags")
    assert "100\tclear" in categories
    assert "101\tcloud" in categories


def test_cleanup_removes_temporary_data(s3, session, tmp_path, monkeypatch):
    if shutil.which("r.external.out") is None:
        pytest.skip("r.external.out is not available")
    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()
    monkeypatch.setattr(s3, "TMP_FILE", tmp_dir)
    monkeypatch.setattr(s3, "TMP_NAME", "tmp_cleanup")
    set_region(n=2, s=0, e=2, w=0, res=1)
    for name in ("tmp_cleanup_a", "keep_cleanup"):
        gs.run_command("r.mapcalc", expression=f"{name} = 1", overwrite=True)

    s3.cleanup()

    assert not tmp_dir.exists()
    maps = gs.list_strings("raster")
    assert "keep_cleanup@PERMANENT" in maps
    assert "tmp_cleanup_a@PERMANENT" not in maps


# The tool as a whole


def run_tool(tool, scene, **kwargs):
    options = {
        "input": str(scene.zip),
        "product_type": "S3SL2LST",
        "bands": "LST,LST_uncertainty",
        "flag_bands": "cloud",
        "ancillary_bands": "NDVI",
        "nprocs": 1,
        "overwrite": True,
        "flags": "k",
        **kwargs,
    }
    gs.run_command(tool, **options)


def test_tool_imports_scene(tool, scene, scene_region, tmp_path):
    register = tmp_path / "register.txt"
    run_tool(tool, scene, basename="lst", flags="ke", register_output=str(register))

    maps = set(gs.list_strings("raster", mapset="."))
    assert {
        "lst_LST@PERMANENT",
        "lst_LST_uncertainty@PERMANENT",
        "lst_cloud_in@PERMANENT",
        "lst_NDVI@PERMANENT",
        "lst_elevation_in@PERMANENT",
    } <= maps
    # No temporary maps are left behind by the tool
    assert not [name for name in maps if name.startswith("tmp_") and "_lst_" in name]

    np.testing.assert_allclose(read_array("lst_LST"), scene.lst, atol=0.05)
    np.testing.assert_allclose(read_array("lst_NDVI"), scene.ndvi, atol=0.01)
    np.testing.assert_allclose(
        read_array("lst_elevation_in"), scene.elevation, atol=0.01
    )
    info = gs.parse_command("r.info", map="lst_elevation_in", format="json")
    assert info["units"] == "m"
    np.testing.assert_array_equal(read_array("lst_cloud_in"), scene.cloud)
    assert 0 in scene.cloud
    assert gs.raster_info("lst_cloud_in")["datatype"] == "CELL"

    categories = gs.read_command("r.category", map="lst_cloud_in")
    assert "1\tvisible" in categories
    assert "2\tthreshold_1.37" in categories

    info = gs.parse_command("r.info", map="lst_LST", format="json")
    assert info["semantic_label"] == "S3_LST"
    assert info["datatype"] == "FCELL"
    assert "2025" in gs.read_command("r.timestamp", map="lst_LST")

    assert sorted(register.read_text().splitlines()) == sorted(
        f"lst_{name}@PERMANENT|2025-03-09 11:01:54|2025-03-09 11:04:54|S3_{label}"
        for name, label in (
            ("LST", "LST"),
            ("LST_uncertainty", "LST_uncertainty"),
            ("cloud_in", "cloud_in"),
            ("NDVI", "NDVI"),
            ("elevation_in", "elevation_in"),
        )
    )


def test_tool_does_not_change_region(tool, scene, scene_region):
    before = gs.region()
    run_tool(tool, scene, basename="region")
    assert gs.region() == before


def test_tool_imports_celsius(tool, scene, scene_region):
    pytest.importorskip("cf_units")
    run_tool(tool, scene, basename="celsius", flags="kc", bands="LST,LST_uncertainty")
    np.testing.assert_allclose(read_array("celsius_LST"), scene.lst - 273.15, atol=0.05)
    info = gs.parse_command("r.info", map="celsius_LST", format="json")
    assert info["units"] == "degree_celsius"
    assert '"units": "K"' not in gs.read_command("r.info", map="celsius_LST", flags="e")
    # The uncertainty is a difference, only its unit changes
    np.testing.assert_allclose(read_array("celsius_LST_uncertainty"), 0.5)
    info = gs.parse_command("r.info", map="celsius_LST_uncertainty", format="json")
    assert info["units"] == "degree_celsius"


def test_tool_rejects_scene_of_other_product_type(tool, scene, scene_region, capfd):
    with pytest.raises(CalledModuleError):
        run_tool(tool, scene, product_type="S3SL1RBT", bands="S7")
    assert (
        "not a supported Sentinel-3 scene for the requested" in capfd.readouterr().err
    )


def test_tool_reads_scene_list_with_empty_lines(tool, scene, scene_region, tmp_path):
    scene_list = tmp_path / "scenes.txt"
    scene_list.write_text(f"\n{scene.zip}\n\n", encoding="utf-8")
    run_tool(tool, scene, basename="listed", input=str(scene_list), bands="LST")
    assert "listed_LST@PERMANENT" in gs.list_strings("raster", mapset=".")


def test_tool_skips_scene_outside_region(tool, scene, session, capfd):
    set_region(n=7100000, s=7090000, e=810000, w=800000, res=1000)
    run_tool(tool, scene, basename="outside", bands="LST")
    assert "outside_LST@PERMANENT" not in gs.list_strings("raster", mapset=".")
    assert "No valid pixels" in capfd.readouterr().err


def test_tool_prints_map_names_without_import(tool, scene, scene_region, tmp_path):
    name = (
        "S3B_SL_1_RBT____20250309T110154_20250309T110454_20250310T155924"
        "_0179_104_094_1800_ESA_O_NT_004.zip"
    )
    rbt_scene = tmp_path / name
    rbt_scene.touch()
    maps_before = gs.list_strings("raster", mapset=".")

    output = gs.read_command(
        tool,
        input=str(rbt_scene),
        product_type="S3SL1RBT",
        bands="S1,S7",
        flag_bands="cloud",
        basename="printed",
        flags="pre",
    )

    assert output.splitlines() == [
        "printed_S1_reflectance_an",
        "printed_S7_BT_in",
        "printed_cloud_an",
        "printed_elevation_an",
        "printed_solar_azimuth",
        "printed_solar_zenith",
    ]
    assert gs.list_strings("raster", mapset=".") == maps_before


@pytest.mark.parametrize(
    "options",
    [
        {"bands": "nope"},
        {"product_type": "invalid"},
        {"ancillary_bands": "elevation"},
        {"flags": "r"},
        {"maximum_solar_angle": 70},
        {"flags": "o"},
        {"input": "/does/not/exist.txt"},
        {"flags": "p", "register_output": "register.txt"},
    ],
)
def test_tool_rejects_invalid_input(tool, scene, scene_region, options):
    with pytest.raises(CalledModuleError):
        run_tool(tool, scene, basename="invalid", **options)
    assert not [
        name
        for name in gs.list_strings("raster", mapset=".")
        if name.startswith("invalid")
    ]
