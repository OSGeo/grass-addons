import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import grass.script as gs

TOOL_PATH = Path(__file__).parents[1] / "v.photo.geometry.py"
DATA_DIR = Path(__file__).parent / "data"

# Camera positions for synthetic photos: an eastward line at 1 s spacing
SYNTHETIC_PHOTOS = [
    {"lon": -82.435, "lat": 35.590, "time": "2024:10:03 18:32:11"},
    {"lon": -82.434, "lat": 35.590, "time": "2024:10:03 18:32:12"},
    {"lon": -82.433, "lat": 35.590, "time": "2024:10:03 18:32:13"},
]


@pytest.fixture(scope="module")
def tool():
    """The tool imported as a module for unit testing its functions."""
    spec = importlib.util.spec_from_file_location("v_photo_geometry", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cap_records():
    """ExifTool output captured from six CAP frames (Canon 5DS R rig)."""
    return json.loads((DATA_DIR / "cap_frames.json").read_text())


@pytest.fixture
def raise_on_error():
    """Make gs.fatal raise instead of exiting."""
    previous = gs.set_raise_on_error(True)
    yield
    gs.set_raise_on_error(previous)


@pytest.fixture(scope="module")
def photo_dir(tmp_path_factory):
    """Directory of small JPEGs with EXIF stamped by ExifTool."""
    exiftool = shutil.which("exiftool")
    if not exiftool:
        pytest.skip("exiftool not on PATH")
    directory = tmp_path_factory.mktemp("photos")
    for i, photo in enumerate(SYNTHETIC_PHOTOS):
        path = directory / f"img_{i:03d}.jpg"
        shutil.copy(DATA_DIR / "seed.jpg", path)
        subprocess.run(
            [
                exiftool,
                "-n",
                "-overwrite_original",
                "-q",
                f"-GPSLatitude={photo['lat']}",
                "-GPSLatitudeRef=N",
                f"-GPSLongitude={photo['lon']}",
                "-GPSLongitudeRef=W",
                "-GPSAltitude=1000",
                "-GPSAltitudeRef=0",
                f"-DateTimeOriginal={photo['time']}",
                "-Make=Test",
                "-Model=TestCam",
                "-FocalLength=50",
                "-ExifImageWidth=8000",
                "-ExifImageHeight=6000",
                "-ISO=100",
                "-FNumber=5.6",
                "-ExposureTime=0.001",
                "-ShutterSpeedValue=0.001",
                str(path),
            ],
            check=True,
        )
    return directory


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """GRASS session in a metric CRS with a constant elevation raster."""
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6346", always_xy=True)
    east, north = transformer.transform(-82.434, 35.590)

    tmp_path = tmp_path_factory.mktemp("grassdata")
    project = tmp_path / "utm17n"
    gs.create_project(project, epsg="6346")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        gs.run_command(
            "g.region",
            w=east - 2000,
            e=east + 2000,
            s=north - 2000,
            n=north + 2000,
            res=10,
            env=session.env,
        )
        gs.run_command("r.mapcalc", expression="dtm = 700", env=session.env)
        yield session
