import grass.script as gs


def _exists(name, env):
    return bool(gs.find_file(name, element="raster", env=env)["name"])


def _univar(name, env, mask=None):
    if mask:
        with gs.MaskManager(mask, env=env):
            return gs.parse_command("r.univar", map=name, format="json", env=env)
    return gs.parse_command("r.univar", map=name, format="json", env=env)


def test_forest_bump_removed(session):
    env = session.env
    gs.run_command(
        "r.dem.bias",
        method="forest",
        dod="dod_forest",
        mask="forest",
        window=21,
        output="dod_forest_corr",
        bias_field="forest_bias",
        env=env,
    )
    assert _exists("dod_forest_corr", env)
    assert _exists("forest_bias", env)
    # Inside the forest the +2 m bump should be largely removed.
    before = _univar("dod_forest", env, mask="forest")
    after = _univar("dod_forest_corr", env, mask="forest")
    assert abs(float(after["mean"])) < abs(float(before["mean"]))
    assert abs(float(after["mean"])) < 0.1


def test_forest_leaves_unmasked_cells_unchanged(session):
    env = session.env
    # Outside the forest mask the bias field is zero, so the DoD is untouched.
    gs.run_command(
        "r.mapcalc",
        expression=("east_diff = if(col() > 25, dod_forest_corr - dod_forest, null())"),
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="east_diff", format="json", env=env)
    assert abs(float(stats["max"])) < 1e-9
    assert abs(float(stats["min"])) < 1e-9


def test_regression_reduces_variance(session):
    env = session.env
    gs.run_command(
        "r.dem.bias",
        method="regression",
        dod="dod_reg",
        predictors="slope",
        stable_mask="stable",
        output="dod_reg_corr",
        env=env,
    )
    assert _exists("dod_reg_corr", env)
    before = _univar("dod_reg", env, mask="stable")
    after = _univar("dod_reg_corr", env, mask="stable")
    # The slope-correlated signal should be largely explained and removed.
    assert float(after["stddev"]) < float(before["stddev"])
