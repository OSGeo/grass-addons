import math

import grass.script as gs


def _univar(name, env):
    return gs.parse_command("r.univar", map=name, format="json", env=env)


def test_sigma_quadrature(session):
    """Propagated sigma equals sqrt(0.3^2 + 0.4^2) = 0.5 everywhere."""
    gs.run_command(
        "r.dem.errprop",
        dod="dod",
        sigma="sigma_a,sigma_b",
        output_sigma="sigma_dod",
        env=session.env,
    )
    stats = _univar("sigma_dod", session.env)
    assert math.isclose(float(stats["min"]), 0.5, abs_tol=1e-6)
    assert math.isclose(float(stats["max"]), 0.5, abs_tol=1e-6)


def test_lod_and_significance_outputs(session):
    """LoD is non-negative and the categorical map stays within [-4, 4]."""
    gs.run_command(
        "r.dem.errprop",
        dod="dod",
        sigma="sigma_a,sigma_b",
        output_sigma="sigma_dod2",
        output_lod="lod95",
        output_tvalue="tval",
        output_pvalue="pval",
        output_class="dclass",
        confidence=0.95,
        overwrite=True,
        env=session.env,
    )
    lod = _univar("lod95", session.env)
    # LoD = 1.96 * 0.5 = 0.98, uniform.
    assert math.isclose(float(lod["min"]), 1.959963 * 0.5, abs_tol=1e-3)
    assert float(lod["min"]) >= 0.0

    pval = _univar("pval", session.env)
    assert float(pval["min"]) >= 0.0
    assert float(pval["max"]) <= 1.0

    cls = _univar("dclass", session.env)
    assert float(cls["min"]) >= -4
    assert float(cls["max"]) <= 4
    # The most extreme DoD rows (|dh| up to ~2.8 m, well above any LoD) must be
    # flagged at the strongest erosion/deposition classes.
    assert int(float(cls["min"])) == -4
    assert int(float(cls["max"])) == 4


def test_null_propagates(session):
    """A NULL in any uncertainty source yields NULL in the propagated sigma."""
    gs.run_command(
        "r.mapcalc",
        expression="sigma_partial = if(row() < 5, null(), 0.4)",
        overwrite=True,
        env=session.env,
    )
    gs.run_command(
        "r.dem.errprop",
        dod="dod",
        sigma="sigma_a,sigma_partial",
        output_sigma="sigma_dod3",
        overwrite=True,
        env=session.env,
    )
    stats = _univar("sigma_dod3", session.env)
    # 30x30 region, 4 rows null => fewer than 900 valid cells.
    assert int(stats["n"]) < 900
