"""Fixtures for the i.landsat.import tests."""

import os
import tarfile
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.tools import Tools

SCENE = "LC08_L2SP_229083_20190101_20200830_02_T1"


@pytest.fixture
def landsat(tmp_path):
    """Fresh UTM project and directories with Landsat-like GeoTIFF files.

    The loose directory holds band files (B4, B5) and an unrelated user
    GeoTIFF. The archive directory holds the same bands packed in a .tar
    archive, as delivered by USGS, next to an unrelated user GeoTIFF.
    """
    project = tmp_path / "project"
    gs.create_project(project, crs="EPSG:32620")
    loose = tmp_path / "loose"
    archive = tmp_path / "archive"
    build = tmp_path / "build"
    for directory in (loose, archive, build):
        directory.mkdir()
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=4000090, s=4000000, e=500090, w=500000, res=30)
            tools.r_mapcalc(expression="band = 7")
            for band in ("B4", "B5"):
                for directory in (loose, build):
                    tools.r_out_gdal(
                        input="band",
                        output=directory / f"{SCENE}_SR_{band}.TIF",
                        format="GTiff",
                        type="Int16",
                    )
            for directory in (loose, archive):
                tools.r_out_gdal(
                    input="band", output=directory / "user_dem.TIF", format="GTiff"
                )
        with tarfile.open(archive / f"{SCENE}.tar", "w") as tar:
            for band in ("B4", "B5"):
                name = f"{SCENE}_SR_{band}.TIF"
                tar.add(build / name, arcname=name)
        yield SimpleNamespace(
            env=session.env.copy(), loose=loose, archive=archive, scene=SCENE
        )
