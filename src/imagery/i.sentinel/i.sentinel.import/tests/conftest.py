"""Fixtures for the i.sentinel.import tests."""

import os
import zipfile
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.tools import Tools

PRODUCT = "S2A_MSIL2A_20190101T140049_N0211_R067_T20HNH_20190101T160000"
GRANULE = "GRANULE/L2A_T20HNH_A000001_20190101T140049"
BAND = "T20HNH_20190101T140049_B04_10m"

MTD_TL = """<?xml version="1.0" encoding="UTF-8"?>
<n1:Level-2A_Tile_ID xmlns:n1="https://psd-14.sentinel2.eo.esa.int/PSD/S2_PDI_Level-2A_Tile_Metadata.xsd">
  <n1:General_Info>
    <TILE_ID>S2A_OPER_MSI_L2A_TL_SGS__20190101T160000_A000001_T20HNH_N02.11</TILE_ID>
    <SENSING_TIME>2019-01-01T14:00:49.024Z</SENSING_TIME>
  </n1:General_Info>
  <n1:Geometric_Info></n1:Geometric_Info>
  <n1:Quality_Indicators_Info></n1:Quality_Indicators_Info>
</n1:Level-2A_Tile_ID>
"""


@pytest.fixture
def sentinel(tmp_path):
    """Fresh UTM project and a directory with a Sentinel-2 zip file.

    The zip file holds a minimal SAFE structure with one band and the tile
    metadata. The band is a GeoTIFF with the .jp2 suffix, which GDAL reads
    based on the file content.
    """
    project = tmp_path / "project"
    gs.create_project(project, crs="EPSG:32620")
    data = tmp_path / "data"
    build = tmp_path / "build"
    data.mkdir()
    granule = build / f"{PRODUCT}.SAFE" / GRANULE
    (granule / "IMG_DATA" / "R10m").mkdir(parents=True)
    (granule / "MTD_TL.xml").write_text(MTD_TL, encoding="utf-8")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=4000030, s=4000000, e=500030, w=500000, res=10)
            tools.r_mapcalc(expression="band = 7")
            tools.r_out_gdal(
                input="band",
                output=granule / "IMG_DATA" / "R10m" / f"{BAND}.jp2",
                format="GTiff",
                type="UInt16",
            )
        with zipfile.ZipFile(data / f"{PRODUCT}.zip", "w") as archive:
            for path in sorted(build.rglob("*")):
                archive.write(path, arcname=path.relative_to(build))
        yield SimpleNamespace(
            env=session.env.copy(),
            data=data,
            safe=data / f"{PRODUCT}.SAFE",
            band=BAND,
        )
