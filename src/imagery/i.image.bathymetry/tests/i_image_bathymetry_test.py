"""Tests for the removal of temporary maps by i.image.bathymetry."""

import subprocess

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


def listed(env):
    return sorted(
        gs.read_command(
            "g.list", type="raster,vector,region,group", mapset=".", env=env
        ).split()
    )


def test_interface_description_keeps_user_data(user_data):
    """Printing the interface (as the GUI dialog does) removes nothing."""
    before = listed(user_data.env)
    subprocess.run(
        ["i.image.bathymetry", "--interface-description"],
        env=user_data.env,
        capture_output=True,
        check=True,
    )
    assert listed(user_data.env) == before


def test_failed_run_keeps_user_data(user_data):
    """A run failing on a misspelled column removes no user data."""
    before = listed(user_data.env)
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "i.image.bathymetry",
            green_band="band@PERMANENT",
            red_band="band@PERMANENT",
            nir_band="band@PERMANENT",
            band_for_correction="band@PERMANENT",
            calibration_points="tmp_points",
            calibration_column="depht",
            depth_estimate="depth",
            env=user_data.env,
        )
    assert listed(user_data.env) == before
