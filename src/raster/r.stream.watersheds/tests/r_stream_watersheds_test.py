"""Tests for handling of the output folder of r.stream.watersheds.

The module used to run rm -fr on the unquoted folder option, which deleted
an existing directory given by the user and, for a path containing a space,
unrelated directories.
"""

import subprocess

import grass.script as gs

NOT_EMPTY_ERROR = "is not empty"


def run_module(watersheds, folder, **kwargs):
    """Run the module from the temporary directory

    :return: return code and standard error output of the module
    """
    process = gs.start_command(
        "r.stream.watersheds",
        drainage="drainage",
        stream="streams",
        folder=str(folder),
        cwd=watersheds.path,
        env=watersheds.env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        **kwargs,
    )
    _, stderr = process.communicate()
    return process.returncode, stderr


def test_non_empty_folder_is_not_deleted(watersheds):
    """An existing non-empty folder is refused and kept without --overwrite."""
    folder = watersheds.path / "project_data"
    folder.mkdir()
    user_file = folder / "plots.csv"
    user_file.write_text("user data")

    returncode, stderr = run_module(watersheds, folder)

    assert returncode != 0
    assert NOT_EMPTY_ERROR in stderr
    assert user_file.read_text() == "user data"


def test_folder_with_space_does_not_touch_other_paths(watersheds):
    """A path with a space is used as one path, not split into several."""
    other_dir = watersheds.path / "My"
    other_dir.mkdir()
    other_file = other_dir / "thesis.tex"
    other_file.write_text("unrelated")
    folder = watersheds.path / "My Data" / "ws"
    folder.mkdir(parents=True)
    user_file = folder / "notes.txt"
    user_file.write_text("user data")

    returncode, stderr = run_module(watersheds, folder)

    assert returncode != 0
    assert NOT_EMPTY_ERROR in stderr
    assert other_file.read_text() == "unrelated"
    assert user_file.read_text() == "user data"


def test_overwrite_keeps_files_not_created_by_module(watersheds):
    """With --overwrite, only outputs of a previous run are replaced."""
    folder = watersheds.path / "results"
    folder.mkdir()
    user_file = folder / "notes.txt"
    user_file.write_text("user data")
    previous_output = folder / "stream_coord.txt"
    previous_output.write_text("previous run")

    # Only the handling of the folder is tested here, not the delineation.
    _, stderr = run_module(watersheds, folder, overwrite=True)

    assert NOT_EMPTY_ERROR not in stderr
    assert user_file.read_text() == "user data"
    assert not previous_output.exists() or previous_output.read_text() != "previous run"
