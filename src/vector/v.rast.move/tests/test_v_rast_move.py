"""Test v.rast.move"""

import pytest

import grass.script as gs


def test_displacement_result(line_dataset):
    """Check geometry of the result"""
    result = "result"
    gs.run_command(
        "v.rast.move",
        input=line_dataset.name,
        x_raster=line_dataset.x,
        y_raster=line_dataset.y,
        output=result,
    )
    old_metadata = gs.vector_info(line_dataset.name)
    metadata = gs.vector_info(result)

    for item in ["lines", "nodes"]:
        assert old_metadata[item] == metadata[item]
    assert metadata["north"] < line_dataset.y_value + 1
    assert metadata["south"] > line_dataset.y_value
    assert metadata["west"] > line_dataset.x_value
    assert metadata["east"] < line_dataset.x_value + 1


@pytest.mark.parametrize("nulls", ["zeros", "warning", "error"])
def test_null_options_accepted(line_dataset, nulls):
    """Check that all values for the nulls option are accepted"""
    result = f"result_nulls_{nulls}"
    gs.run_command(
        "v.rast.move",
        input=line_dataset.name,
        x_raster=line_dataset.x,
        y_raster=line_dataset.y,
        output=result,
        nulls=nulls,
    )


def test_nulls_as_zeros(line_dataset):
    """Check that transforming nulls to zeros works"""
    result = "result_zeros"
    gs.run_command(
        "v.rast.move",
        input=line_dataset.name,
        x_raster=line_dataset.nulls,
        y_raster=line_dataset.nulls,
        output=result,
        nulls="zeros",
    )
    old_metadata = gs.vector_info(line_dataset.name)
    metadata = gs.vector_info(result)

    for item in ["lines", "nodes", "north", "south", "east", "west"]:
        assert old_metadata[item] == metadata[item], item


def test_nulls_fail(line_dataset):
    """Check that an error is generated for nulls"""
    result = "result_fails"
    with pytest.raises(gs.CalledModuleError):
        gs.run_command(
            "v.rast.move",
            input=line_dataset.name,
            x_raster=line_dataset.nulls,
            y_raster=line_dataset.nulls,
            output=result,
            nulls="error",
        )
