"""Comprehensive tests for the r.surf.volcano addon."""

import pytest
from grass.exceptions import CalledModuleError

# Reference values for the standard Gaussian method (from the original shell test)
REF_MAX = 1000.0
REF_MEAN = 31.3
REF_STDDEV = 121.1

# Tolerance threshold (corresponds to var=5 in the original shell script)
TOLERANCE = 5.0


def parse_key_value(text):
    """Helper to parse shell-style key-value output (e.g., r.info -g or r.univar -g)."""
    result = {}
    for line in text.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            try:
                result[key.strip()] = float(val)
            except ValueError:
                result[key.strip()] = val.strip()
    return result


def test_gaussian_method_statistics(volcano):
    """Test that r.surf.volcano with the gaussian method generates correct raster stats."""
    tools = volcano.tools
    output_map = "volcano_gauss"

    # Run the module
    tools.r_surf_volcano(method="gaussian", output=output_map)

    # Calculate statistics
    univar_out = tools.r_univar(map=output_map, flags="g").stdout
    stats = parse_key_value(univar_out)

    # Assertions with tolerance
    assert stats["max"] == pytest.approx(REF_MAX, abs=TOLERANCE)
    assert stats["mean"] == pytest.approx(REF_MEAN, abs=TOLERANCE)
    assert stats["stddev"] == pytest.approx(REF_STDDEV, abs=TOLERANCE)


def test_crater_depth_math(volcano):
    """Test that setting a crater correctly inverts the peak mathematically.

    Formula in the source code: if(vs > pk, 2*pk - vs, vs)
    At the exact center (2560, 2560), the expected height with peak=1000 and crater=200
    is exactly peak - crater = 800.
    """
    tools = volcano.tools
    output_map = "volcano_crater"
    peak = 1000.0
    crater = 200.0

    # Generate a volcano with a crater using the default polynomial method
    tools.r_surf_volcano(
        output=output_map, peak=peak, crater=crater, method="polynomial"
    )

    # Query the cell value at the exact center of the region (2560, 2560)
    # Typical r.what output format: "2560|2560||800"
    rwhat_out = tools.r_what(map=output_map, coordinates="2560,2560").stdout
    cell_value = float(rwhat_out.strip().split("|")[-1])

    # The center of the crater must match peak - crater (800)
    assert cell_value == pytest.approx(peak - crater, abs=20.0)


@pytest.mark.parametrize(
    "method", ["polynomial", "lorentzian", "exponential", "logarithmic"]
)
def test_all_mathematical_methods(volcano, method):
    """Test that all mathematical methods run cleanly and produce valid raster maps."""
    tools = volcano.tools
    output_map = f"volcano_{method}"

    # Execute the module for each supported method found in the code
    tools.r_surf_volcano(method=method, output=output_map)

    # Verify that the raster was successfully created and contains valid data
    univar_out = tools.r_univar(map=output_map, flags="g").stdout
    stats = parse_key_value(univar_out)

    assert stats["n"] > 0
    assert stats["max"] > 0


def test_surface_roughness_flag(volcano):
    """Test that the -r (roughen) flag modifies the surface statistics."""
    tools = volcano.tools
    smooth_map = "volcano_smooth"
    rough_map = "volcano_rough"

    # Generate a smooth volcano
    tools.r_surf_volcano(output=smooth_map, peak=1000)
    smooth_stats = parse_key_value(tools.r_univar(map=smooth_map, flags="g").stdout)

    # Generate the same volcano with the roughness flag '-r' and sigma=5
    tools.r_surf_volcano(flags="r", output=rough_map, peak=1000, sigma=5.0)
    rough_stats = parse_key_value(tools.r_univar(map=rough_map, flags="g").stdout)

    # Due to the random noise injected by r.surf.gauss,
    # the standard deviation and maximum values of the two maps must differ.
    assert rough_stats["stddev"] != pytest.approx(smooth_stats["stddev"], abs=1e-4)
    assert rough_stats["max"] != pytest.approx(smooth_stats["max"], abs=1e-4)


def test_metadata_generation(volcano):
    """Test that r.support metadata (title, description) is correctly written."""
    tools = volcano.tools
    output_map = "volcano_metadata"

    tools.r_surf_volcano(method="gaussian", output=output_map, peak=1200)

    # Retrieve metadata using r.info with the shell-style '-g' flag
    rinfo_out = tools.r_info(map=output_map, flags="e", format="json")

    # Verify the title field populated by r.support in the source code
    expected_title = "Artificial surface resembling a seamount or cone volcano"
    assert rinfo_out["title"] == expected_title


def test_overwrite_protection(volcano):
    """Reusing an output name without --overwrite fails."""
    tools = volcano.tools
    output_map = "volcano_overwrite"

    tools.r_surf_volcano(method="gaussian", output=output_map)
    with pytest.raises(CalledModuleError):
        # Must fail when trying to write to the same raster without --overwrite
        tools.r_surf_volcano(method="gaussian", output=output_map)
