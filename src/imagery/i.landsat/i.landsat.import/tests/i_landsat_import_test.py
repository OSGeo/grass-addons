"""Tests for the removal of GeoTIFF files by i.landsat.import."""

import pytest

import grass.script as gs
from grass.tools import Tools


def tif_names(directory):
    return sorted(path.name for path in directory.glob("*.TIF"))


def test_print_flag_keeps_files(landsat):
    """Printing the files to import does not remove them."""
    pytest.importorskip("osgeo")
    before = tif_names(landsat.loose)
    tools = Tools(env=landsat.env)
    tools.i_landsat_import(input=landsat.loose, flags="p")
    assert tif_names(landsat.loose) == before


def test_link_flag_keeps_linked_files(landsat):
    """Files linked with -l stay in place so the linked maps can be read."""
    before = tif_names(landsat.loose)
    tools = Tools(env=landsat.env)
    tools.i_landsat_import(input=landsat.loose, flags="l")
    assert tif_names(landsat.loose) == before
    name = f"{landsat.scene}_SR_B4"
    tools.g_region(raster=name)
    assert tools.r_univar(map=name, format="json")["mean"] == 7


def test_import_keeps_files_not_extracted(landsat):
    """Existing files are kept, also those not matching the pattern."""
    before = tif_names(landsat.loose)
    tools = Tools(env=landsat.env)
    tools.i_landsat_import(input=landsat.loose, pattern="B4")
    assert tif_names(landsat.loose) == before
    rasters = gs.list_strings("raster", mapset=".", env=landsat.env)
    assert f"{landsat.scene}_SR_B4@PERMANENT" in rasters
    assert f"{landsat.scene}_SR_B5@PERMANENT" not in rasters


def test_extracted_files_are_removed(landsat):
    """Files extracted from the archive are removed after import."""
    tools = Tools(env=landsat.env)
    tools.i_landsat_import(input=landsat.archive)
    assert tif_names(landsat.archive) == ["user_dem.TIF"]
    assert (landsat.archive / f"{landsat.scene}.tar").exists()
    name = f"{landsat.scene}_SR_B5"
    tools.g_region(raster=name)
    assert tools.r_univar(map=name, format="json")["mean"] == 7
