# SPDX-FileCopyrightText: 2026 Bhuvan Somisetty
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for the r.colors.out_sld addon."""

import pytest

from grass.exceptions import CalledModuleError


def test_cell_without_categories(tools, tmp_path):
    """CELL map without category labels exports a ramp color map."""
    output = tmp_path / "cell.sld"
    tools.run("r.colors.out_sld", map="cell_map", output=output)

    content = output.read_text(encoding="utf-8")
    assert "StyledLayerDescriptor" in content
    assert "<ColorMap>" in content


def test_cell_with_categories(tools, tmp_path):
    """CELL map with category labels exports a values color map with labels."""
    output = tmp_path / "labeled.sld"
    tools.run("r.colors.out_sld", map="labeled_map", output=output)

    content = output.read_text(encoding="utf-8")
    assert 'type="values"' in content
    assert 'label="Forest"' in content
    assert 'label="Water"' in content


def test_cell_all_null(tools, tmp_path):
    """All-null CELL map, for which r.category returns nothing, does not crash."""
    output = tmp_path / "null.sld"
    tools.run("r.colors.out_sld", map="null_map", output=output)

    assert "StyledLayerDescriptor" in output.read_text(encoding="utf-8")


def test_dcell(tools, tmp_path):
    """DCELL map exports a color map."""
    output = tmp_path / "dcell.sld"
    tools.run("r.colors.out_sld", map="dcell_map", output=output)

    assert "<ColorMap>" in output.read_text(encoding="utf-8")


def test_overwrite_protection(tools, tmp_path):
    """Reusing an output file fails without --overwrite and succeeds with it."""
    output = tmp_path / "overwrite.sld"
    tools.run("r.colors.out_sld", map="cell_map", output=output)
    with pytest.raises(CalledModuleError):
        tools.run("r.colors.out_sld", map="cell_map", output=output)
    tools.run("r.colors.out_sld", map="cell_map", output=output, overwrite=True)


def test_missing_map_fails(tools, tmp_path):
    """A non-existent input map fails."""
    with pytest.raises(CalledModuleError):
        tools.run("r.colors.out_sld", map="does_not_exist", output=tmp_path / "x.sld")
