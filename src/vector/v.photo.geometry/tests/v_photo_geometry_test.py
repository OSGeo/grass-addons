"""Tests for the v.photo.geometry metadata reader."""

import shutil
from datetime import datetime, timezone

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError, ScriptError

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


def test_orientation_dji_string_tags(tool):
    """DJI XMP writes signed strings; values must come back as floats."""
    exif = {
        "FlightYawDegree": "+90.50",
        "GimbalPitchDegree": "-89.90",
        "GimbalRollDegree": "+0.00",
    }
    yaw, pitch, roll = tool.get_orientation(exif)
    assert yaw == pytest.approx(90.5)
    assert pitch == pytest.approx(-89.9)
    assert roll == pytest.approx(0.0)


def test_orientation_unparseable_yaw_stays_missing(tool):
    yaw, pitch, roll = tool.get_orientation({"FlightYawDegree": "n/a"})
    assert yaw is None
    assert pitch == pytest.approx(-90.0)


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


def test_headings_split_at_time_gap(tool):
    """A long pause splits the track; headings must not bridge the break."""
    images = []
    # Segment 1: northward at seconds 0-2
    for i in range(3):
        images.append(_track_image("A", i * 20.0, i * 0.0002, i))
    # Segment 2: eastward starting 100 s later from a distant start
    for i in range(3):
        img = _track_image("A", 0.0, 0.0, 40 + i)
        img["timestamp"] = datetime(2024, 10, 3, 18, 34, i)
        img["easting"] = 5000.0 + i * 20.0
        img["northing"] = 5000.0
        img["lon"] = 0.05 + i * 0.0002
        img["lat"] = 0.045
        images.append(img)
    result = tool.compute_headings_from_gps(images, time_gap=30.0)
    assert [img["segment"] for img in result] == [0, 0, 0, 1, 1, 1]
    # Last image of segment 1 keeps the northward heading
    assert result[2]["yaw"] == pytest.approx(0.0, abs=0.5)
    # First image of segment 2 is eastward, not a blend across the gap
    assert result[3]["yaw"] == pytest.approx(90.0, abs=0.5)


def test_headings_keep_recorded_yaw(tool):
    images = [_track_image("A", i * 20.0, i * 0.0002, i) for i in range(3)]
    images[1]["yaw"] = 123.0
    result = tool.compute_headings_from_gps(images)
    assert result[1]["yaw"] == pytest.approx(123.0)


def _footprint_image(**overrides):
    img = {
        "filename": "test.jpg",
        "easting": 2000.0,
        "northing": 2000.0,
        "alt": 1000.0,
        "focal_length": 50.0,
        "yaw": 0.0,
        "pitch": -90.0,
        "roll": 0.0,
        "sensor_size_w": 36.0,
        "sensor_size_h": 24.0,
    }
    img.update(overrides)
    return img


def _flat_region():
    return {"n": 4000.0, "s": 0.0, "w": 0.0, "e": 4000.0, "nsres": 10.0, "ewres": 10.0}


def test_footprint_nadir_flat_dem(tool):
    """Nadir over flat ground: ray-traced corners match the analytic extent."""
    import numpy as np

    dem = np.full((400, 400), 700.0)
    footprint = tool.make_footprint(_footprint_image(), dem, _flat_region())
    assert len(footprint) == 5  # closed ring
    xs = [p[0] for p in footprint[:4]]
    ys = [p[1] for p in footprint[:4]]
    zs = [p[2] for p in footprint[:4]]
    # 300 m AGL, 50 mm lens: half extents 108 m (E) and 72 m (N)
    assert max(xs) == pytest.approx(2108.0, abs=1.0)
    assert min(xs) == pytest.approx(1892.0, abs=1.0)
    assert max(ys) == pytest.approx(2072.0, abs=1.0)
    assert min(ys) == pytest.approx(1928.0, abs=1.0)
    for z in zs:
        assert z == pytest.approx(700.0, abs=0.5)


def test_footprint_yaw_rotates(tool):
    import numpy as np

    dem = np.full((400, 400), 700.0)
    footprint = tool.make_footprint(_footprint_image(yaw=90.0), dem, _flat_region())
    xs = [p[0] for p in footprint[:4]]
    ys = [p[1] for p in footprint[:4]]
    # Long sensor axis now spans north-south
    assert max(ys) - min(ys) == pytest.approx(216.0, abs=2.0)
    assert max(xs) - min(xs) == pytest.approx(144.0, abs=2.0)


def test_footprint_slope_asymmetry(tool):
    """On ground rising north, the uphill footprint edge pulls in and the
    downhill edge extends."""
    import numpy as np

    # 500 m at the south edge rising to 900 m at the north edge
    rows = np.linspace(900.0, 500.0, 400)  # row 0 is north
    dem = np.repeat(rows[:, None], 400, axis=1)
    footprint = tool.make_footprint(_footprint_image(), dem, _flat_region())
    ys = sorted(p[1] for p in footprint[:4])
    north_offset = max(ys) - 2000.0
    south_offset = 2000.0 - min(ys)
    assert north_offset < 72.0 < south_offset


def test_footprint_horizon_ray_rejected(tool):
    import numpy as np

    dem = np.full((400, 400), 700.0)
    footprint = tool.make_footprint(_footprint_image(pitch=0.0), dem, _flat_region())
    assert footprint == []


def test_catmull_rom_endpoints_and_density(tool):
    points = [(0.0, 0.0, 100.0), (100.0, 50.0, 110.0), (200.0, 0.0, 100.0)]
    smooth = tool.catmull_rom_spline(points)
    assert len(smooth) > len(points)
    assert smooth[0] == pytest.approx(points[0])
    assert smooth[-1] == pytest.approx(points[-1])


def test_is_grid_flight(tool):
    # Boustrophedon grid: two 180-degree turns
    grid = [(0, 0, 0), (100, 0, 0), (100, 20, 0), (0, 20, 0), (0, 40, 0)]
    assert tool.is_grid_flight(grid)
    # Gentle arc: no sharp turns
    arc = [(0, 0, 0), (100, 10, 0), (200, 30, 0), (300, 60, 0)]
    assert not tool.is_grid_flight(arc)


def _square(x0, y0, size=10.0):
    return [
        (x0, y0, 0.0),
        (x0 + size, y0, 0.0),
        (x0 + size, y0 + size, 0.0),
        (x0, y0 + size, 0.0),
        (x0, y0, 0.0),
    ]


def test_footprint_overlap_half(tool):
    assert tool.footprint_overlap(_square(0, 0), _square(5, 0)) == pytest.approx(0.5)


def test_footprint_overlap_disjoint(tool):
    assert tool.footprint_overlap(_square(0, 0), _square(20, 20)) == pytest.approx(0.0)


def test_footprint_overlap_identical(tool):
    assert tool.footprint_overlap(_square(0, 0), _square(0, 0)) == pytest.approx(1.0)


def test_footprint_overlap_quarter(tool):
    assert tool.footprint_overlap(_square(0, 0), _square(5, 5)) == pytest.approx(0.25)


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
        footprints="footprints",
        stations="stations",
        path="path",
        env=session.env,
    )
    info = gs.vector_info_topo("footprints", env=session.env)
    assert info["areas"] == 3
    assert info["centroids"] == 3
    assert gs.vector_info_topo("stations", env=session.env)["points"] == 3
    assert gs.vector_info("stations", env=session.env)["map3d"] == 1
    # One camera, one segment: a single smoothed 3D line
    assert gs.vector_info_topo("path", env=session.env)["lines"] == 1
    assert gs.vector_info("path", env=session.env)["map3d"] == 1
    path_records = gs.parse_command(
        "v.db.select", map="path", format="json", env=session.env
    )["records"]
    assert path_records[0]["camera_serial"] == "TestCam"
    assert path_records[0]["n_images"] == 3
    records = gs.parse_command(
        "v.db.select", map="footprints", format="json", env=session.env
    )["records"]
    assert len(records) == 3
    for record in records:
        # Eastward flight line
        assert record["yaw"] == pytest.approx(90.0, abs=2.0)
        # AGL from constant 700 m ground under 1000 m flight altitude
        assert record["agl_alt"] == pytest.approx(300.0, abs=1.0)
        assert record["camera_serial"] == "TestCam"
    # 36 x 24 mm sensor, 300 m AGL, 50 mm lens: 216 x 144 m footprint
    areas = gs.parse_command(
        "v.to.db",
        map="footprints",
        option="area",
        flags="pc",
        format="json",
        env=session.env,
    )["records"]
    for area in areas:
        assert area["area"] == pytest.approx(216.0 * 144.0, rel=0.01)


@requires_exiftool
def test_tool_overlap_csv(session, photo_dir, tmp_path):
    overlap_file = tmp_path / "overlap.csv"
    gs.run_command(
        "v.photo.geometry",
        input=str(photo_dir),
        elevation="dtm",
        overlap=str(overlap_file),
        format="csv",
        env=session.env,
    )
    import csv as csv_module

    rows = list(csv_module.DictReader(overlap_file.open()))
    assert len(rows) == 3
    # Along-track footprint side is the short one (144 m: image top
    # faces the flight direction); ~90.5 m photo spacing eastward
    expected = (144.0 - 90.5) / 144.0
    for row in rows[:-1]:  # the last image has no next photo
        assert float(row["forward"]) == pytest.approx(expected, abs=0.02)
    assert rows[-1]["forward"] == ""


@requires_exiftool
def test_tool_overlap_density(session, photo_dir):
    gs.run_command(
        "v.photo.geometry",
        input=str(photo_dir),
        elevation="dtm",
        overlap_density="density",
        env=session.env,
    )
    stats = gs.parse_command("r.univar", map="density", format="json", env=session.env)
    if isinstance(stats, list):
        stats = stats[0]
    # 144 m along-track footprints at ~90.5 m spacing: two-image overlap
    # zones between neighbors, never three
    assert stats["max"] == 2
    assert stats["min"] == 1
    # Uncovered cells are NULL, so far fewer cells than the region
    region = gs.region(env=session.env)
    assert stats["n"] < region["cells"]
    # Union area: 216 m across track, 144 + 2 * 90.5 m along track
    expected_cells = 216.0 * (144.0 + 2 * 90.5) / (10.0 * 10.0)
    assert stats["n"] == pytest.approx(expected_cells, rel=0.05)
    # Magma color table was applied (pale yellow top end)
    colors = gs.read_command("r.colors.out", map="density", env=session.env)
    assert "252:253:191" in colors


@requires_exiftool
def test_tool_refuses_overwrite(session, photo_dir):
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "v.photo.geometry",
            input=str(photo_dir),
            elevation="dtm",
            footprints="footprints",
            env=session.env,
        )


@requires_exiftool
def test_tool_requires_an_output(session, photo_dir):
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "v.photo.geometry",
            input=str(photo_dir),
            elevation="dtm",
            env=session.env,
        )
