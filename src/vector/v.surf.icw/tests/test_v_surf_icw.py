"""Comprehensive tests for the v.surf.icw addon."""

import pytest
from grass.exceptions import CalledModuleError


def test_icw_interpolation_accuracy(icw):
    """Test that v.surf.icw interpolates values correctly under a uniform cost.

    Under a uniform cost surface of 1:
    - The interpolated value at the seed points should be extremely close to their original values (10.0 and 100.0).
    - The value at any symmetric equidistant cell (e.g., 25, 75) should be exactly the midpoint (55.0).
    """
    tools = icw.tools
    output_map = "icw_uniform"

    # Run the interpolation
    tools.v_surf_icw(
        input="seed_points",
        column="val",
        cost_map="cost_raster",
        output=output_map,
        friction=2.0,
    )

    # 1. Verify general statistics
    stats = tools.r_univar(map=output_map, format="json")

    assert stats["min"] == pytest.approx(10.0, abs=1e-1)
    assert stats["max"] == pytest.approx(100.0, abs=1e-1)

    # 2. Verify values at exact seed locations (due to the cleansed 0.1 division anomaly bypass)
    # At (25, 25), value should be 10.0
    val_at_p1 = float(
        tools.r_what(map=output_map, coordinates="25,25").stdout.strip().split("|")[-1]
    )
    assert val_at_p1 == pytest.approx(10.0, abs=1e-1)

    # At (75, 75), value should be 100.0
    val_at_p2 = float(
        tools.r_what(map=output_map, coordinates="75,75").stdout.strip().split("|")[-1]
    )
    assert val_at_p2 == pytest.approx(100.0, abs=1e-1)

    # 3. Verify value at a symmetric, equidistant location (25, 75)
    # Distance to both (25, 25) and (75, 75) is exactly 50 meters, meaning weights are identical.
    # Midpoint of 10.0 and 100.0 is 55.0.
    val_mid = float(
        tools.r_what(map=output_map, coordinates="25,75").stdout.strip().split("|")[-1]
    )
    assert val_mid == pytest.approx(55.0, abs=1e-1)


def test_icw_radial_basis_function(icw):
    """Test the radial basis function flag (-r) runs cleanly and produces output."""
    tools = icw.tools
    output_map = "icw_radial"

    tools.v_surf_icw(
        flags="r",
        input="seed_points",
        column="val",
        cost_map="cost_raster",
        output=output_map,
        friction=2.0,
    )

    # Check that the raster has non-null stats and valid scale
    stats = tools.r_univar(map=output_map, format="json")
    assert stats["n"] > 0
    assert stats["max"] > stats["min"]


@pytest.mark.parametrize("friction_val", [1.0, 3.0, 4.0])
def test_icw_friction_parameters(icw, friction_val):
    """Test that different friction (power 'n') values calculate cleanly."""
    tools = icw.tools
    output_map = f"icw_friction_{int(friction_val)}"

    tools.v_surf_icw(
        input="seed_points",
        column="val",
        cost_map="cost_raster",
        output=output_map,
        friction=friction_val,
    )

    stats = tools.r_univar(map=output_map, format="json")
    assert stats["n"] > 0


def test_nonexistent_column_raises_error(icw):
    """Passing a column name that does not exist should fail."""
    tools = icw.tools
    with pytest.raises(CalledModuleError):
        tools.v_surf_icw(
            input="seed_points",
            column="nonexistent_column",
            cost_map="cost_raster",
            output="icw_fail_col",
        )


def test_post_mask_failure_with_preexisting_mask(icw):
    """Using the post_mask option when a MASK already exists must fail.

    This asserts that the module guardrail exits cleanly before executing calculations.
    """
    tools = icw.tools

    # Create an actual MASK raster in the current environment
    tools.r_mapcalc(expression="MASK = 1")
    # Create another map to pass to the post_mask option
    tools.r_mapcalc(expression="my_post_mask = 1")

    with pytest.raises(CalledModuleError):
        tools.v_surf_icw(
            input="seed_points",
            column="val",
            cost_map="cost_raster",
            post_mask="my_post_mask",
            output="icw_fail_mask",
        )


def test_overwrite_protection(icw):
    """Reusing an output name without --overwrite fails."""
    tools = icw.tools
    output_map = "icw_overwrite"

    tools.v_surf_icw(
        input="seed_points",
        column="val",
        cost_map="cost_raster",
        output=output_map,
    )

    with pytest.raises(CalledModuleError):
        # Try writing to the same raster name without using --overwrite
        tools.v_surf_icw(
            input="seed_points",
            column="val",
            cost_map="cost_raster",
            output=output_map,
        )
