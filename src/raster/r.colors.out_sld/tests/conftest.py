# SPDX-FileCopyrightText: 2026 Bhuvan Somisetty
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later

"""Fixtures for the r.colors.out_sld tests."""

import os

import pytest

import grass.script as gs
from grass.tools import Tools


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """XY project with 10x10 CELL, DCELL, all-null CELL and labeled rasters."""
    project = tmp_path_factory.mktemp("r_colors_out_sld") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=10, s=0, e=10, w=0, res=1)
            tools.r_mapcalc(expression="cell_map = (row() - 1) * 10 + col()")
            tools.r_mapcalc(expression="dcell_map = ((row() - 1) * 10 + col()) * 1.5")
            tools.r_mapcalc(expression="null_map = null()")
            tools.r_mapcalc(expression="labeled_map = if(col() <= 5, 1, 2)")
            rules = tmp_path_factory.mktemp("rules") / "categories.txt"
            rules.write_text("1=Forest\n2=Water\n")
            tools.r_category(map="labeled_map", rules=rules, separator="=")
        yield session


@pytest.fixture
def tools(session):
    with Tools(session=session) as tools:
        yield tools
