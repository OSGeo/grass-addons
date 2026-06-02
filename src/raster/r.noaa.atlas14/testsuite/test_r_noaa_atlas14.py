"""
Unit tests for r.noaa.atlas14 pure-Python helpers.

These tests exercise the parsing, filtering, and safety helpers that do not
require network access or a running PFDS endpoint. The full point and grid
workflows are network-dependent and exercised by integration examples in the
docs.
"""

import importlib.util
import io
import sys
import zipfile
from pathlib import Path

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


MODULE_PATH = Path(__file__).resolve().parent.parent / "r.noaa.atlas14.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("r_noaa_atlas14", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["r_noaa_atlas14"] = module
    spec.loader.exec_module(module)
    return module


r_noaa = _load_module()


SAMPLE_PFDS = """\
Point precipitation frequency estimates (inches)
NOAA Atlas 14, Volume 2, Version 3
Data type: Precipitation depth
Units: English
Series: Partial duration
Latitude: 35.7796, Longitude: -78.6382
by duration for ARI (years):,1,2,5,10,25,50,100
5-min:,0.34,0.41,0.52,0.60,0.72,0.82,0.92
15-min:,0.71,0.86,1.09,1.27,1.52,1.72,1.93
60-min:,1.17,1.43,1.82,2.13,2.55,2.89,3.25
24-hr:,2.86,3.49,4.48,5.30,6.52,7.56,8.70
Upper bound of 90% confidence interval
by duration for ARI (years):,1,2,5,10,25,50,100
5-min:,0.38,0.46,0.58,0.67,0.81,0.92,1.04
60-min:,1.30,1.58,2.01,2.36,2.82,3.19,3.59
Lower bound of 90% confidence interval
by duration for ARI (years):,1,2,5,10,25,50,100
5-min:,0.30,0.37,0.47,0.54,0.65,0.73,0.82
60-min:,1.05,1.29,1.64,1.92,2.29,2.60,2.92
"""


class TestParsePfdsResponse(TestCase):
    def test_parses_all_three_sections(self):
        data = r_noaa.parse_pfds_response(SAMPLE_PFDS, request={"lat": 35.78})
        self.assertEqual(data["request"], {"lat": 35.78})
        for section in ("expected", "upper", "lower"):
            rps = data["tables"][section]["return_periods_years"]
            self.assertEqual(rps, [1, 2, 5, 10, 25, 50, 100])
            self.assertTrue(data["tables"][section]["rows"])

    def test_expected_rows_have_numeric_values(self):
        data = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        rows = data["tables"]["expected"]["rows"]
        first = rows[0]
        self.assertEqual(first["duration"], "5-min")
        self.assertAlmostEqual(first["values"]["1"], 0.34)
        self.assertAlmostEqual(first["values"]["100"], 0.92)

    def test_metadata_keys_are_normalized(self):
        data = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        meta = data["metadata"]
        self.assertEqual(meta.get("data_type"), "Precipitation depth")
        self.assertEqual(meta.get("units"), "English")

    def test_empty_input_raises(self):
        with self.assertRaises(r_noaa.Atlas14Error):
            r_noaa.parse_pfds_response("")

    def test_no_expected_rows_raises(self):
        text = "Point precipitation frequency estimates\nby duration for ARI (years):,1,2\n"
        with self.assertRaises(r_noaa.Atlas14Error):
            r_noaa.parse_pfds_response(text)


class TestParseGridFilename(TestCase):
    """Filenames here are verified against the actual NOAA HDSC index."""

    def test_expected_pds_hour(self):
        c = r_noaa.parse_grid_filename("se2yr24ha.zip")
        self.assertEqual(c.region, "se")
        self.assertEqual(c.ari, 2)
        self.assertEqual(c.duration, "24hr")
        self.assertEqual(c.bound, "expected")
        self.assertEqual(c.series, "pds")
        self.assertEqual(c.statistic, "depth")
        self.assertEqual(c.units, "english")

    def test_upper_bound_ams_minute(self):
        c = r_noaa.parse_grid_filename("orb1000yr30mau_ams.zip")
        self.assertEqual(c.region, "orb")
        self.assertEqual(c.ari, 1000)
        self.assertEqual(c.duration, "30min")
        self.assertEqual(c.bound, "upper")
        self.assertEqual(c.series, "ams")

    def test_lower_bound_day(self):
        c = r_noaa.parse_grid_filename("se1000yr60dal.zip")
        self.assertEqual(c.region, "se")
        self.assertEqual(c.ari, 1000)
        self.assertEqual(c.duration, "60day")
        self.assertEqual(c.bound, "lower")
        self.assertEqual(c.series, "pds")

    def test_leading_zero_duration_stripped(self):
        # NOAA uses 05m, 02h, 03d — we normalize to 5min/2hr/3day.
        c = r_noaa.parse_grid_filename("se1yr05ma.zip")
        self.assertEqual(c.duration, "5min")

    def test_inner_raster_stem_parses(self):
        c = r_noaa.parse_grid_filename("se2yr24ha.asc")
        self.assertEqual(c.region, "se")
        self.assertEqual(c.ari, 2)

    def test_unknown_region_code_becomes_none(self):
        c = r_noaa.parse_grid_filename("xx2yr24ha.zip")
        self.assertIsNone(c.region)

    def test_non_matching_returns_empty_metadata(self):
        c = r_noaa.parse_grid_filename("unrelated_file.zip")
        self.assertIsNone(c.region)
        self.assertIsNone(c.ari)
        self.assertIsNone(c.duration)
        self.assertIsNone(c.bound)


class TestSanitizeName(TestCase):
    def test_replaces_invalid_chars(self):
        self.assertEqual(r_noaa.sanitize_name("a14.se-100yr/24hr"), "a14_se_100yr_24hr")

    def test_collapses_repeats_and_strips(self):
        self.assertEqual(r_noaa.sanitize_name("__foo___bar__"), "foo_bar")

    def test_truncates_to_63_chars(self):
        result = r_noaa.sanitize_name("a" * 100)
        self.assertEqual(len(result), 63)


class TestNormalizeDuration(TestCase):
    def test_alias_lookup(self):
        self.assertEqual(r_noaa.normalize_duration("24-hour"), "24hr")
        self.assertEqual(r_noaa.normalize_duration("5-minute"), "5min")

    def test_case_insensitive_alias(self):
        self.assertEqual(r_noaa.normalize_duration("2-DAY"), "2day")

    def test_already_short_form_passes_through(self):
        self.assertEqual(r_noaa.normalize_duration("24hr"), "24hr")


class TestFilterCandidates(TestCase):
    def _make(self, **kwargs):
        defaults = dict(
            url="u",
            filename="f.zip",
            region="se",
            bound="expected",
            statistic="depth",
            units="english",
            series="pds",
            duration="24hr",
            ari=100,
        )
        defaults.update(kwargs)
        return r_noaa.GridCandidate(**defaults)

    def test_aris_filter_is_strict_rejects_none(self):
        c_known = self._make(ari=100)
        c_unknown = self._make(ari=None)
        out = r_noaa.filter_candidates(
            [c_known, c_unknown],
            bound="expected",
            statistic="depth",
            units="english",
            series="pds",
            durations=None,
            aris={100},
        )
        self.assertEqual(out, [c_known])

    def test_durations_filter_is_strict_rejects_none(self):
        c_known = self._make(duration="24hr")
        c_unknown = self._make(duration=None)
        out = r_noaa.filter_candidates(
            [c_known, c_unknown],
            bound="expected",
            statistic="depth",
            units="english",
            series="pds",
            durations={"24hr"},
            aris=None,
        )
        self.assertEqual(out, [c_known])

    def test_statistic_filter_is_permissive_for_none(self):
        c_unknown = self._make(statistic=None)
        out = r_noaa.filter_candidates(
            [c_unknown],
            bound="expected",
            statistic="depth",
            units="english",
            series="pds",
            durations=None,
            aris=None,
        )
        self.assertEqual(out, [c_unknown])

    def test_bound_all_matches_any(self):
        c1 = self._make(bound="expected")
        c2 = self._make(bound="upper")
        out = r_noaa.filter_candidates(
            [c1, c2],
            bound="all",
            statistic="depth",
            units="english",
            series="pds",
            durations=None,
            aris=None,
        )
        self.assertEqual(out, [c1, c2])

    def test_bound_mismatch_rejected(self):
        c1 = self._make(bound="upper")
        out = r_noaa.filter_candidates(
            [c1],
            bound="expected",
            statistic="depth",
            units="english",
            series="pds",
            durations=None,
            aris=None,
        )
        self.assertEqual(out, [])


class TestParseCoordinates(TestCase):
    def test_single_pair(self):
        self.assertEqual(
            r_noaa.parse_coordinates("-78.6382,35.7796"),
            [(-78.6382, 35.7796)],
        )

    def test_multiple_pairs(self):
        self.assertEqual(
            r_noaa.parse_coordinates("-78.6,35.7,-81.0,29.5"),
            [(-78.6, 35.7), (-81.0, 29.5)],
        )

    def test_whitespace_tolerated(self):
        self.assertEqual(
            r_noaa.parse_coordinates("  -78.6 , 35.7 , -81.0 , 29.5  "),
            [(-78.6, 35.7), (-81.0, 29.5)],
        )

    def test_empty_returns_empty_list(self):
        self.assertEqual(r_noaa.parse_coordinates(""), [])

    def test_odd_count_raises(self):
        with self.assertRaises(r_noaa.Atlas14Error):
            r_noaa.parse_coordinates("-78.6,35.7,-81.0")

    def test_non_numeric_raises(self):
        with self.assertRaises(r_noaa.Atlas14Error):
            r_noaa.parse_coordinates("-78.6,abc")


class TestRegionCenterLonLat(TestCase):
    """Exercises region_center_lonlat() against the actual g.region output
    of the test mapset."""

    def test_returns_lonlat_tuple(self):
        self.use_temp_region()
        try:
            self.runModule("g.region", flags="d")
            lon, lat = r_noaa.region_center_lonlat()
            self.assertIsInstance(lon, float)
            self.assertIsInstance(lat, float)
            self.assertGreaterEqual(lat, -90.0)
            self.assertLessEqual(lat, 90.0)
            self.assertGreaterEqual(lon, -180.0)
            self.assertLessEqual(lon, 180.0)
        finally:
            self.del_temp_region()


class TestReprojectLonlat(TestCase):
    """Exercises _reproject_lonlat_to_project() against the NC SPM CRS."""

    def test_raleigh_reprojects_into_nc_spm(self):
        # Downtown Raleigh in WGS84 lon/lat -> NC SPM meters (EPSG:3358).
        projected = r_noaa._reproject_lonlat_to_project([(-78.6382, 35.7796, {})])
        self.assertEqual(len(projected), 1)
        east, north = projected[0]
        # Raleigh sits around 642000 E, 225000 N in the NC SPM project.
        self.assertAlmostEqual(east, 642310, delta=2000)
        self.assertAlmostEqual(north, 225207, delta=2000)

    def test_order_preserved_for_multiple_points(self):
        pts = [(-78.6382, 35.7796, {}), (-80.8431, 35.2271, {})]
        projected = r_noaa._reproject_lonlat_to_project(pts)
        self.assertEqual(len(projected), 2)
        # Charlotte (second point) is west of Raleigh in NC SPM.
        self.assertLess(projected[1][0], projected[0][0])


class TestMultiPointCsv(TestCase):
    def test_combined_csv_has_lon_lat_columns(self):
        d1 = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        d1["request"] = {"lon": -78.6, "lat": 35.7}
        d2 = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        d2["request"] = {"lon": -81.0, "lat": 29.5}
        text = r_noaa._multi_point_csv_text([d1, d2], "expected", ".3f")
        lines = text.strip().splitlines()
        self.assertEqual(lines[0].split(",")[:4], ["lon", "lat", "bound", "duration"])
        # Each data row starts with a lon value from one of the two points.
        data_rows = lines[1:]
        lons = {row.split(",")[0] for row in data_rows}
        self.assertEqual(lons, {"-78.6", "-81.0"})

    def test_custom_separator_applied(self):
        d1 = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        d1["request"] = {"lon": -78.6, "lat": 35.7}
        text = r_noaa._multi_point_csv_text([d1], "expected", ".3f", separator="|")
        header = text.strip().splitlines()[0]
        self.assertEqual(header.split("|")[:4], ["lon", "lat", "bound", "duration"])
        self.assertNotIn(",", header)


class TestPfdsToCsvText(TestCase):
    def test_custom_separator_applied(self):
        data = r_noaa.parse_pfds_response(SAMPLE_PFDS)
        text = r_noaa.pfds_to_csv_text(data, "expected", ".3f", separator="\t")
        header = text.splitlines()[0]
        self.assertEqual(header.split("\t")[0], "duration")
        self.assertNotIn(",", header)


class TestDurationToHours(TestCase):
    def test_minute_to_hour(self):
        self.assertAlmostEqual(r_noaa.duration_to_hours("5min"), 5 / 60)
        self.assertAlmostEqual(r_noaa.duration_to_hours("60min"), 1.0)

    def test_hour(self):
        self.assertEqual(r_noaa.duration_to_hours("24hr"), 24.0)

    def test_day(self):
        self.assertEqual(r_noaa.duration_to_hours("2day"), 48.0)

    def test_unparseable_raises(self):
        with self.assertRaises(r_noaa.Atlas14Error):
            r_noaa.duration_to_hours("fortnight")


class TestRescaleNoaaRaster(TestCase):
    """End-to-end: build a raw-encoded raster, run rescale, check values."""

    input_raster = "a14_rescale_input"

    def setUp(self):
        self.use_temp_region()
        self.runModule("g.region", n=10, s=0, e=10, w=0, res=1)
        # Raw value 2500 = 2.500 inches in NOAA 1000ths-of-inch encoding.
        self.runModule(
            "r.mapcalc",
            expression=f"{self.input_raster} = 2500",
            overwrite=True,
        )

    def tearDown(self):
        self.runModule(
            "g.remove",
            type="raster",
            name=f"{self.input_raster},{self.input_raster}_test",
            flags="f",
        )
        self.del_temp_region()

    def _copy_input(self):
        out = f"{self.input_raster}_test"
        self.runModule(
            "r.mapcalc",
            expression=f"{out} = {self.input_raster}",
            overwrite=True,
        )
        return out

    def test_depth_english_scales_to_inches(self):
        r = self._copy_input()
        label = r_noaa.rescale_noaa_raster(
            r, source_duration="24hr", output_statistic="depth", output_units="english"
        )
        self.assertEqual(label, "inches")
        stats = gs.parse_command("r.univar", map=r, flags="g")
        # All valid cells were 2500 -> 2.5 inches
        self.assertAlmostEqual(float(stats["min"]), 2.5, places=4)
        self.assertAlmostEqual(float(stats["max"]), 2.5, places=4)

    def test_depth_metric_scales_to_mm(self):
        r = self._copy_input()
        label = r_noaa.rescale_noaa_raster(
            r, source_duration="24hr", output_statistic="depth", output_units="metric"
        )
        self.assertEqual(label, "mm")
        stats = gs.parse_command("r.univar", map=r, flags="g")
        # 2500 * 0.0254 = 63.5 mm
        self.assertAlmostEqual(float(stats["min"]), 63.5, places=3)

    def test_intensity_metric_per_hour(self):
        r = self._copy_input()
        label = r_noaa.rescale_noaa_raster(
            r,
            source_duration="24hr",
            output_statistic="intensity",
            output_units="metric",
        )
        self.assertEqual(label, "mm/hr")
        stats = gs.parse_command("r.univar", map=r, flags="g")
        # 2500 * 0.0254 / 24 hr = 2.645833... mm/hr
        self.assertAlmostEqual(float(stats["min"]), 2500 * 0.0254 / 24.0, places=4)


class TestSafeExtractZip(TestCase):
    def test_rejects_path_traversal(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.txt", b"pwned")
        buf.seek(0)

        dest = Path(self._make_tmpdir())
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(r_noaa.Atlas14Error):
                r_noaa._safe_extract_zip(zf, dest)

    def test_rejects_absolute_path(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("/tmp/evil.txt", b"pwned")
        buf.seek(0)

        dest = Path(self._make_tmpdir())
        with zipfile.ZipFile(buf) as zf:
            with self.assertRaises(r_noaa.Atlas14Error):
                r_noaa._safe_extract_zip(zf, dest)

    def test_allows_safe_member(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("sub/ok.txt", b"fine")
        buf.seek(0)

        dest = Path(self._make_tmpdir())
        with zipfile.ZipFile(buf) as zf:
            r_noaa._safe_extract_zip(zf, dest)
        self.assertTrue((dest / "sub" / "ok.txt").exists())

    def _make_tmpdir(self):
        import shutil
        import tempfile

        path = tempfile.mkdtemp(prefix="atlas14_test_")
        self.addCleanup(shutil.rmtree, path, ignore_errors=True)
        return path


if __name__ == "__main__":
    test()
