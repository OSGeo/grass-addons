import os
import pytest
import grass.script as gs


@pytest.fixture
def setup_nlcd(tmp_path):
    """Set up a GRASS session and create NLCD land cover test raster."""
    project = tmp_path / "r_manning_project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        gs.run_command(
            "g.region",
            n=3,
            s=0,
            e=3,
            w=0,
            res=1,
            env=session.env,
        )

        # Create NLCD land cover raster
        # 11 (Open Water), 41 (Deciduous Forest), 71 (Grassland)
        # 11  41  71
        # 41  71  11
        # 71  11  41
        gs.mapcalc(
            "nlcd = "
            "if(row() == 1 && col() == 1, 11, "
            "if(row() == 1 && col() == 2, 41, "
            "if(row() == 1 && col() == 3, 71, "
            "if(row() == 2 && col() == 1, 41, "
            "if(row() == 2 && col() == 2, 71, "
            "if(row() == 2 && col() == 3, 11, "
            "if(row() == 3 && col() == 1, 71, "
            "if(row() == 3 && col() == 2, 11, 41))))))))",
            overwrite=True,
            env=session.env,
        )
        yield session


@pytest.fixture
def setup_worldcover(tmp_path):
    """Set up a GRASS session and create WorldCover land cover test raster."""
    project = tmp_path / "r_manning_wc_project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        gs.run_command(
            "g.region",
            n=3,
            s=0,
            e=3,
            w=0,
            res=1,
            env=session.env,
        )

        # Create WorldCover land cover raster
        # 10 (Tree cover), 30 (Grassland), 80 (Water)
        # 10  30  80
        # 30  80  10
        # 80  10  30
        gs.mapcalc(
            "worldcover = "
            "if(row() == 1 && col() == 1, 10, "
            "if(row() == 1 && col() == 2, 30, "
            "if(row() == 1 && col() == 3, 80, "
            "if(row() == 2 && col() == 1, 30, "
            "if(row() == 2 && col() == 2, 80, "
            "if(row() == 2 && col() == 3, 10, "
            "if(row() == 3 && col() == 1, 80, "
            "if(row() == 3 && col() == 2, 10, 30))))))))",
            overwrite=True,
            env=session.env,
        )
        yield session


def get_cell_value(raster, row, col, env):
    """Get the value of a specific cell in a raster."""
    result = gs.read_command(
        "r.what",
        map=raster,
        coordinates=(col + 0.5, 3 - row - 0.5),
        env=env,
    )
    value = result.strip().split("|")[-1]
    return float(value) if value != "*" else None


def test_nlcd_kalyanapu_medium(setup_nlcd):
    """Test NLCD with Kalyanapu source and medium method."""
    session = setup_nlcd
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="nlcd",
        source="kalyanapu",
        method="medium",
        env=session.env,
    )

    # Expected values from NLCD_KALYANAPU (medium index)
    # 11 (Open Water): 0.040
    # 41 (Deciduous Forest): 0.360
    # 71 (Grassland): 0.368
    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.040)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.360)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.368)


def test_nlcd_kalyanapu_low(setup_nlcd):
    """Test NLCD with Kalyanapu source and low method."""
    session = setup_nlcd
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="nlcd",
        source="kalyanapu",
        method="low",
        env=session.env,
    )

    # Expected values from NLCD_KALYANAPU (low index)
    # 11 (Open Water): 0.025
    # 41 (Deciduous Forest): 0.270
    # 71 (Grassland): 0.280
    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.025)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.270)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.280)


def test_nlcd_kalyanapu_high(setup_nlcd):
    """Test NLCD with Kalyanapu source and high method."""
    session = setup_nlcd
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="nlcd",
        source="kalyanapu",
        method="high",
        env=session.env,
    )

    # Expected values from NLCD_KALYANAPU (high index)
    # 11 (Open Water): 0.050
    # 41 (Deciduous Forest): 0.480
    # 71 (Grassland): 0.490
    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.050)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.480)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.490)


def test_nlcd_hecras_medium(setup_nlcd):
    """Test NLCD with HEC-RAS source and medium method."""
    session = setup_nlcd
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="nlcd",
        source="hecras",
        method="medium",
        env=session.env,
    )

    # Expected values from NLCD_HECRAS (medium index)
    # 11 (Open Water): 0.035
    # 41 (Deciduous Forest): 0.140
    # 71 (Grassland): 0.035
    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.035)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.140)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.035)


def test_worldcover_medium(setup_worldcover):
    """Test WorldCover with medium method."""
    session = setup_worldcover
    gs.run_command(
        "r.manning",
        input="worldcover",
        output="mannings_n",
        landcover="worldcover",
        method="medium",
        env=session.env,
    )

    # Expected values from WORLDCOVER_AZZAM (medium index)
    # 10 (Tree cover): 0.094
    # 30 (Grassland): 0.033
    # 80 (Water): 0.035
    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.094)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.033)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.035)


def test_nlcd_kalyanapu_random(setup_nlcd):
    """Test NLCD with Kalyanapu source and random method."""
    session = setup_nlcd
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="nlcd",
        source="kalyanapu",
        method="random",
        seed=42,
        env=session.env,
    )

    # Check values are within expected ranges
    # 11 (Open Water): [0.025, 0.050]
    # 41 (Deciduous Forest): [0.270, 0.480]
    # 71 (Grassland): [0.280, 0.490]
    water = get_cell_value("mannings_n", 0, 0, session.env)
    forest = get_cell_value("mannings_n", 0, 1, session.env)
    grass = get_cell_value("mannings_n", 0, 2, session.env)

    assert 0.025 <= water <= 0.050
    assert 0.270 <= forest <= 0.480
    assert 0.280 <= grass <= 0.490


def test_custom_rules_single_value(setup_nlcd, tmp_path):
    """Test custom rules file with single values."""
    session = setup_nlcd

    # Create custom rules file
    rules_file = tmp_path / "rules.csv"
    rules_file.write_text("# code,n\n11,0.05\n41,0.25\n71,0.15\n")

    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n",
        landcover="custom",
        rules=str(rules_file),
        method="medium",
        env=session.env,
    )

    assert get_cell_value("mannings_n", 0, 0, session.env) == pytest.approx(0.05)
    assert get_cell_value("mannings_n", 0, 1, session.env) == pytest.approx(0.25)
    assert get_cell_value("mannings_n", 0, 2, session.env) == pytest.approx(0.15)


def test_custom_rules_three_values(setup_nlcd, tmp_path):
    """Test custom rules file with low/medium/high values."""
    session = setup_nlcd

    # Create custom rules file with three values
    rules_file = tmp_path / "rules.csv"
    rules_file.write_text(
        "# code,n_low,n_medium,n_high\n"
        "11,0.01,0.05,0.10\n"
        "41,0.15,0.25,0.35\n"
        "71,0.10,0.15,0.20\n"
    )

    # Test low
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n_low",
        landcover="custom",
        rules=str(rules_file),
        method="low",
        env=session.env,
    )
    assert get_cell_value("mannings_n_low", 0, 0, session.env) == pytest.approx(0.01)

    # Test medium
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n_med",
        landcover="custom",
        rules=str(rules_file),
        method="medium",
        env=session.env,
    )
    assert get_cell_value("mannings_n_med", 0, 0, session.env) == pytest.approx(0.05)

    # Test high
    gs.run_command(
        "r.manning",
        input="nlcd",
        output="mannings_n_high",
        landcover="custom",
        rules=str(rules_file),
        method="high",
        env=session.env,
    )
    assert get_cell_value("mannings_n_high", 0, 0, session.env) == pytest.approx(0.10)
