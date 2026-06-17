import grass.script as gs


def _univar(name, env):
    return gs.parse_command("r.univar", map=name, format="json", env=env)


def _exists(name, env):
    return bool(gs.find_file(name, element="raster", env=env)["name"])


def test_global_lod_uniform_and_positive(session):
    env = session.env
    gs.run_command(
        "r.dem.lod",
        dem="dem_post",
        reference="dem_pre",
        output="lod_global",
        method="global",
        confidence=0.95,
        stable_mask="stable",
        env=env,
    )
    stats = _univar("lod_global", env)
    # Uniform raster: min == max, and strictly positive.
    assert float(stats["min"]) > 0.0
    assert abs(float(stats["max"]) - float(stats["min"])) < 1e-9


def test_global_lod_with_precomputed_nmad(session):
    env = session.env
    gs.run_command(
        "r.dem.lod",
        dem="dem_post",
        reference="dem_pre",
        output="lod_nmad",
        method="global",
        confidence=0.95,
        nmad=0.2,
        overwrite=True,
        env=env,
    )
    stats = _univar("lod_nmad", env)
    # LoD = 1.95996 * sqrt(2) * (0.2 / 1.4826) ~= 0.374 m, uniform.
    assert abs(float(stats["min"]) - 0.3739) < 1e-2


def test_local_lod_spatially_variable(session):
    env = session.env
    gs.run_command(
        "r.dem.lod",
        dem="dem_post",
        reference="dem_pre",
        output="lod_local",
        method="local",
        window=15,
        confidence=0.95,
        stable_mask="stable",
        overwrite=True,
        env=env,
    )
    assert _exists("lod_local", env)
    stats = _univar("lod_local", env)
    # Local LoD varies across space and stays non-negative.
    assert float(stats["min"]) >= 0.0
    assert float(stats["max"]) > float(stats["min"])


def test_higher_confidence_raises_lod(session):
    env = session.env
    gs.run_command(
        "r.dem.lod",
        dem="dem_post",
        reference="dem_pre",
        output="lod_68",
        method="global",
        confidence=0.68,
        nmad=0.2,
        overwrite=True,
        env=env,
    )
    lod68 = float(_univar("lod_68", env)["min"])
    lod95 = float(_univar("lod_nmad", env)["min"])
    assert lod95 > lod68
