"""Tests for the v.gsflow.grid addon."""

# The basin is 10 x 10 cells and the grid has 3 cells of padding on every side
GRID_CELLS = (10 + 2 * 3) ** 2


def run_grid(tools):
    tools.v_gsflow_grid(
        basin="basin",
        pour_point="pp",
        raster_input="dem",
        dx=10,
        dy=10,
        output="grid",
        mask_output="mask",
        bc_cell="bc_cell",
    )


def count(tools, vector, kind):
    return tools.v_info(map=vector, flags="t", format="json")[kind]


def test_bc_cell_next_to_pour_point(grid_tools):
    """B.c. cell directly south of the pour point (read as 0-d arrays)."""
    # Slopes to the south, with a trough in the column of the pour point
    grid_tools.r_mapcalc(expression="dem = 1000 - 5 * row() + 10 * abs(col() - 16)")
    run_grid(grid_tools)

    assert count(grid_tools, "grid", "areas") == GRID_CELLS
    assert count(grid_tools, "bc_cell", "points") == 1


def test_bc_cell_diagonal_to_pour_point(grid_tools):
    """B.c. cell diagonal to the pour point (reads the basin mask of the grid)."""
    # Slopes to the south-west, so the water leaves the pour point diagonally
    grid_tools.r_mapcalc(expression="dem = 1000 - 5 * row() + 5 * col()")
    run_grid(grid_tools)

    assert count(grid_tools, "grid", "areas") == GRID_CELLS
    assert count(grid_tools, "bc_cell", "points") >= 1
