"""Test the download verification helpers of i.eodag with synthetic archives."""

import importlib.util
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[1] / "i.eodag.py"


@pytest.fixture(scope="module")
def eodag_module():
    pytest.importorskip("eodag")
    spec = importlib.util.spec_from_file_location("i_eodag", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def good_zip(tmp_path):
    path = tmp_path / "good.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        archive.writestr("a.txt", "A" * 1000)
        archive.writestr("b.txt", "B" * 1000)
    return path


def test_valid_zip(eodag_module, good_zip):
    size = good_zip.stat().st_size
    assert eodag_module.check_zip_integrity(good_zip) is None
    assert eodag_module.check_zip_integrity(good_zip, full=True) is None
    assert eodag_module.check_zip_integrity(good_zip, expected_size=size) is None


@pytest.mark.parametrize("full", [True, False])
def test_truncated_zip(eodag_module, good_zip, full):
    good_zip.write_bytes(good_zip.read_bytes()[:-500])
    assert eodag_module.check_zip_integrity(good_zip, full=full)


def test_crc_error_only_found_by_full_check(eodag_module, good_zip):
    data = bytearray(good_zip.read_bytes())
    data[data.index(b"A") + 10] = ord("X")
    good_zip.write_bytes(data)
    assert eodag_module.check_zip_integrity(good_zip) is None
    assert "a.txt" in eodag_module.check_zip_integrity(good_zip, full=True)


def test_size_mismatch(eodag_module, good_zip):
    size = good_zip.stat().st_size
    problem = eodag_module.check_zip_integrity(good_zip, expected_size=size + 1)
    assert str(size + 1) in problem


def test_expected_size(eodag_module):
    scene = SimpleNamespace(size=100, headers={"Content-Encoding": "identity"})
    assert eodag_module.get_expected_size(scene) == 100
    assert eodag_module.get_expected_size(SimpleNamespace(size=None)) is None
    gzipped = SimpleNamespace(size=100, headers={"Content-Encoding": "gzip"})
    assert eodag_module.get_expected_size(gzipped) is None


def test_get_scene_zip(eodag_module, tmp_path, good_zip):
    assert eodag_module.get_scene_zip(good_zip) == good_zip
    assert eodag_module.get_scene_zip(tmp_path / "missing.zip") is None

    other = tmp_path / "file.txt"
    other.write_text("content")
    assert eodag_module.get_scene_zip(other) is None

    # eodag moves archives it cannot identify as ZIP into a directory
    scene_dir = tmp_path / "scene"
    scene_dir.mkdir()
    moved = scene_dir / "scene.ZIP"
    moved.write_bytes(good_zip.read_bytes())
    assert eodag_module.get_scene_zip(scene_dir) == moved

    (scene_dir / "second.zip").write_bytes(good_zip.read_bytes())
    assert eodag_module.get_scene_zip(scene_dir) is None


def test_extracted_scene_has_no_zip(eodag_module, tmp_path):
    scene_dir = tmp_path / "scene.SAFE"
    scene_dir.mkdir()
    (scene_dir / "manifest.safe").write_text("content")
    assert eodag_module.get_scene_zip(scene_dir) is None


def test_remove_corrupt_download(eodag_module, tmp_path, good_zip):
    scene_dir = tmp_path / "scene"
    scene_dir.mkdir()
    moved = scene_dir / "scene.zip"
    moved.write_bytes(good_zip.read_bytes())
    record = tmp_path / "record"
    record.write_text("url")
    eodag_module.remove_corrupt_download(scene_dir, moved, record)
    assert not scene_dir.exists()
    assert not record.exists()

    record.write_text("url")
    eodag_module.remove_corrupt_download(good_zip, good_zip, record)
    assert not good_zip.exists()
    assert not record.exists()


def test_skip_existing_checks_every_scene(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    scenes = []
    for name in ("scene_a", "scene_b", "scene_c", "scene_d"):
        with zipfile.ZipFile(tmp_path / f"{name}.zip", "w") as archive:
            archive.writestr("a.txt", "A")
        scene = SimpleNamespace(
            product_type="S2_MSI_L2A",
            properties={
                "id": name,
                "title": name,
                "modificationDate": "2000-01-01T00:00:00Z",
            },
        )
        record = eodag_module.get_download_record(tmp_path, scene)
        record.parent.mkdir(exist_ok=True)
        record.write_text("url")
        scenes.append(scene)

    # A truncated archive must stay in the result to be downloaded again
    broken = tmp_path / "scene_c.zip"
    broken.write_bytes(broken.read_bytes()[:-10])

    result = eodag_module.skip_existing(tmp_path, list(scenes))
    assert result == [scenes[2]]


def test_skip_existing_uses_eodag4_property_names(eodag_module, tmp_path, monkeypatch):
    monkeypatch.setattr(eodag_module, "VER", eodag_module.EODAG_MAP[4])
    with zipfile.ZipFile(tmp_path / "scene_a.zip", "w") as archive:
        archive.writestr("a.txt", "A")
    # EODAG 4 calls modificationDate "updated"
    scene = SimpleNamespace(
        collection="S2_MSI_L2A",
        properties={
            "id": "scene_a",
            "title": "scene_a",
            "updated": "2000-01-01T00:00:00Z",
        },
    )
    record = eodag_module.get_download_record(tmp_path, scene)
    record.parent.mkdir(exist_ok=True)
    record.write_text("url")

    assert eodag_module.skip_existing(tmp_path, [scene]) == []


def make_scene(name, extract=True):
    return SimpleNamespace(
        product_type="S2_MSI_L2A",
        properties={"id": name, "title": name},
        downloader=SimpleNamespace(config=SimpleNamespace(extract=extract)),
    )


def prepare_existing_downloads(eodag_module, directory, scenes):
    (directory / "scene_a.zip").write_text("data")
    (directory / "scene_a").mkdir()
    (directory / "scene_a" / "file").write_text("data")
    (directory / "scene_a.txt").write_text("data")
    (directory / "scene_b.zip").write_text("data")
    for scene in scenes:
        record = eodag_module.get_download_record(directory, scene)
        record.parent.mkdir(exist_ok=True)
        record.write_text("url")


def test_find_existing_download(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    prepare_existing_downloads(eodag_module, tmp_path, [])
    found = eodag_module.find_existing_download(make_scene("scene_a"), str(tmp_path))
    assert sorted(path.name for path in found) == ["scene_a", "scene_a.zip"]
    assert eodag_module.find_existing_download(make_scene("c"), str(tmp_path)) == []


def test_remove_existing_download_extracted(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    scene, other = make_scene("scene_a"), make_scene("scene_b")
    prepare_existing_downloads(eodag_module, tmp_path, [scene, other])

    eodag_module.remove_existing_download(scene, str(tmp_path))

    # Only data and record of the scene are removed
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        ".downloaded",
        "scene_a.txt",
        "scene_b.zip",
    ]
    assert not eodag_module.get_download_record(tmp_path, scene).exists()
    assert eodag_module.get_download_record(tmp_path, other).exists()


def test_remove_existing_download_not_extracted(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    scene = make_scene("scene_a", extract=False)
    prepare_existing_downloads(eodag_module, tmp_path, [scene])

    eodag_module.remove_existing_download(scene, str(tmp_path))

    # The record is removed but the directory is not, as it is no scene archive
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        ".downloaded",
        "scene_a",
        "scene_a.txt",
        "scene_b.zip",
    ]
    assert not eodag_module.get_download_record(tmp_path, scene).exists()


def test_remove_existing_download_moved_archive(eodag_module, tmp_path, good_zip):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    scene = make_scene("scene_a", extract=False)
    scene_dir = tmp_path / "scene_a"
    scene_dir.mkdir()
    (scene_dir / "scene_a.zip").write_bytes(good_zip.read_bytes())

    eodag_module.remove_existing_download(scene, str(tmp_path))

    assert not scene_dir.exists()


class FakeGateway:
    """Gateway whose downloads of scenes are truncated or not delivered n times."""

    def __init__(self, directory, truncated_times, failed_times=None):
        self.directory = directory
        self.truncated_times = dict(truncated_times)
        self.failed_times = dict(failed_times or {})
        self.requested = []

    def download_all(self, scenes, downloaded_callback, **kwargs):
        self.requested.append([scene.properties["title"] for scene in scenes])
        for scene in scenes:
            name = scene.properties["title"]
            if self.failed_times.get(name, 0) > 0:
                self.failed_times[name] -= 1
                continue
            path = self.directory / f"{name}.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("a.txt", "A" * 1000)
            if self.truncated_times.get(name, 0) > 0:
                self.truncated_times[name] -= 1
                path.write_bytes(path.read_bytes()[:-20])
            scene.location = path.as_uri()
            downloaded_callback(scene)


@pytest.mark.parametrize(
    ("retries", "truncated_times", "requested"),
    [
        (0, {}, [["a", "b"]]),
        (2, {"b": 1}, [["a", "b"], ["b"]]),
        (2, {"a": 1, "b": 2}, [["a", "b"], ["a", "b"], ["b"]]),
    ],
)
def test_verify_download_succeeds(
    eodag_module, tmp_path, retries, truncated_times, requested
):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    gateway = FakeGateway(tmp_path, truncated_times)
    scenes = [make_scene("a"), make_scene("b")]
    eodag_module.verify_download(gateway, scenes, {}, retries=retries)
    assert gateway.requested == requested
    for name in ("a", "b"):
        assert eodag_module.check_zip_integrity(tmp_path / f"{name}.zip") is None


@pytest.mark.parametrize("retries", [0, 1])
def test_verify_download_fails_when_retries_are_exhausted(
    eodag_module, tmp_path, retries
):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    gateway = FakeGateway(tmp_path, {"b": 5})
    scenes = [make_scene("a"), make_scene("b")]
    with pytest.raises(SystemExit):
        eodag_module.verify_download(gateway, scenes, {}, retries=retries)
    assert len(gateway.requested) == retries + 1
    # Corrupt downloads are removed
    assert not (tmp_path / "b.zip").exists()
    assert (tmp_path / "a.zip").exists()


def test_verify_download_retries_failed_scenes(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    gateway = FakeGateway(tmp_path, {"a": 2}, failed_times={"b": 1})
    scenes = [make_scene("a"), make_scene("b")]
    eodag_module.verify_download(gateway, scenes, {}, retries=2)
    assert gateway.requested == [["a", "b"], ["b", "a"], ["a"]]


def test_verify_download_fails_if_scene_is_never_delivered(eodag_module, tmp_path):
    if eodag_module.EODAG_VERSION != 3:
        pytest.skip("The scenes are mocked for EODAG 3 only.")
    gateway = FakeGateway(tmp_path, {}, failed_times={"b": 5})
    scenes = [make_scene("a"), make_scene("b")]
    with pytest.raises(SystemExit):
        eodag_module.verify_download(gateway, scenes, {}, retries=1)
    assert gateway.requested == [["a", "b"], ["b"]]


def test_parse_query_keeps_values(eodag_module):
    query = eodag_module.parse_query(
        "a=INS-NOBS|none,b=30;ge,modificationDate=2026-10-15 00:14:12;le"
    )
    assert query == [
        ("a", [("INS-NOBS", None), (None, None)]),
        ("b", [(30.0, "ge")]),
        ("modificationDate", [("2026-10-15 00:14:12", "le")]),
    ]


@pytest.fixture
def filter_products(eodag_module, monkeypatch):
    # Both are only defined when the script runs as a module
    eodag_module.options = {"pattern": ""}
    eodag_module.SearchResult = pytest.importorskip(
        "eodag.api.search_result"
    ).SearchResult

    def filter_products(products, query, version=3):
        """Filter mocked products (id: properties) as EODAG `version` would return them."""
        monkeypatch.setattr(eodag_module, "VER", eodag_module.EODAG_MAP[version])
        scenes = [
            SimpleNamespace(properties={"id": key, **properties})
            for key, properties in products.items()
        ]
        result = eodag_module.filter_result(
            scenes,
            queryables=eodag_module.parse_query(query),
            area_relation=None,
            minimum_overlap=None,
            clouds=None,
            start=None,
            end=None,
            map=None,
        )
        return [scene.properties["id"] for scene in result]

    return filter_products


@pytest.fixture
def filter_by_query(filter_products):
    def filter_by_query(dates, query):
        products = {key: {"modificationDate": value} for key, value in dates.items()}
        return filter_products(products, query)

    return filter_by_query


def test_filter_result_compares_datetimes(filter_by_query):
    dates = {
        "a": "2026-10-14T23:00:00Z",
        "b": "2026-10-15T00:14:12.500Z",
        "c": "2026-10-16T12:00:00+02:00",
        "d": "2026-10-18T00:00:00Z",
        "e": "not a date",
        "f": None,
    }
    query = "modificationDate=2026-10-15 00:14:12;ge,modificationDate=2026-10-17;le"
    assert filter_by_query(dates, query) == ["b", "c"]


def test_filter_result_datetime_equality_ignores_notation(filter_by_query):
    dates = {"a": "2026-10-15T00:14:12Z", "b": "2026-10-15T00:14:13Z"}
    assert filter_by_query(dates, "modificationDate=2026-10-15 00:14:12") == ["a"]
    assert filter_by_query(dates, "modificationDate=2026-10-15 00:14:12;ne") == ["b"]


def test_filter_result_compares_non_dates_as_strings(
    eodag_module, filter_by_query, monkeypatch
):
    warnings = []
    monkeypatch.setattr(eodag_module.gs, "warning", warnings.append)
    dates = {"a": "2026-10-15", "b": "2026-10-15T00:00:00Z", "c": "other"}
    assert filter_by_query(dates, "modificationDate=other|2026-10-15") == [
        "c",
        "a",
        "b",
    ]
    assert filter_by_query({"c": "other"}, "modificationDate=2026-10-15;ne") == ["c"]
    assert not warnings

    # Ordering operators are honored as string comparison, with a single warning
    products = {"c": "other", "d": "zzz", "e": "1abc"}
    assert filter_by_query(products, "modificationDate=2026-10-15;ge") == ["c", "d"]
    assert len(warnings) == 1
    assert "modificationDate" in warnings[0]
    assert filter_by_query(products, "modificationDate=2026-10-15;le") == ["e"]


def test_filter_result_assumes_utc_without_timezone(filter_by_query):
    dates = {
        "naive": "2026-10-15T12:00:00",
        "utc": "2026-10-15T12:00:00Z",
        "offset": "2026-10-15T14:00:00+02:00",
        "other": "2026-10-15T12:00:00+02:00",
    }
    assert filter_by_query(dates, "modificationDate=2026-10-15 12:00:00") == [
        "naive",
        "utc",
        "offset",
    ]


def test_filter_result_maps_eodag3_queryables_to_eodag4(filter_products):
    products = {
        "a": {
            "updated": "2026-11-02T14:24:50.578079Z",
            "grid:code": "MGRS-32VNM",
            "sat:absolute_orbit": 50413,
            "sar:polarizations": ["VV", "VH"],
            "s2:datatake_type": "INS-NOBS",
        },
        "b": {
            "updated": "2026-10-31T13:12:19.945232Z",
            "grid:code": "MGRS-32VNN",
            "sat:absolute_orbit": 50414,
            "sar:polarizations": ["VV"],
            "sar:instrument_mode": "IW",
        },
    }

    def ids(query):
        return filter_products(products, query, version=4)

    assert ids("modificationDate=2026-11-01;ge") == ["a"]
    assert ids("tileIdentifier=32VNM;eq|32VNX;eq") == ["a"]
    assert ids("tileIdentifier=32VNM;ne") == ["b"]
    assert ids("orbitNumber=50414") == ["b"]
    assert ids("polarizationChannels=VV+VH") == ["a"]
    assert ids("sensorMode=INS-NOBS|IW") == ["a", "b"]


def test_filter_result_converts_eodag4_values(filter_products):
    products = {
        "a": {
            "order:status": "succeeded",
            "processing:version": "05.13",
            "instruments": ["MSI"],
            "s2:tile_id": "S2B_OPER_MSI_L1C_TL_T32VNM",
            "s1:slice_number": 10,
        },
        "b": {
            "order:status": "orderable",
            "processing:version": "004.03",
            "instruments": ["SAR"],
            "s2:tile_id": "other",
            "s1:slice_number": 11,
        },
    }

    def ids(query):
        return filter_products(products, query, version=4)

    assert ids("storageStatus=ONLINE") == ["a"]
    assert ids("storageStatus=OFFLINE|STAGING") == ["b"]
    assert ids("processorVersion=5.13|4.03") == ["a", "b"]
    assert ids("instrument=SAR") == ["b"]
    assert ids("granuleIdentifier=S2B_OPER_MSI_L1C_TL_T32VNM") == ["a"]
    assert ids("sliceNumber=10") == ["a"]


def test_filter_result_reports_missing_operator_without_warning(
    eodag_module, filter_by_query, monkeypatch
):
    warnings, verbose = [], []
    monkeypatch.setattr(eodag_module.gs, "warning", warnings.append)
    monkeypatch.setattr(eodag_module.gs, "verbose", verbose.append)
    assert filter_by_query({"a": "x", "b": "y"}, "modificationDate=x") == ["a"]
    assert not warnings
    assert (
        "No operator given for queryable <modificationDate> with value <x>"
        in verbose[0]
    )
