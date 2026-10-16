"""Tests for the removal of SAFE directories by i.sentinel.import."""

import zipfile

import pytest

from grass.tools import Tools


def test_print_after_link_keeps_linked_files(sentinel):
    """Printing the files to import keeps the files of linked maps."""
    pytest.importorskip("osgeo")
    tools = Tools(env=sentinel.env)
    tools.i_sentinel_import(input=sentinel.data, flags="l")
    assert sentinel.safe.is_dir()
    tools.i_sentinel_import(input=sentinel.data, flags="p")
    assert sentinel.safe.is_dir()
    tools.g_region(raster=sentinel.band)
    assert tools.r_univar(map=sentinel.band, format="json")["mean"] == 7


def test_existing_safe_is_kept(sentinel):
    """A SAFE directory extracted before the import is not removed."""
    with zipfile.ZipFile(next(sentinel.data.glob("*.zip"))) as archive:
        archive.extractall(sentinel.data)
    tools = Tools(env=sentinel.env)
    tools.i_sentinel_import(input=sentinel.data)
    assert sentinel.safe.is_dir()


def test_extracted_safe_is_removed(sentinel):
    """A SAFE directory extracted by the import is removed afterwards."""
    tools = Tools(env=sentinel.env)
    tools.i_sentinel_import(input=sentinel.data)
    assert not sentinel.safe.exists()
    tools.g_region(raster=sentinel.band)
    assert tools.r_univar(map=sentinel.band, format="json")["mean"] == 7
