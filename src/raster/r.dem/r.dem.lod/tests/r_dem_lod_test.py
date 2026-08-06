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


def test_global_lod_tracks_injected_noise(session):
    """Estimated NMAD must follow the injected sigma=0.2 noise.

    Guards against the median silently missing from r.univar output, which
    made the estimate a data-independent constant (NMAD = 1.4826).
    """
    env = session.env
    gs.run_command(
        "r.dem.lod",
        dem="dem_post",
        reference="dem_pre",
        output="lod_est",
        method="global",
        confidence=0.95,
        stable_mask="stable",
        overwrite=True,
        env=env,
    )
    lod = float(_univar("lod_est", env)["min"])
    # LoD = z * NMAD with NMAD ~= 0.2 => ~0.392 m; bounds tight enough to
    # reject both the old sqrt(2) inflation (0.554) and the old /1.4826
    # deflation (0.374 with precomputed values).
    assert 0.30 < lod < 0.47


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
    # LoD = z * NMAD = 1.95996 * 0.2 ~= 0.392 m, uniform.
    assert abs(float(stats["min"]) - 0.39199) < 1e-3


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


def test_global_paths_identical(session):
    """Global LoD from dod= equals the dem+reference value (same residuals,
    same NMAD, one convention)."""
    import re
    import subprocess

    env = session.env
    gs.run_command(
        "r.mapcalc",
        expression="dod_pre = dem_post - dem_pre",
        overwrite=True,
        env=env,
    )
    vals = {}
    for tag, kwargs in (
        ("legacy", dict(dem="dem_post", reference="dem_pre")),
        ("dodpath", dict(dod="dod_pre")),
    ):
        proc = gs.start_command(
            "r.dem.lod",
            output=f"lod_g_{tag}",
            method="global",
            confidence=0.95,
            stable_mask="stable",
            overwrite=True,
            env=env,
            stderr=subprocess.PIPE,
            **kwargs,
        )
        _, err = proc.communicate()
        if isinstance(err, bytes):
            err = err.decode()
        assert proc.returncode == 0, err
        m = re.search(r"LoD:\s+([0-9.]+) m", err)
        assert m, err
        vals[tag] = float(m.group(1))
    assert abs(vals["legacy"] / vals["dodpath"] - 1.0) < 1e-6


def test_coverage_restricted_to_observed(session):
    """A holey DoD yields an LoD restricted to observed cells: no detection
    limit over unobserved terrain, coverage at most 100%."""
    env = session.env
    gs.run_command(
        "r.mapcalc",
        expression="dod_pre = dem_post - dem_pre",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression="dod_holey = if(col() > 80, null(), dod_pre)",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.dem.lod",
        dod="dod_holey",
        output="lod_holey",
        method="local",
        window=11,
        stable_mask="stable",
        overwrite=True,
        env=env,
    )
    n_obs = int(
        gs.parse_command("r.univar", map="dod_holey", format="json", env=env)["n"]
    )
    n_lod = int(
        gs.parse_command("r.univar", map="lod_holey", format="json", env=env)["n"]
    )
    assert n_lod <= n_obs
    # A probe inside the hole must be NULL despite window dilation.
    out = gs.read_command(
        "r.what", map="lod_holey", coordinates="85.5,50.5", env=env
    )
    assert "*" in out


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


def test_input_paths_identical(session):
    """LoD from dod= equals the dem+reference LoD exactly: both paths
    difference the surfaces before windowing, so no epoch factor differs."""
    env = session.env
    gs.run_command(
        "r.mapcalc",
        expression="dod_pre = dem_post - dem_pre",
        overwrite=True,
        env=env,
    )
    common = dict(
        method="local", window=11, confidence=0.95,
        stable_mask="stable", overwrite=True, env=env,
    )
    gs.run_command(
        "r.dem.lod", dem="dem_post", reference="dem_pre",
        output="lod_legacy", **common,
    )
    gs.run_command("r.dem.lod", dod="dod_pre", output="lod_dod", **common)
    gs.run_command(
        "r.mapcalc",
        expression="lod_ratio = lod_legacy / lod_dod",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="lod_ratio", format="json", env=env)
    assert abs(float(stats["min"]) - 1.0) < 1e-9
    assert abs(float(stats["max"]) - 1.0) < 1e-9


def test_floor_sigma_output_and_z_relation(session):
    """output = z * output_sigma cellwise, and sigma never falls below floor."""
    from scipy.stats import norm

    env = session.env
    gs.run_command(
        "r.mapcalc",
        expression="dod_pre = dem_post - dem_pre",
        overwrite=True,
        env=env,
    )
    floor = 5.0  # far above the 0.2 m noise: s_long ~= floor
    gs.run_command(
        "r.dem.lod",
        dod="dod_pre",
        output="lod_fl",
        output_sigma="sigma_fl",
        method="local",
        window=11,
        confidence=0.95,
        stable_mask="stable",
        floor=floor,
        overwrite=True,
        env=env,
    )
    z = float(norm.ppf((1 + 0.95) / 2))
    gs.run_command(
        "r.mapcalc",
        expression=f"zdiff = abs(lod_fl - {z} * sigma_fl)",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="zdiff", format="json", env=env)
    assert float(stats["max"]) < 1e-6
    sig = gs.parse_command("r.univar", map="sigma_fl", format="json", env=env)
    # Two-scale decomposition: sigma >= s_long = sqrt(floor^2 - med(sigma_win^2)),
    # which is within a hair of the floor when the floor dwarfs the noise.
    assert float(sig["min"]) >= floor * 0.99
    # And it must NOT be the double-counting quadrature sqrt(win^2 + floor^2)
    # everywhere: max stays close to the floor too.
    assert float(sig["max"]) < floor * 1.05


def test_domain_not_extended(session):
    """Beyond the window's reach of stable cells the LoD stays NULL, and the
    domain raster flags exactly the defined cells."""
    env = session.env
    # Stable cells only in the far west; the east half is out of reach.
    gs.run_command(
        "r.mapcalc",
        expression="stable_west = if(col() <= 20, 1, null())",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.dem.lod",
        dod="dod_pre",
        output="lod_west",
        output_domain="dom_west",
        method="local",
        window=11,
        stable_mask="stable_west",
        overwrite=True,
        env=env,
    )
    lod = gs.parse_command("r.univar", map="lod_west", format="json", env=env)
    dom = gs.parse_command("r.univar", map="dom_west", format="json", env=env)
    # Defined region is a dilation of the mask, far smaller than the region.
    assert 0 < int(lod["n"]) < 10000
    assert int(dom["n"]) == int(lod["n"])
    assert float(dom["min"]) == 1.0 and float(dom["max"]) == 1.0
    # A probe far east of the mask must be NULL.
    out = gs.read_command(
        "r.what", map="lod_west", coordinates="90.5,50.5", env=env
    )
    assert "*" in out


def test_parser_rules_dod_exclusive(session):
    """dod together with dem is rejected; neither is rejected."""
    import subprocess

    env = session.env
    for kwargs in (
        dict(dod="dod_pre", dem="dem_post", reference="dem_pre"),
        dict(),
    ):
        proc = gs.start_command(
            "r.dem.lod",
            output="lod_bad",
            method="local",
            window=11,
            overwrite=True,
            env=env,
            stderr=subprocess.PIPE,
            **kwargs,
        )
        _, err = proc.communicate()
        assert proc.returncode != 0
