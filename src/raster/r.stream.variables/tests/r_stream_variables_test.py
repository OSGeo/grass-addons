"""Tests for the removal of temporary mapsets by r.stream.variables.

The module used to run rm -fr on every mapset whose name started with
sub_stream or sub_watershed, which deleted user mapsets such as sub_streams.
"""

import subprocess

import pytest

import grass.script as gs


@pytest.mark.parametrize(
    ("area", "user_mapset"),
    [("stream", "sub_streams"), ("watershed", "sub_watersheds")],
)
def test_user_mapset_is_not_deleted(variables, area, user_mapset):
    """Only temporary mapsets of the module are removed, not user mapsets."""
    folder = variables.path / "folder_structure"
    folder.mkdir()

    # Only the removal of mapsets is tested here, not the aggregation,
    # so the run fails later on the empty folder structure.
    process = gs.start_command(
        "r.stream.variables",
        variable="elevation",
        area=area,
        output="mean",
        folder=str(folder),
        out_folder=str(variables.path / "output"),
        cwd=variables.path,
        env=variables.env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process.wait()

    assert (variables.project / user_mapset / "cell" / "user_map").exists()
    assert not (variables.project / f"sub_{area}ID5").exists()
