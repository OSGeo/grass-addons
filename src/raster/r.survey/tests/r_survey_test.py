"""Tests for the removal of temporary maps by r.survey."""

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


def listed(env):
    return sorted(
        gs.read_command("g.list", type="raster,vector", mapset=".", env=env).split()
    )


def test_refused_run_keeps_user_maps(user_data):
    """Maps that make the module stop are not removed by it."""
    before = listed(user_data.env)
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "r.survey",
            points="observers@PERMANENT",
            dem="dem@PERMANENT",
            output="survey",
            maxdist=50,
            obs_heigh=1.75,
            viewangle_threshold=90,
            env=user_data.env,
        )
    assert listed(user_data.env) == before
