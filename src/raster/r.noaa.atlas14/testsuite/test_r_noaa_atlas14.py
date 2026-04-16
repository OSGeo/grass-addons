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
    def test_extracts_region_duration_ari_bound(self):
        c = r_noaa.parse_grid_filename("se_100yr_24hr.zip")
        self.assertEqual(c.region, "se")
        self.assertEqual(c.ari, 100)
        self.assertEqual(c.duration, "24hr")
        self.assertEqual(c.bound, "expected")

    def test_upper_bound_detected(self):
        c = r_noaa.parse_grid_filename("sw_upper_2yr_60min.zip")
        self.assertEqual(c.bound, "upper")
        self.assertEqual(c.ari, 2)
        self.assertEqual(c.duration, "60min")

    def test_lower_bound_detected(self):
        c = r_noaa.parse_grid_filename("orb_lwr_100yr_24hr.zip")
        self.assertEqual(c.bound, "lower")

    def test_metric_units_detected(self):
        c = r_noaa.parse_grid_filename("se_metric_10yr_24hr.zip")
        self.assertEqual(c.units, "metric")

    def test_ams_vs_pds(self):
        self.assertEqual(
            r_noaa.parse_grid_filename("se_ams_10yr_24hr.zip").series, "ams"
        )
        self.assertEqual(
            r_noaa.parse_grid_filename("se_pds_10yr_24hr.zip").series, "pds"
        )

    def test_no_match_returns_none_fields(self):
        c = r_noaa.parse_grid_filename("unrelated_file.zip")
        self.assertIsNone(c.region)
        self.assertIsNone(c.ari)
        self.assertIsNone(c.duration)


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
