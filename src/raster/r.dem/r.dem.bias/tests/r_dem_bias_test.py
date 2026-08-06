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


def test_regression_output_se(session):
    """Prediction SE: positive, floored by residual variance, grows where
    the model extrapolates beyond the stable predictor range."""
    import math
    import re
    import subprocess

    env = session.env
    # Synthetic: linear trend in row plus seeded noise; stable = rows 1-25,
    # so rows 26-50 extrapolate beyond the fitted predictor range.
    gs.run_command("r.mapcalc", expression="rowpred = row()", env=env)
    gs.run_command(
        "r.mapcalc",
        expression="dod_se = 1.0 + 0.1 * row() + rand(-0.3, 0.3)",
        seed=7,
        env=env,
    )
    proc = gs.start_command(
        "r.dem.bias",
        method="regression",
        dod="dod_se",
        predictors="rowpred,slope",
        stable_mask="stable",
        output="dod_se_corr",
        output_se="se_map",
        overwrite=True,
        env=env,
        stderr=subprocess.PIPE,
    )
    _, err = proc.communicate()
    if isinstance(err, bytes):
        err = err.decode()
    assert proc.returncode == 0, err
    m = re.search(r"s2 = ([0-9.]+)", err)
    assert m, "s2 message not found"
    s2 = float(m.group(1))
    assert s2 > 0.0

    se = _univar("se_map", env)
    # Defined wherever every predictor is defined (slope is NULL on the
    # region edge), non-negative, spatially varying (pure model term).
    assert int(se["n"]) == int(_univar("slope", env)["n"])
    assert float(se["min"]) >= 0.0
    assert float(se["max"]) > float(se["min"])
    # Extrapolation: SE beyond the stable rows exceeds SE within them.
    gs.run_command(
        "r.mapcalc",
        expression="se_in = if(row() <= 25, se_map, null())",
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression="se_out = if(row() > 25, se_map, null())",
        env=env,
    )
    assert float(_univar("se_out", env)["mean"]) > float(_univar("se_in", env)["mean"])
    # Debiasing holds on the stable cells despite the noise.
    gs.run_command(
        "r.mapcalc",
        expression="corr_stable = if(!isnull(stable), dod_se_corr, null())",
        env=env,
    )
    assert abs(float(_univar("corr_stable", env)["mean"])) < 0.05


def test_regression_se_pointwise(session):
    """se_map matches an independent numpy computation of
    sqrt(s2 + x' Cov x) cell by cell (skew-free predictors, no log path)."""
    import numpy as np
    from grass.script import array as garray

    env = session.env
    gs.run_command("r.mapcalc", expression="colpred = col()", env=env)
    gs.run_command(
        "r.mapcalc",
        expression="dod_pw = 0.8 + 0.05 * row() - 0.02 * col() + rand(-0.2, 0.2)",
        seed=11,
        env=env,
    )
    gs.run_command(
        "r.dem.bias",
        method="regression",
        dod="dod_pw",
        predictors="rowpred,colpred",
        stable_mask="stable",
        output="dod_pw_corr",
        output_se="se_pw",
        overwrite=True,
        env=env,
    )

    rowp = np.asarray(garray.array("rowpred", env=env))
    colp = np.asarray(garray.array("colpred", env=env))
    dod = np.asarray(garray.array("dod_pw", env=env))
    stable = np.asarray(garray.array("stable", env=env))
    se_tool = np.asarray(garray.array("se_pw", env=env))

    # Replicate the tool: z-score on FULL-region population stats (both
    # predictors are symmetric, so the log path is not taken).
    z1 = (rowp - rowp.mean()) / rowp.std()
    z2 = (colp - colp.mean()) / colp.std()
    m = stable == 1
    X = np.column_stack([np.ones(m.sum()), z1[m], z2[m]])
    y = dod[m]
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta
    s2 = float(resid @ resid) / (X.shape[0] - X.shape[1])
    cov = s2 * xtx_inv

    for r, c in [(0, 0), (49, 49), (25, 10)]:
        x = np.array([1.0, z1[r, c], z2[r, c]])
        se_ref = np.sqrt(max(0.0, x @ cov @ x))
        assert abs(se_tool[r, c] - se_ref) < 1e-6, (r, c, se_tool[r, c], se_ref)


def test_spline_removes_smooth_bump(session):
    """method=spline: a long-wavelength bump sampled on stable cells is
    removed from the corrected DoD."""
    env = session.env
    # Smooth dome centered in the region + noise; stable cells everywhere
    # except a central square (simulating a change zone).
    gs.run_command(
        "r.mapcalc",
        expression=(
            "dod_sp = 2.0 * exp(-((row()-25)^2 + (col()-25)^2) "
            "/ 400.0) + rand(-0.1, 0.1)"
        ),
        seed=3,
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression=(
            "stable_sp = if(row() > 20 && row() < 30 && "
            "col() > 20 && col() < 30, null(), 1)"
        ),
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.dem.bias",
        method="spline",
        dod="dod_sp",
        stable_mask="stable_sp",
        output="dod_sp_corr",
        bias_field="sp_field",
        spline_npoints=1500,
        spline_res=2,
        overwrite=True,
        env=env,
    )
    before = _univar("dod_sp", env)
    after = _univar("dod_sp_corr", env)
    # The dome (mean ~0.3, max ~2) is flattened.
    assert abs(float(after["mean"])) < abs(float(before["mean"])) * 0.5
    assert float(after["max"]) < float(before["max"]) * 0.6
    assert _exists("sp_field", env)
