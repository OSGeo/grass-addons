import grass.script as gs


def _classes(name, env):
    """Return the set of integer classes present in a raster."""
    raw = gs.read_command(
        "r.stats", input=name, flags="n", separator=",", env=env
    ).strip()
    return {int(line.split(",")[0]) for line in raw.splitlines() if line.strip()}


def test_triage_topo_only(session):
    env = session.env
    gs.run_command(
        "r.dem.screen",
        dod="dod",
        output="triage_topo",
        topo_threshold=1.0,
        env=env,
    )
    # No spectral input: only no-change (0) and topographic (2) classes.
    assert _classes("triage_topo", env) == {0, 2}


def test_triage_topo_and_spectral(session):
    env = session.env
    gs.run_command(
        "r.dem.screen",
        dod="dod",
        spectral_change="ndvi_change",
        output="triage_full",
        topo_threshold=1.0,
        spectral_threshold=-0.15,
        overwrite=True,
        env=env,
    )
    # All four priority classes occur given the orthogonal change halves.
    assert _classes("triage_full", env) == {0, 1, 2, 3}


def test_hazard_overlay_flags_critical(session):
    env = session.env
    gs.run_command(
        "r.dem.screen",
        dod="dod",
        spectral_change="ndvi_change",
        output="triage_h",
        infrastructure="infra",
        hazard_output="hazard",
        infra_buffer_m=5,
        overwrite=True,
        env=env,
    )
    classes = _classes("hazard", env)
    # Critical class 3 (change intersecting infrastructure) must be present.
    assert 3 in classes
    assert classes <= {0, 1, 2, 3}
