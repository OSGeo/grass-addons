"""Tests for the v.photo.geometry metadata reader."""

import shutil
from datetime import datetime, timezone

import pytest

import grass.script as gs
from grass.exceptions import ScriptError

requires_exiftool = pytest.mark.skipif(
    shutil.which("exiftool") is None, reason="exiftool not on PATH"
)


def test_get_coords(tool, cap_records):
    lon, lat, alt = tool.get_coords(cap_records[0])
    assert lon == pytest.approx(-82.4319388, abs=1e-6)
    assert lat == pytest.approx(35.5905111, abs=1e-6)
    assert alt == pytest.approx(1661.0)


def test_get_coords_missing_gps(tool):
    assert tool.get_coords({"FileName": "no_gps.jpg"}) is None


def test_parse_datetime_subsecond(tool, cap_records):
    ts = tool.parse_exif_datetime(cap_records[0])
    assert ts.microsecond == 191000
    assert ts.utcoffset() is not None
    assert ts.astimezone(timezone.utc).hour == 23  # 18:32 at -05:00


def test_parse_datetime_plain(tool):
    ts = tool.parse_exif_datetime({"DateTimeOriginal": "2024:10:03 18:32:11"})
    assert ts == datetime(2024, 10, 3, 18, 32, 11)


def test_parse_datetime_missing(tool):
    assert tool.parse_exif_datetime({}) is None


def test_camera_details(tool, cap_records):
    make, model, lens = tool.get_camera_details(cap_records[0])
    assert make == "Canon"
    assert model == "Canon EOS 5DS R"
    assert lens == "EF50mm f/1.4 USM"


def test_camera_details_lens_id_fallback(tool):
    _, _, lens = tool.get_camera_details({"LensID": 198})
    assert lens == "198"  # LensID when LensModel is absent


def test_orientation_absent_defaults(tool, cap_records):
    yaw, pitch, roll = tool.get_orientation(cap_records[0])
    assert yaw is None  # estimated from the GPS track later
    assert pitch == pytest.approx(-90.0)
    assert roll == pytest.approx(0.0)


def test_sensor_size_focal_plane(tool, cap_records):
    width, height, source = tool.compute_sensor_size(cap_records[0])
    # Canon 5DS R: FocalPlane tags imply 36.8 x 24.5 mm (true size 36 x 24)
    assert width == pytest.approx(36.83, abs=0.01)
    assert height == pytest.approx(24.51, abs=0.01)
    assert source == "focal plane resolution"


def test_sensor_size_override(tool, cap_records):
    width, height, source = tool.compute_sensor_size(
        cap_records[0], override=(36.0, 24.0)
    )
    assert (width, height) == (36.0, 24.0)
    assert source == "user"


def test_sensor_size_scale_factor(tool):
    # Full-frame equivalence: scale 1.0 must give a 43.27 mm diagonal
    exif = {"ExifImageWidth": 6000, "ExifImageHeight": 4000, "ScaleFactor35efl": 1.0}
    width, height, source = tool.compute_sensor_size(exif)
    assert (width**2 + height**2) ** 0.5 == pytest.approx(43.26661)
    assert width / height == pytest.approx(1.5)
    assert source == "35 mm scale factor"


def test_sensor_size_unavailable(tool):
    assert tool.compute_sensor_size({"ExifImageWidth": 6000}) is None


def test_camera_serial(tool, cap_records):
    serials = {tool.get_camera_serial(r) for r in cap_records}
    assert serials == {"384055000191", "384055000156"}


def test_camera_serial_model_fallback(tool):
    assert tool.get_camera_serial({"Model": "TestCam"}) == "TestCam"


def _track_image(serial, northing, lat, second):
    return {
        "camera_serial": serial,
        "easting": 0.0,
        "northing": northing,
        "lon": 0.0,
        "lat": lat,
        "timestamp": datetime(2024, 10, 3, 18, 32, second),
        "yaw": None,
    }


def test_headings_dual_camera_rig(tool):
    """Two bodies firing together at identical positions must not corrupt
    each other's heading estimates."""
    images = []
    for serial in ("A", "B"):
        for i in range(3):
            # Northward track: identical GPS positions for both bodies
            images.append(_track_image(serial, i * 20.0, i * 0.0002, i))
    result = tool.compute_headings_from_gps(images)
    for img in result:
        assert img["yaw"] == pytest.approx(0.0, abs=0.5)


def test_headings_keep_recorded_yaw(tool):
    images = [_track_image("A", i * 20.0, i * 0.0002, i) for i in range(3)]
    images[1]["yaw"] = 123.0
    result = tool.compute_headings_from_gps(images)
    assert result[1]["yaw"] == pytest.approx(123.0)


def test_find_exiftool_missing(tool, raise_on_error, monkeypatch):
    monkeypatch.setattr(tool.shutil, "which", lambda name: None)
    with pytest.raises(ScriptError, match="ExifTool"):
        tool.find_exiftool()


@requires_exiftool
def test_read_metadata(tool, photo_dir):
    records = tool.read_metadata(tool.find_exiftool(), str(photo_dir))
    assert len(records) == 3
    names = [r["FileName"] for r in records]
    assert names == sorted(names)
    first = records[0]
    assert first["GPSLatitude"] == pytest.approx(35.590)
    assert first["GPSLongitude"] == pytest.approx(-82.435)
    assert first["FocalLength"] == pytest.approx(50.0)


@requires_exiftool
def test_read_metadata_empty_dir(tool, tmp_path):
    assert tool.read_metadata(tool.find_exiftool(), str(tmp_path)) == []


@requires_exiftool
def test_tool_end_to_end(session, photo_dir):
    gs.run_command(
        "v.photo.geometry",
        input=str(photo_dir),
        elevation="dtm",
        footprint_vector="footprints",
        env=session.env,
    )
    info = gs.vector_info_topo("footprints", env=session.env)
    assert info["points"] == 3
    records = gs.parse_command(
        "v.db.select", map="footprints", format="json", env=session.env
    )["records"]
    assert len(records) == 3
    for record in records:
        # Eastward flight line
        assert record["yaw"] == pytest.approx(90.0, abs=2.0)
        # AGL from constant 700 m ground under 1000 m flight altitude
        assert record["agl_alt"] == pytest.approx(300.0, abs=1.0)
