"""Tests for r.out.3mf."""

import re
import zipfile

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


def _max_vertex_z(model_xml):
    """Return the maximum Z value from serialized 3MF model XML."""
    z_values = [float(value) for value in re.findall(r' z="([^"]+)"', model_xml)]
    return max(z_values)


def test_export_creates_valid_3mf_package(dem_session, tmp_path):
    """The module should produce a readable 3MF ZIP with mesh content."""
    output_path = tmp_path / "terrain.3mf"
    gs.run_command(
        "r.out.3mf",
        input=dem_session.name,
        output=str(output_path),
        size=80,
        resolution=4,
        zscale=2,
        base_height=2,
        overwrite=True,
        env=dem_session.session.env,
    )
    assert output_path.exists()

    with zipfile.ZipFile(output_path) as zip_file:
        members = zip_file.namelist()
        assert "[Content_Types].xml" in members
        assert "_rels/.rels" in members
        assert "3D/3dmodel.model" in members

        model_xml = zip_file.read("3D/3dmodel.model").decode("utf-8")
        assert "<vertices>" in model_xml
        assert "<triangles>" in model_xml
        assert model_xml.count("<vertex ") > 0
        assert model_xml.count("<triangle ") > 0


def test_normalize_flag_changes_z_scale(dem_session, tmp_path):
    """The -n flag should produce a different vertical scale than the default."""
    plain_path = tmp_path / "plain.3mf"
    norm_path = tmp_path / "norm.3mf"

    common = {
        "input": dem_session.name,
        "size": 60,
        "resolution": 6,
        "zscale": 10,
        "base_height": 2,
        "overwrite": True,
    }
    env = dem_session.session.env
    gs.run_command("r.out.3mf", output=str(plain_path), env=env, **common)
    gs.run_command("r.out.3mf", output=str(norm_path), flags="n", env=env, **common)

    with zipfile.ZipFile(plain_path) as plain_zip:
        plain_xml = plain_zip.read("3D/3dmodel.model").decode("utf-8")
    with zipfile.ZipFile(norm_path) as norm_zip:
        norm_xml = norm_zip.read("3D/3dmodel.model").decode("utf-8")

    # The two modes use different vertical-scale formulas (geographic-true vs.
    # zscale-as-mm-of-relief), so the resulting heights should differ.
    assert abs(_max_vertex_z(plain_xml) - _max_vertex_z(norm_xml)) > 1.0


def test_full_raster_flag(dem_session, tmp_path):
    """The -r flag should export the full raster and produce a valid 3MF."""
    output_path = tmp_path / "full.3mf"
    gs.run_command(
        "r.out.3mf",
        input=dem_session.name,
        output=str(output_path),
        flags="r",
        size=80,
        resolution=4,
        overwrite=True,
        env=dem_session.session.env,
    )
    assert output_path.exists()

    with zipfile.ZipFile(output_path) as zip_file:
        model_xml = zip_file.read("3D/3dmodel.model").decode("utf-8")
        assert model_xml.count("<vertex ") > 0
        assert model_xml.count("<triangle ") > 0


def test_overwrite_protection(dem_session, tmp_path):
    """Writing over an existing file should require overwrite=True.

    The output name is given without an extension so the module's own
    post-rewrite check is exercised, not just the parser's check on the
    typed name.
    """
    typed = tmp_path / "guard"
    written = tmp_path / "guard.3mf"
    common = {
        "input": dem_session.name,
        "output": str(typed),
        "size": 50,
        "resolution": 6,
    }
    env = dem_session.session.env
    gs.run_command("r.out.3mf", overwrite=True, env=env, **common)
    assert written.exists()

    # Second run without overwrite must fail rather than clobber the file.
    with pytest.raises(CalledModuleError):
        gs.run_command("r.out.3mf", env=env, **common)

    # With overwrite it should succeed again.
    gs.run_command("r.out.3mf", overwrite=True, env=env, **common)


def test_stl_output_is_binary_geometry(dem_session, tmp_path):
    """STL output should be a binary STL whose triangle count matches its size."""
    output_path = tmp_path / "terrain.stl"
    gs.run_command(
        "r.out.3mf",
        input=dem_session.name,
        output=str(output_path),
        format="stl",
        size=50,
        resolution=4,
        overwrite=True,
        env=dem_session.session.env,
    )
    assert output_path.exists()

    data = output_path.read_bytes()
    n_tris = int.from_bytes(data[80:84], "little")
    assert n_tris > 0
    # 80-byte header + 4-byte count + 50 bytes per triangle.
    assert len(data) == 84 + n_tris * 50
