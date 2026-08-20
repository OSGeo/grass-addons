import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


def _exists(name, env):
    return bool(gs.find_file(name, element="raster", env=env)["name"])


def _univar(name, env):
    return gs.parse_command("r.univar", map=name, format="json", env=env)


def test_slope(session):
    gs.run_command(
        "r.dem.stats",
        input="dem",
        output="dem_slope",
        metric="slope",
        env=session.env,
    )
    assert _exists("dem_slope", session.env)
    stats = _univar("dem_slope", session.env)
    assert float(stats["min"]) >= 0.0


def test_roughness_std_nonnegative(session):
    gs.run_command(
        "r.dem.stats",
        input="dem",
        output="dem_rough",
        metric="roughness_std",
        window=7,
        env=session.env,
    )
    stats = _univar("dem_rough", session.env)
    assert float(stats["min"]) >= 0.0


def test_error_sigma_local_nonnegative(session):
    gs.run_command(
        "r.dem.stats",
        input="dem",
        output="dem_sigma",
        metric="error_sigma_local",
        window=9,
        env=session.env,
    )
    stats = _univar("dem_sigma", session.env)
    assert float(stats["min"]) >= 0.0


def test_shannon_with_evenness(session):
    gs.run_command(
        "r.geomorphon",
        elevation="dem",
        forms="dem_forms",
        search=7,
        flat=4,
        env=session.env,
    )
    gs.run_command(
        "r.dem.stats",
        input="dem_forms",
        output="dem_shannon",
        metric="diversity_shannon",
        window=11,
        flags="e",
        env=session.env,
    )
    assert _exists("dem_shannon", session.env)
    assert _exists("dem_shannon_evenness", session.env)
    stats = _univar("dem_shannon", session.env)
    assert float(stats["min"]) >= 0.0


def test_even_window_rejected(session):
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "r.dem.stats",
            input="dem",
            output="dem_bad",
            metric="roughness_std",
            window=8,
            env=session.env,
        )
