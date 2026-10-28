"""Comprehensive test suite for r.in.ssurgo addon.

Tests are organised into sections:

1. Pure utility / helper functions (no GRASS session required)
2. SDAClient SQL generation
3. SDAClient HTTP interactions (mocked)
4. SDA response → GeoJSON pipeline
5. Module-level constants and enums
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


class TestParseWktCoordinates:
    """Tests for _parse_wkt_coordinates."""

    def test_basic_pair(self, ssurgo_module):
        result = ssurgo_module._parse_wkt_coordinates("1.0 2.0")
        assert result == [[1.0, 2.0]]

    def test_multiple_pairs(self, ssurgo_module):
        result = ssurgo_module._parse_wkt_coordinates("1.0 2.0, 3.0 4.0, 5.0 6.0")
        assert result == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]

    def test_extra_whitespace(self, ssurgo_module):
        result = ssurgo_module._parse_wkt_coordinates("  1.5  2.5 ,  3.5  4.5  ")
        assert result == [[1.5, 2.5], [3.5, 4.5]]

    def test_three_dimensional_coords(self, ssurgo_module):
        """3D coordinates should take only the first two values."""
        result = ssurgo_module._parse_wkt_coordinates("1.0 2.0 99.0")
        assert result == [[1.0, 2.0]]

    def test_empty_string(self, ssurgo_module):
        result = ssurgo_module._parse_wkt_coordinates("")
        assert result == []

    def test_single_number_skipped(self, ssurgo_module):
        """A token with only one number should be skipped."""
        result = ssurgo_module._parse_wkt_coordinates("42")
        assert result == []

    def test_negative_coordinates(self, ssurgo_module):
        result = ssurgo_module._parse_wkt_coordinates("-79.5 35.2, -78.1 36.0")
        assert result == [[-79.5, 35.2], [-78.1, 36.0]]


class TestWktToGeojsonGeometry:
    """Tests for _wkt_to_geojson_geometry."""

    def test_simple_polygon(self, ssurgo_module):
        wkt = "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "Polygon"
        assert len(result["coordinates"]) == 1  # one ring
        assert len(result["coordinates"][0]) == 5  # closed ring (5 points)
        assert result["coordinates"][0][0] == [0.0, 0.0]
        assert result["coordinates"][0][-1] == [0.0, 0.0]

    def test_polygon_with_hole(self, ssurgo_module):
        wkt = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0),(2 2, 8 2, 8 8, 2 8, 2 2))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "Polygon"
        assert len(result["coordinates"]) == 2  # outer ring + hole

    def test_multipolygon(self, ssurgo_module):
        wkt = "MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)),((2 2, 3 2, 3 3, 2 3, 2 2)))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "MultiPolygon"
        assert len(result["coordinates"]) == 2  # two polygons

    def test_multipolygon_single_polygon(self, ssurgo_module):
        wkt = "MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "MultiPolygon"
        assert len(result["coordinates"]) == 1

    def test_case_insensitive(self, ssurgo_module):
        wkt = "polygon((0 0, 1 0, 1 1, 0 1, 0 0))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "Polygon"

    def test_unsupported_type_returns_none(self, ssurgo_module):
        result = ssurgo_module._wkt_to_geojson_geometry("POINT(1 2)")
        assert result is None

    def test_whitespace_handling(self, ssurgo_module):
        wkt = "  POLYGON (( 0 0, 1 0, 1 1, 0 1, 0 0 ))  "
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result is not None
        assert result["type"] == "Polygon"

    def test_real_world_polygon(self, ssurgo_module):
        """Test with coordinates similar to real SSURGO data."""
        wkt = (
            "POLYGON(("
            "-79.1234 35.5678, -79.1234 35.6789, "
            "-79.0123 35.6789, -79.0123 35.5678, "
            "-79.1234 35.5678"
            "))"
        )
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "Polygon"
        # Check first coordinate is negative longitude
        assert result["coordinates"][0][0][0] < 0


class TestCheckIfZipfile:
    """Tests for check_if_zipfile.

    The function validates the zip and looks for a ``<base>.gdb/`` directory
    inside it, so tests build a real (tiny) zip fixture on disk.
    """

    @staticmethod
    def _make_fixture_zip(tmp_path, base_name="data", with_gdb=True):
        import zipfile

        zip_path = tmp_path / f"{base_name}.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            if with_gdb:
                # Empty marker entry inside the expected gdb directory
                zf.writestr(f"{base_name}.gdb/gdb", b"")
            else:
                zf.writestr("README.txt", b"no gdb here")
        return zip_path

    def test_zip_path_returns_vsizip(self, ssurgo_module, tmp_path):
        zip_path = self._make_fixture_zip(tmp_path, "data")
        result = ssurgo_module.check_if_zipfile(zip_path)
        result_str = str(result)
        assert result_str.startswith("/vsizip/")
        assert result_str.endswith("data.gdb/")
        assert str(zip_path) in result_str

    def test_zip_without_gdb_raises(self, ssurgo_module, tmp_path):
        zip_path = self._make_fixture_zip(tmp_path, "no_gdb", with_gdb=False)
        with pytest.raises(ValueError, match="not found in ZIP"):
            ssurgo_module.check_if_zipfile(zip_path)

    def test_missing_path_raises(self, ssurgo_module, tmp_path):
        with pytest.raises(FileNotFoundError):
            ssurgo_module.check_if_zipfile(tmp_path / "does_not_exist.zip")

    def test_non_zip_existing_path_passes_through(self, ssurgo_module, tmp_path):
        """A non-zip path that exists should be returned unmodified."""
        # The .gdb directory case: pass a real directory
        gdb_dir = tmp_path / "data.gdb"
        gdb_dir.mkdir()
        result = ssurgo_module.check_if_zipfile(gdb_dir)
        assert result == gdb_dir.resolve()


class TestHydrologicSoilGroupCategories:
    """Tests for hydrologic_soil_group_categories.

    The module writes the rules via ``gs.write_command("r.category", ...)``,
    not ``tools.r_category``. Tests exercise the call against the mocked gs.
    """

    def _capture_call(self, ssurgo_module):
        """Run the function and return the (args, kwargs) of the gs.write_command call."""
        ssurgo_module.gs.write_command.reset_mock()
        ssurgo_module.hydrologic_soil_group_categories("test_hsg")
        ssurgo_module.gs.write_command.assert_called_once()
        return ssurgo_module.gs.write_command.call_args

    def test_calls_r_category(self, ssurgo_module):
        call_args = self._capture_call(ssurgo_module)
        assert call_args.args[0] == "r.category"

    def test_map_name_passed(self, ssurgo_module):
        ssurgo_module.gs.write_command.reset_mock()
        ssurgo_module.hydrologic_soil_group_categories("my_hydgrp")
        call_args = ssurgo_module.gs.write_command.call_args
        assert call_args.kwargs["map"] == "my_hydgrp"

    def test_separator_is_pipe(self, ssurgo_module):
        call_args = self._capture_call(ssurgo_module)
        assert call_args.kwargs["separator"] == "pipe"

    def test_rules_read_from_stdin(self, ssurgo_module):
        """rules='-' tells r.category to read from stdin."""
        call_args = self._capture_call(ssurgo_module)
        assert call_args.kwargs["rules"] == "-"

    def test_rules_contain_all_single_groups(self, ssurgo_module):
        """Stdin payload must include labels for HSG codes 1-4."""
        call_args = self._capture_call(ssurgo_module)
        stdin_text = call_args.kwargs["stdin"]
        for code, letter in [("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")]:
            assert f"{code}|{letter}:" in stdin_text, (
                f"Missing category for HSG code {code} ({letter})"
            )

    def test_rules_contain_all_dual_groups(self, ssurgo_module):
        """Stdin payload must include labels for dual HSG codes 11-14."""
        call_args = self._capture_call(ssurgo_module)
        stdin_text = call_args.kwargs["stdin"]
        for code in ("11", "12", "13", "14"):
            assert f"{code}|" in stdin_text, (
                f"Missing category for dual HSG code {code}"
            )

    def test_rules_use_pipe_delimited_format(self, ssurgo_module):
        """Each rule line must be in 'code|label' format."""
        call_args = self._capture_call(ssurgo_module)
        stdin_text = call_args.kwargs["stdin"]
        lines = [line for line in stdin_text.strip().split("\n") if line]
        assert len(lines) == 8
        for line in lines:
            parts = line.split("|", 1)
            assert len(parts) == 2, f"Rule line not pipe-delimited: {line}"
            assert parts[0].strip().isdigit(), f"Code is not numeric: {parts[0]}"
            assert len(parts[1].strip()) > 0, f"Label is empty for code {parts[0]}"


class TestSoilAggMethod:
    """Tests for the SoilAggMethod enum."""

    def test_values(self, SoilAggMethod):
        assert SoilAggMethod.DOMINANT_COMPONENT.value == "dominant_component"
        assert SoilAggMethod.WEIGHTED_COMPONENT.value == "weighted_component"

    def test_members(self, SoilAggMethod):
        names = [m.name for m in SoilAggMethod]
        assert "DOMINANT_COMPONENT" in names
        assert "WEIGHTED_COMPONENT" in names


class TestBuildSdaSql:
    """Tests for SDAClient._build_sda_sql."""

    AOI = "POLYGON((-79 35, -79 36, -78 36, -78 35, -79 35))"

    def test_dominant_component_contains_expected_keywords(
        self, SDAClient, SoilAggMethod
    ):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            desgnmaster="A",
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in sql
        assert "SDA_Get_MupolygonWktWgs84_from_Mukey" in sql
        assert "ROW_NUMBER()" in sql
        assert "dom_comp" in sql
        assert "ksat_l" in sql
        assert "ksat_r" in sql
        assert "ksat_h" in sql
        assert "hydgrp" in sql
        assert "mukey_int" in sql

    def test_weighted_component_contains_expected_keywords(
        self, SDAClient, SoilAggMethod
    ):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            desgnmaster="A",
            agg=SoilAggMethod.WEIGHTED_COMPONENT,
        )
        assert "SDA_Get_Mukey_from_intersection_with_WktWgs84" in sql
        assert "comppct_r" in sql
        assert "ksat_r_comp" in sql
        assert "ksat_l_comp" in sql
        assert "ksat_h_comp" in sql

    def test_aoi_wkt_embedded_in_sql(self, SDAClient, SoilAggMethod):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert self.AOI in sql

    def test_depth_parameters_embedded(self, SDAClient, SoilAggMethod):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=5,
            bottom_cm=30,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "5.0" in sql
        assert "30.0" in sql

    def test_desgnmaster_embedded(self, SDAClient, SoilAggMethod):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            desgnmaster="B",
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "h.desgnmaster = 'B'" in sql

    def test_conversion_factor_applied(self, SDAClient, SoilAggMethod, ssurgo_module):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        conv = ssurgo_module.MICROMETERS_PER_SECOND_TO_MM_PER_HOUR
        assert str(conv) in sql

    def test_returns_string(self, SDAClient, SoilAggMethod):
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert isinstance(sql, str)
        assert len(sql) > 100

    def test_dominant_selects_rn_equals_1(self, SDAClient, SoilAggMethod):
        """Dominant component query must filter to row number 1."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "rn = 1" in sql

    def test_weighted_groups_by_mukey(self, SDAClient, SoilAggMethod):
        """Weighted component query must GROUP BY mukey."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=25,
            agg=SoilAggMethod.WEIGHTED_COMPONENT,
        )
        assert "GROUP BY mukey" in sql

    def test_dominant_includes_extended_horizon_fields(self, SDAClient, SoilAggMethod):
        """The dominant-component SQL must project the depth-weighted SSURGO
        fields beyond Ksat (texture, AWC, OM, bulk density, pH, CEC) plus
        component-level dominants (compname, drainagecl, slope_r).
        """
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=100,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        for fld in (
            "sandtotal_r",
            "silttotal_r",
            "claytotal_r",
            "awc_r",
            "om_r",
            "dbthirdbar_r",
            "ph1to1h2o_r",
            "cec7_r",
        ):
            assert f"hz.{fld}" in sql, (
                f"Depth-weighted field {fld} missing from dominant SQL"
            )
        for fld in ("compname", "drainagecl", "slope_r"):
            assert f"d.{fld}" in sql, (
                f"Component-dominant field {fld} missing from dominant SQL"
            )

    def test_horizon_filter_uses_depth_overlap(self, SDAClient, SoilAggMethod):
        """Horizons must be selected by overlap with [top, bottom], not by
        starting at the surface. The previous filter (`hzdept_r = 0`) silently
        dropped any horizon that didn't begin at depth 0, so depth ranges like
        5–100 cm or 0–100 cm with split A horizons returned no ksat values.
        """
        client = SDAClient()
        for agg_method in (
            SoilAggMethod.DOMINANT_COMPONENT,
            SoilAggMethod.WEIGHTED_COMPONENT,
        ):
            sql = client._build_sda_sql(
                aoi_wkt=self.AOI,
                top_cm=10,
                bottom_cm=80,
                agg=agg_method,
            )
            # Old buggy form must be gone for both aggregation methods.
            assert "hzdept_r = 0" not in sql
            assert "hzdepb_r > 0" not in sql
            # New form: horizon overlaps requested [top, bottom].
            assert "hzdept_r < 80.0" in sql
            assert "hzdepb_r > 10.0" in sql


class TestSdaPostSql:
    """Tests for SDAClient._sda_post_sql with mocked HTTP."""

    # Raw SDA JSON+COLUMNNAME format: first row = column names, rest = data
    FAKE_RAW_RESPONSE = {
        "Table": [
            ["mukey", "ksat_r"],
            ["12345", "1.5"],
        ]
    }
    # Expected dict format after conversion in _sda_post_sql
    EXPECTED_RESPONSE = {"Table": [{"mukey": "12345", "ksat_r": "1.5"}]}

    def _make_mock_response(self, body_dict, status=200):
        """Create a mock HTTP response."""
        body = json.dumps(body_dict).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        resp.status = status
        return resp

    def test_successful_post(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            result = client._sda_post_sql("SELECT 1")
            assert result == self.EXPECTED_RESPONSE
            mock_urlopen.assert_called_once()

    def test_custom_url(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            custom_url = "https://example.com/sda"
            client._sda_post_sql("SELECT 1", sda_url=custom_url)
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            assert request_obj.full_url == custom_url

    def test_default_url_used(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            client._sda_post_sql("SELECT 1")
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            assert "sdmdataaccess" in request_obj.full_url.lower()

    def test_sql_in_form_encoded_body(self, SDAClient, ssurgo_module):
        """Body must be URL-encoded form data with QUERY and FORMAT params."""
        from urllib.parse import parse_qs

        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            test_sql = "SELECT mukey FROM component"
            client._sda_post_sql(test_sql)
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            body = request_obj.data.decode("utf-8")
            params = parse_qs(body)
            assert params["QUERY"] == [test_sql]
            assert params["FORMAT"] == ["JSON+COLUMNNAME"]

    def test_http_error_calls_fatal(self, SDAClient, ssurgo_module):
        from urllib.error import HTTPError

        with patch.object(ssurgo_module, "urlopen") as mock_urlopen, patch.object(
            ssurgo_module.gs, "fatal", side_effect=SystemExit
        ):
            mock_urlopen.side_effect = HTTPError(
                url="http://test", code=500, msg="Server Error", hdrs={}, fp=None
            )
            client = SDAClient()
            with pytest.raises(SystemExit):
                client._sda_post_sql("SELECT 1")

    def test_url_error_calls_fatal(self, SDAClient, ssurgo_module):
        from urllib.error import URLError

        with patch.object(ssurgo_module, "urlopen") as mock_urlopen, patch.object(
            ssurgo_module.gs, "fatal", side_effect=SystemExit
        ):
            mock_urlopen.side_effect = URLError("Connection refused")
            client = SDAClient()
            with pytest.raises(SystemExit):
                client._sda_post_sql("SELECT 1")

    def test_json_decode_error_calls_fatal(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen, patch.object(
            ssurgo_module.gs, "fatal", side_effect=SystemExit
        ):
            resp = MagicMock()
            resp.read.return_value = b"NOT JSON"
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = resp
            client = SDAClient()
            with pytest.raises(SystemExit):
                client._sda_post_sql("SELECT 1")

    def test_request_headers(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            client._sda_post_sql("SELECT 1")
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            assert (
                request_obj.get_header("Content-type")
                == "application/x-www-form-urlencoded"
            )

    def test_request_method_is_post(self, SDAClient, ssurgo_module):
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(self.FAKE_RAW_RESPONSE)
            client = SDAClient()
            client._sda_post_sql("SELECT 1")
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            assert request_obj.method == "POST"

    def test_columnname_conversion(self, SDAClient, ssurgo_module):
        """Verify JSON+COLUMNNAME rows are converted to list of dicts."""
        raw = {
            "Table": [
                ["mukey", "compname", "hydgrp"],
                ["12345", "Alfisol", "B"],
                ["67890", "Mollisol", "A"],
            ]
        }
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(raw)
            client = SDAClient()
            result = client._sda_post_sql("SELECT 1")
            assert len(result["Table"]) == 2
            assert result["Table"][0] == {
                "mukey": "12345",
                "compname": "Alfisol",
                "hydgrp": "B",
            }
            assert result["Table"][1] == {
                "mukey": "67890",
                "compname": "Mollisol",
                "hydgrp": "A",
            }

    def test_empty_table_passthrough(self, SDAClient, ssurgo_module):
        """If Table has only column names and no data rows, return empty."""
        raw = {"Table": [["mukey", "compname"]]}
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(raw)
            client = SDAClient()
            result = client._sda_post_sql("SELECT 1")
            # Only header row, fewer than 2 rows → returned as-is
            assert result == raw


class TestFetchSda:
    """Tests for SDAClient.fetch_sda."""

    AOI = "POLYGON((-79 35, -79 36, -78 36, -78 35, -79 35))"

    def _make_mock_response(self, body_dict):
        body = json.dumps(body_dict).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    def test_fetch_returns_table(self, SDAClient, ssurgo_module):
        # Raw JSON+COLUMNNAME format: first row = column names, rest = data
        fake_data = {
            "Table": [
                ["mukey", "mukey_int", "compname", "hydgrp", "ksat_r", "wkt"],
                [
                    "12345",
                    12345,
                    "Cecil",
                    "B",
                    "5.4",
                    "POLYGON((-79 35, -79 36, -78 36, -78 35, -79 35))",
                ],
            ]
        }
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(fake_data)
            client = SDAClient()
            result = client.fetch_sda(
                aoi_wkt=self.AOI,
                top_cm=0,
                bottom_cm=25,
                desgnmaster="A",
            )
            assert "Table" in result
            assert len(result["Table"]) == 1
            assert result["Table"][0]["mukey"] == "12345"

    def test_fetch_passes_agg_method(self, SDAClient, SoilAggMethod, ssurgo_module):
        fake_data = {"Table": [["mukey"], ["12345"]]}
        with patch.object(ssurgo_module, "urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_mock_response(fake_data)
            client = SDAClient()
            client.fetch_sda(
                aoi_wkt=self.AOI,
                top_cm=0,
                bottom_cm=25,
                agg=SoilAggMethod.WEIGHTED_COMPONENT,
            )
            # Verify the SQL posted contains weighted component keywords
            call_args = mock_urlopen.call_args
            request_obj = call_args[0][0]
            posted_body = request_obj.data.decode("utf-8")
            assert "ksat_r_comp" in posted_body


class TestSdaResponseToGeojson:
    """Test the GeoJSON FeatureCollection building logic in sda_ssurgo_query."""

    def _build_sda_response(self, num_rows=2):
        """Build a fake SDA-like JSON response."""
        rows = []
        for i in range(num_rows):
            rows.append(
                {
                    "mukey": str(10000 + i),
                    "mukey_int": 10000 + i,
                    "compname": f"Soil{i}",
                    "comppct_r": 80 - i * 5,
                    "hydgrp": ["A", "B", "C", "D"][i % 4],
                    "drainagecl": "Well drained",
                    "ksat_l": str(1.2 + i),
                    "ksat_r": str(3.6 + i),
                    "ksat_h": str(7.2 + i),
                    "wkt": (
                        f"POLYGON(({-79 - i * 0.01} 35, "
                        f"{-79 - i * 0.01} 36, "
                        f"{-78 - i * 0.01} 36, "
                        f"{-78 - i * 0.01} 35, "
                        f"{-79 - i * 0.01} 35))"
                    ),
                }
            )
        return {"Table": rows}

    def test_features_built_from_rows(self, ssurgo_module):
        """Simulate the GeoJSON building logic from sda_ssurgo_query."""
        response = self._build_sda_response(3)
        rows = response["Table"]

        features = []
        for row in rows:
            wkt = row.get("wkt")
            if not wkt:
                continue
            geom = ssurgo_module._wkt_to_geojson_geometry(wkt)
            if geom is None:
                continue
            properties = {}
            for key, val in row.items():
                if key == "wkt":
                    continue
                if val is None or val == "":
                    properties[key] = None
                else:
                    try:
                        if "." in str(val):
                            properties[key] = float(val)
                        else:
                            properties[key] = int(val)
                    except (ValueError, TypeError):
                        properties[key] = val
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": properties,
                }
            )

        assert len(features) == 3
        for feat in features:
            assert feat["type"] == "Feature"
            assert feat["geometry"]["type"] == "Polygon"
            assert "mukey" in feat["properties"]
            assert "hydgrp" in feat["properties"]
            assert isinstance(feat["properties"]["ksat_r"], float)

    def test_rows_without_wkt_skipped(self, ssurgo_module):
        """Rows missing the wkt field should be silently skipped."""
        rows = [
            {"mukey": "1", "ksat_r": "1.0"},  # no wkt
            {
                "mukey": "2",
                "ksat_r": "2.0",
                "wkt": "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
            },
        ]
        features = []
        for row in rows:
            wkt = row.get("wkt")
            if not wkt:
                continue
            geom = ssurgo_module._wkt_to_geojson_geometry(wkt)
            if geom is not None:
                features.append({"type": "Feature", "geometry": geom, "properties": {}})
        assert len(features) == 1

    def test_null_property_values(self, ssurgo_module):
        """Null / empty values should become None in properties."""
        row = {
            "mukey": "100",
            "ksat_r": "",
            "hydgrp": None,
            "wkt": "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
        }
        properties = {}
        for key, val in row.items():
            if key == "wkt":
                continue
            if val is None or val == "":
                properties[key] = None
            else:
                try:
                    if "." in str(val):
                        properties[key] = float(val)
                    else:
                        properties[key] = int(val)
                except (ValueError, TypeError):
                    properties[key] = val

        assert properties["ksat_r"] is None
        assert properties["hydgrp"] is None
        assert properties["mukey"] == 100

    def test_geojson_collection_structure(self, ssurgo_module):
        """The assembled GeoJSON should be a valid FeatureCollection."""
        response = self._build_sda_response(2)
        rows = response["Table"]

        features = []
        for row in rows:
            wkt = row.get("wkt")
            geom = ssurgo_module._wkt_to_geojson_geometry(wkt)
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {"mukey": row["mukey"]},
                }
            )

        geojson = {"type": "FeatureCollection", "features": features}

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2
        # Should be JSON-serializable
        serialized = json.dumps(geojson)
        parsed = json.loads(serialized)
        assert parsed["type"] == "FeatureCollection"

    def test_string_property_preserved(self, ssurgo_module):
        """Non-numeric string values should be kept as strings."""
        row = {
            "mukey": "100",
            "compname": "Cecil",
            "drainagecl": "Well drained",
            "wkt": "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
        }
        properties = {}
        for key, val in row.items():
            if key == "wkt":
                continue
            if val is None or val == "":
                properties[key] = None
            else:
                try:
                    if "." in str(val):
                        properties[key] = float(val)
                    else:
                        properties[key] = int(val)
                except (ValueError, TypeError):
                    properties[key] = val

        assert properties["compname"] == "Cecil"
        assert properties["drainagecl"] == "Well drained"


# ===================================================================
# Section 7 – Module-level constants
# ===================================================================


class TestConstants:
    """Tests for module-level constants."""

    def test_conversion_factor(self, ssurgo_module):
        assert ssurgo_module.MICROMETERS_PER_SECOND_TO_MM_PER_HOUR == 3.6

    def test_sda_rest_url(self, SDAClient):
        assert "sdmdataaccess" in SDAClient.REST_URL.lower()
        assert SDAClient.REST_URL.startswith("https://")
        assert SDAClient.REST_URL.endswith("post.rest")


class TestEdgeCases:
    """Various edge-case and regression tests."""

    def test_empty_sda_table_raises(self, ssurgo_module):
        """sda_ssurgo_query should call gs.fatal on empty Table."""
        with patch.object(
            ssurgo_module.SDAClient,
            "fetch_sda",
            return_value={"Table": []},
        ), patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module.sda_ssurgo_query(
                    aoi_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
                    tmp_fd=-1,
                    desgnmaster="A",
                    hzdept_r=0,
                    hzdepb_r=25,
                )

    def test_no_table_key_raises(self, ssurgo_module):
        """sda_ssurgo_query should call gs.fatal when Table key is missing."""
        with patch.object(
            ssurgo_module.SDAClient,
            "fetch_sda",
            return_value={"error": "bad query"},
        ), patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module.sda_ssurgo_query(
                    aoi_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
                    tmp_fd=-1,
                    desgnmaster="A",
                    hzdept_r=0,
                    hzdepb_r=25,
                )

    def test_none_result_raises(self, ssurgo_module):
        """sda_ssurgo_query should call gs.fatal when fetch returns None."""
        with patch.object(
            ssurgo_module.SDAClient,
            "fetch_sda",
            return_value=None,
        ), patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module.sda_ssurgo_query(
                    aoi_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
                    tmp_fd=-1,
                    desgnmaster="A",
                    hzdept_r=0,
                    hzdepb_r=25,
                )

    def test_multipolygon_with_holes(self, ssurgo_module):
        """MULTIPOLYGON with holes should parse correctly."""
        wkt = (
            "MULTIPOLYGON("
            "((0 0, 10 0, 10 10, 0 10, 0 0), (2 2, 8 2, 8 8, 2 8, 2 2)),"
            "((20 20, 30 20, 30 30, 20 30, 20 20))"
            ")"
        )
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "MultiPolygon"
        assert len(result["coordinates"]) == 2
        # First polygon has 2 rings (exterior + hole)
        assert len(result["coordinates"][0]) == 2
        # Second polygon has 1 ring
        assert len(result["coordinates"][1]) == 1

    def test_build_sql_zero_depth_range(self, SDAClient, SoilAggMethod):
        """Zero depth range (top == bottom) should not crash the SQL builder."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))",
            top_cm=10,
            bottom_cm=10,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "10.0" in sql

    def test_large_coordinate_values(self, ssurgo_module):
        """Very large coordinate values should parse correctly."""
        wkt = "POLYGON((1000000.5 2000000.5, 1000001.5 2000000.5, 1000001.5 2000001.5, 1000000.5 2000001.5, 1000000.5 2000000.5))"
        result = ssurgo_module._wkt_to_geojson_geometry(wkt)
        assert result["type"] == "Polygon"
        assert result["coordinates"][0][0] == [1000000.5, 2000000.5]

    def test_all_rows_missing_wkt_produces_empty_features(self, ssurgo_module):
        """If every row lacks a wkt, no features should be produced."""
        rows = [
            {"mukey": "1", "ksat_r": "1.0"},
            {"mukey": "2", "ksat_r": "2.0", "wkt": ""},
        ]
        features = []
        for row in rows:
            wkt = row.get("wkt")
            if not wkt:
                continue
            geom = ssurgo_module._wkt_to_geojson_geometry(wkt)
            if geom is not None:
                features.append(geom)
        assert len(features) == 0


# ===================================================================
# Section 8 – -s flag forces the SQLite/OGR backend
# ===================================================================


class TestForceSqliteFlag:
    """Tests for the -s flag in main() that forces the SQLite/OGR backend."""

    BASE_OPTIONS = {
        "ssurgo_path": "/tmp/fake.zip",
        "soils": "soils_out",
        "hydgrp": "",
        "ksat_h": "",
        "ksat_r": "",
        "ksat_l": "",
        "mukey": "",
        "sand": "",
        "silt": "",
        "clay": "",
        "bulk_density": "",
        "desgnmaster": "A",
        "hzdept_r": "0",
        "hzdepb_r": "25",
        "nprocs": "1",
        "depths": "",
    }

    def _patch_main(self, ssurgo_module, options, flags):
        """Build a context with patched module-level options/flags and the
        common helpers stubbed out so main() can run without GRASS or files.

        Returns a tuple of (duckdb_query_mock, sqlite_query_mock).
        """
        ssurgo_module.options = options
        ssurgo_module.flags = flags
        return patch.multiple(
            ssurgo_module,
            check_if_zipfile=MagicMock(return_value="/tmp/fake.zip"),
            region_to_crs_wkt=MagicMock(
                return_value="POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"
            ),
            connect_duckdb=MagicMock(return_value=MagicMock()),
            local_ssurgo_query=MagicMock(),
            local_ssurgo_sqlite_query=MagicMock(),
            write_ssurgo_to_grass=MagicMock(),
            _rasterize_and_style=MagicMock(),
        )

    def test_flag_skips_duckdb_when_duckdb_available(self, ssurgo_module):
        """With -s set, the SQLite path runs even if duckdb is importable."""
        with self._patch_main(
            ssurgo_module, dict(self.BASE_OPTIONS), {"s": True}
        ), patch.object(
            ssurgo_module, "_import_duckdb", return_value=MagicMock()
        ) as mock_import:
            ssurgo_module.main()

            # When the flag is set we must NOT even probe for duckdb.
            mock_import.assert_not_called()
            ssurgo_module.local_ssurgo_query.assert_not_called()
            ssurgo_module.local_ssurgo_sqlite_query.assert_called_once()

    def test_no_flag_uses_duckdb_when_available(self, ssurgo_module):
        """Without -s, duckdb is preferred when importable."""
        with self._patch_main(
            ssurgo_module, dict(self.BASE_OPTIONS), {"s": False}
        ), patch.object(ssurgo_module, "_import_duckdb", return_value=MagicMock()):
            ssurgo_module.main()

            ssurgo_module.local_ssurgo_query.assert_called_once()
            ssurgo_module.local_ssurgo_sqlite_query.assert_not_called()

    def test_no_flag_falls_back_to_sqlite_when_duckdb_missing(self, ssurgo_module):
        """Without -s and no duckdb, fall back to the SQLite path."""
        with self._patch_main(
            ssurgo_module, dict(self.BASE_OPTIONS), {"s": False}
        ), patch.object(ssurgo_module, "_import_duckdb", return_value=None):
            ssurgo_module.main()

            ssurgo_module.local_ssurgo_query.assert_not_called()
            ssurgo_module.local_ssurgo_sqlite_query.assert_called_once()

    def test_flag_absent_from_dict_treated_as_false(self, ssurgo_module):
        """A flags dict missing the 's' key must not raise; defaults to off."""
        with self._patch_main(ssurgo_module, dict(self.BASE_OPTIONS), {}), patch.object(
            ssurgo_module, "_import_duckdb", return_value=MagicMock()
        ):
            # Should run the duckdb branch without KeyError.
            ssurgo_module.main()
            ssurgo_module.local_ssurgo_query.assert_called_once()


# ===================================================================
# Section 9 – depth-slice (r3) support
# ===================================================================


class TestParseDepths:
    """Tests for _parse_depths."""

    def test_empty_returns_none(self, ssurgo_module):
        slices, max_depth = ssurgo_module._parse_depths("")
        assert slices is None
        assert max_depth is None

    def test_basic_slices(self, ssurgo_module):
        slices, max_depth = ssurgo_module._parse_depths("0,15,30,60,100")
        assert slices == [(0.0, 15.0), (15.0, 30.0), (30.0, 60.0), (60.0, 100.0)]
        assert max_depth == 100.0

    def test_floats_accepted(self, ssurgo_module):
        slices, max_depth = ssurgo_module._parse_depths("0,12.5,25")
        assert slices == [(0.0, 12.5), (12.5, 25.0)]
        assert max_depth == 25.0

    def test_whitespace_tolerated(self, ssurgo_module):
        slices, _ = ssurgo_module._parse_depths(" 0 , 15 , 30 ")
        assert slices == [(0.0, 15.0), (15.0, 30.0)]

    def test_single_value_fatal(self, ssurgo_module):
        with patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module._parse_depths("0")

    def test_non_increasing_fatal(self, ssurgo_module):
        with patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module._parse_depths("0,30,15")

    def test_duplicate_boundary_fatal(self, ssurgo_module):
        # Equal adjacent values produce a zero-thickness slice → reject.
        with patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module._parse_depths("0,15,15,30")

    def test_non_numeric_fatal(self, ssurgo_module):
        with patch.object(ssurgo_module.gs, "fatal", side_effect=SystemExit):
            with pytest.raises(SystemExit):
                ssurgo_module._parse_depths("0,abc,30")


class TestSlicedSqlGeneration:
    """Tests for the SDA SQL builder with slices."""

    AOI = "POLYGON((-79 35, -79 36, -78 36, -78 35, -79 35))"

    def test_single_slice_uses_unsuffixed_columns(self, SDAClient, SoilAggMethod):
        """Without slices the SQL keeps the unsuffixed (`hz.ksat_r`) form."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=100,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
        )
        assert "hz.ksat_r" in sql
        assert "ksat_r__s0" not in sql
        assert "hz_s0" not in sql

    def test_slices_produce_per_slice_columns(self, SDAClient, SoilAggMethod):
        """With slices set, the SQL projects per-slice columns and CTEs."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=100,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
            slices=[(0.0, 15.0), (15.0, 30.0), (30.0, 60.0)],
        )
        # One hz_sN CTE per slice
        for i in range(3):
            assert f"hz_s{i} AS (" in sql
        # Per-slice ksat columns appear in the outer SELECT
        for i in range(3):
            assert f"hz_s{i}.ksat_r__s{i}" in sql
        # Each slice's hz CTE gets its own LEFT JOIN
        for i in range(3):
            assert f"LEFT JOIN hz_s{i}" in sql
        # Single-slice aliases are gone
        assert "LEFT JOIN hz ON" not in sql
        assert "hz.ksat_r" not in sql

    def test_slice_thickness_bounds_in_sql(self, SDAClient, SoilAggMethod):
        """Each slice's WHERE filter must use that slice's own (top, bottom)."""
        client = SDAClient()
        sql = client._build_sda_sql(
            aoi_wkt=self.AOI,
            top_cm=0,
            bottom_cm=100,
            agg=SoilAggMethod.DOMINANT_COMPONENT,
            slices=[(0.0, 15.0), (15.0, 30.0)],
        )
        # Slice 0 filter: hzdept_r < 15.0 AND hzdepb_r > 0.0
        assert "hzdept_r < 15.0" in sql
        # Slice 1 filter: hzdept_r < 30.0 AND hzdepb_r > 15.0
        assert "hzdept_r < 30.0" in sql
        assert "hzdepb_r > 15.0" in sql


class TestHorizonSliceColumns:
    """Tests for _horizon_slice_columns."""

    def test_expansion_count(self, ssurgo_module):
        """N slices × M fields → N*M output columns."""
        slices = [(0.0, 15.0), (15.0, 30.0), (30.0, 60.0)]
        cols = ssurgo_module._horizon_slice_columns(slices)
        assert len(cols) == len(slices) * len(ssurgo_module._HORIZON_WEIGHTED_FIELDS)

    def test_naming_convention(self, ssurgo_module):
        """Column names are `<field>__s<i>`; types come from the field table."""
        slices = [(0.0, 15.0), (15.0, 30.0)]
        cols = ssurgo_module._horizon_slice_columns(slices)
        names = [n for n, _ in cols]
        # First slice: ksat_l__s0, ksat_r__s0, ...
        assert "ksat_l__s0" in names
        assert "ksat_r__s0" in names
        assert "awc_r__s0" in names
        # Second slice: same fields, __s1
        assert "ksat_l__s1" in names
        assert "claytotal_r__s1" in names
        # All types are inherited from the field definitions
        for _name, sql_type in cols:
            assert sql_type in ("REAL", "INTEGER", "TEXT")


class TestRasterizeAndStyle:
    """Tests for _rasterize_and_style.

    The helpers it calls all need a GRASS session, so they are patched out and
    the assertions are made against the resulting v.to.rast / _rasterize_3d
    calls.
    """

    def _patch(self, ssurgo_module):
        return patch.multiple(
            ssurgo_module,
            gs=MagicMock(),
            update_hydrologic_group=MagicMock(),
            _ensure_numeric_column=MagicMock(),
            hydrologic_soil_group_categories=MagicMock(),
            hydrologic_soil_group_color_scheme=MagicMock(),
            ksat_color_scheme=MagicMock(),
            _rasterize_3d=MagicMock(),
        )

    @staticmethod
    def _rasterized(ssurgo_module):
        """Map attribute_column -> kwargs for every v.to.rast call made."""
        return {
            call.kwargs["attribute_column"]: call.kwargs
            for call in ssurgo_module.gs.run_command.call_args_list
            if call.args and call.args[0] == "v.to.rast"
        }

    def test_outputs_map_to_their_source_columns(self, ssurgo_module):
        """Every requested output rasterizes from its own attribute column."""
        with self._patch(ssurgo_module):
            ssurgo_module._rasterize_and_style(
                "soils",
                hydgrp="hsg_out",
                ksat_h="",
                ksat_r="ksat_out",
                ksat_l="",
                mukey="mukey_out",
                sand="sand_out",
                silt="silt_out",
                clay="clay_out",
                bulk_density="bd_out",
            )
            rasterized = self._rasterized(ssurgo_module)

        assert rasterized["sandtotal_r"]["output"] == "sand_out"
        assert rasterized["silttotal_r"]["output"] == "silt_out"
        assert rasterized["claytotal_r"]["output"] == "clay_out"
        assert rasterized["dbthirdbar_r"]["output"] == "bd_out"
        # The outputs that predate the texture options are still produced.
        assert rasterized["hsg"]["output"] == "hsg_out"
        assert rasterized["mukey_int"]["output"] == "mukey_out"
        assert rasterized["ksat_r"]["output"] == "ksat_out"

    def test_null_attributes_are_excluded(self, ssurgo_module):
        """v.to.rast turns NULL attributes into 0, so they are filtered out."""
        with self._patch(ssurgo_module):
            ssurgo_module._rasterize_and_style(
                "soils",
                hydgrp="hsg_out",
                ksat_h="",
                ksat_r="",
                ksat_l="",
                mukey="mukey_out",
                sand="sand_out",
                bulk_density="bd_out",
            )
            rasterized = self._rasterized(ssurgo_module)

        assert rasterized
        for col, kwargs in rasterized.items():
            assert kwargs["where"] == f"{col} IS NOT NULL"

    def test_columns_recast_before_rasterizing(self, ssurgo_module):
        """All-NULL SDA columns import as TEXT, so each one is recast first."""
        with self._patch(ssurgo_module):
            ssurgo_module._rasterize_and_style(
                "soils",
                hydgrp="",
                ksat_h="",
                ksat_r="",
                ksat_l="",
                mukey="",
                sand="sand_out",
                clay="clay_out",
            )
            recast = [
                call.args[1]
                for call in ssurgo_module._ensure_numeric_column.call_args_list
            ]

        assert recast == ["sandtotal_r", "claytotal_r"]

    def test_unrequested_outputs_are_skipped(self, ssurgo_module):
        """Only the outputs the user named are produced."""
        with self._patch(ssurgo_module):
            ssurgo_module._rasterize_and_style(
                "soils",
                hydgrp="",
                ksat_h="",
                ksat_r="",
                ksat_l="",
                mukey="",
                sand="sand_out",
            )
            rasterized = self._rasterized(ssurgo_module)

        assert set(rasterized) == {"sandtotal_r"}

    def test_slices_build_3d_rasters_instead(self, ssurgo_module):
        """With depth slices the depth-weighted outputs go through the 3D path."""
        slices = [(0.0, 15.0), (15.0, 30.0)]
        with self._patch(ssurgo_module):
            ssurgo_module._rasterize_and_style(
                "soils",
                hydgrp="",
                ksat_h="",
                ksat_r="ksat_out",
                ksat_l="",
                mukey="mukey_out",
                sand="sand_out",
                bulk_density="bd_out",
                slices=slices,
            )
            rasterized = self._rasterized(ssurgo_module)
            calls_3d = {
                call.kwargs["base_field"]: call.kwargs
                for call in ssurgo_module._rasterize_3d.call_args_list
            }

        # mukey is an identity value, so it stays 2D; the rest become 3D.
        assert set(rasterized) == {"mukey_int"}
        assert set(calls_3d) == {"ksat_r", "sandtotal_r", "dbthirdbar_r"}
        assert calls_3d["sandtotal_r"]["output"] == "sand_out"
        assert calls_3d["sandtotal_r"]["slices"] == slices
        # Ksat keeps its dedicated ramp; texture and bulk density use the default.
        assert calls_3d["ksat_r"]["color_func"] is ssurgo_module.ksat_color_scheme_3d
        assert calls_3d["sandtotal_r"]["color_func"] is None
        assert calls_3d["dbthirdbar_r"]["color_func"] is None
