"""Known-answer tests for the r.dem toolset on the NC sample dataset.

The whole toolset is exercised against one synthetic scene built on
`elev_lid792_1m`, so that every assertion compares a tool's output with a
quantity that is known before the run: the applied rigid offset, the
constructed bias fields, or the analytic volume of the constructed change
features.

Two post-event surfaces are built, because they answer different questions:

- `rdem_dsm_offset` carries a pure rigid misregistration and is used for the
  co-registration tools. Its answer is exactly the applied offset.
- `rdem_dsm_post` is already aligned and carries the systematic bias fields
  and the change features. Its answers are the constructed bias fields and
  the analytic change volumes.

They are kept separate on purpose. A long-wavelength vertical bias (survey
doming) is partly degenerate with a horizontal shift in the first-order
Nuth and Kaab model, so a surface carrying both does not have a single
known co-registration answer. See the NOTES section of r.dem.nk.

The scene is expensive to build, so it is built once for the module rather
than once per tool, and the tool test cases share it. That is why this is a
single test module instead of one testsuite directory per tool.

The change features are Gaussians, so their volumes are analytic:
a feature of amplitude A and standard deviation s integrates to A * 2 * pi * s^2.

(C) 2026 by Corey T. White and the GRASS Development Team

SPDX-License-Identifier: GPL-2.0-or-later
"""

import os
import tempfile

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.tools import Tools

# Scene construction and the statistics the assertions rest on go through
# grass.tools. The tools under test are still driven by assertModule, which
# reports failures better than a bare call would.
tools = Tools(overwrite=True, consistent_return_value=True)

# Applied misregistration. The horizontal components are equal so that the
# shift magnitude is 0.65 m.
DX = 0.4596
DY = 0.4596
DZ = 1.32

# The change follows the drainage network: scour along the upper channel and
# deposition along the lower one, which is what a flood actually does. Both
# reaches are kept out of forest, because r.dem.bias method=forest cannot
# distinguish a canopy bump from real deposition and would remove the signal.
STREAM_THRESHOLD = 8000
SCOUR_ELEVATION = 116  # upper reach, above this elevation
FILL_ELEVATION = 110  # lower reach, below this elevation
SCOUR_DEPTH, SCOUR_SLOPE, SCOUR_FLAT = 2.5, 0.35, 5.0
FILL_HEIGHT, FILL_SLOPE, FILL_FLAT = 2.0, 0.30, 10.0

# Filled in by setUpModule from the constructed surface, which is exact.
VOL_EROSION = None
VOL_DEPOSITION = None

# Constructed bias fields.
DOME_AMPLITUDE = 0.25
DOME_RADIUS = 400.0
DOME_CENTER = (638650, 220375)
ROUGHNESS_COEFF = 0.6
CANOPY_BUMP = 1.5

# Survey noise is heteroscedastic: it grows with surface roughness and again
# under canopy. That is what makes a spatially variable Level of Detection
# worth computing, and a uniform one demonstrably wrong.
NOISE_BASE = 0.05
NOISE_ROUGHNESS_COEFF = 0.20
NOISE_CANOPY = 0.08
NOISE_SEED = 42

FOREST_CLASS = 2
POND_CLASS = 1
STABLE_CLASSES = (3, 4, 5, 6, 10)

# Every raster and vector this module creates, removed in tearDownModule.
RASTERS = [
    "rdem_change_truth",
    "rdem_acc",
    "rdem_streams",
    "rdem_ch_scour",
    "rdem_ch_scour_dist",
    "rdem_ch_fill",
    "rdem_ch_fill_dist",
    "rdem_dsm_truth",
    "rdem_tmp_shift",
    "rdem_post_shift",
    "rdem_roughness",
    "rdem_bias_dome",
    "rdem_bias_rough",
    "rdem_bias_canopy",
    "rdem_bias_truth",
    "rdem_noise_unit",
    "rdem_sigma_survey",
    "rdem_noise",
    "rdem_dsm_offset",
    "rdem_dsm_post",
    "rdem_dod_raw",
    "rdem_change_foot",
    "rdem_stable_roads",
    "rdem_stable_terrain",
    "rdem_stable_lod",
    "rdem_forest",
]
VECTORS = ["rdem_pgcp_roads"]


def _signed_volume(raster, negative):
    """Volume of the negative or positive part of a raster, in cubic metres.

    The region is 1 m by 1 m, so the cell sum is already a volume.
    """
    tmp = "rdem_tmp_signed"
    test = "< 0" if negative else "> 0"
    tools.r_mapcalc(
        expression=f"{tmp} = if({raster} {test}, {raster}, null())",
        overwrite=True,
        quiet=True,
    )
    total = tools.r_univar(map=tmp, format="json").json["sum"]
    tools.g_remove(flags="f", type="raster", name=tmp, quiet=True)
    return total


def setUpModule():
    """Build the shared scene once."""
    tools.g_region(raster="elev_lid792_1m")

    # Drainage network, from which the change features are built.
    tools.r_watershed(
        elevation="elev_lid792_1m",
        accumulation="rdem_acc",
        overwrite=True,
        quiet=True,
    )
    tools.r_stream_extract(
        elevation="elev_lid792_1m",
        accumulation="rdem_acc",
        threshold=STREAM_THRESHOLD,
        stream_raster="rdem_streams",
        overwrite=True,
        quiet=True,
    )
    for name, test in (
        ("rdem_ch_scour", f"elev_lid792_1m > {SCOUR_ELEVATION}"),
        ("rdem_ch_fill", f"elev_lid792_1m < {FILL_ELEVATION}"),
    ):
        tools.r_mapcalc(
            expression=f"{name} = if(rdem_streams && {test}"
            f" && landcover_1m != {FOREST_CLASS}, 1, null())",
            overwrite=True,
        )
        tools.r_grow_distance(
            input=name,
            distance=f"{name}_dist",
            overwrite=True,
            quiet=True,
        )

    # A flat core out to the given radius, then a constant-slope taper. This
    # is the same geometry r.earthworks builds with function=linear, which is
    # what the manual pages use, but it needs no addon.
    scour = (
        f"max(0.0, {SCOUR_DEPTH} - {SCOUR_SLOPE}"
        f" * max(0.0, rdem_ch_scour_dist - {SCOUR_FLAT}))"
    )
    fill = (
        f"max(0.0, {FILL_HEIGHT} - {FILL_SLOPE}"
        f" * max(0.0, rdem_ch_fill_dist - {FILL_FLAT}))"
    )
    tools.r_mapcalc(expression=f"rdem_change_truth = {fill} - {scour}", overwrite=True)

    # The constructed surface is the truth, so integrate it directly.
    global VOL_EROSION, VOL_DEPOSITION
    VOL_EROSION = abs(_signed_volume("rdem_change_truth", negative=True))
    VOL_DEPOSITION = _signed_volume("rdem_change_truth", negative=False)
    tools.r_mapcalc(
        expression="rdem_dsm_truth = elev_lid792_1m + rdem_change_truth", overwrite=True
    )

    # Misregistration: shift the truth surface by (DX, DY) by offsetting its
    # bounds and resampling back onto the analysis grid. This reproduces the
    # inverse-warp geometry r.dem.nk applies internally.
    region = tools.g_region(flags="g").keyval
    tools.g_copy(raster=("rdem_dsm_truth", "rdem_tmp_shift"), overwrite=True)
    tools.r_region(
        map="rdem_tmp_shift",
        n=region["n"] + DY,
        s=region["s"] + DY,
        e=region["e"] + DX,
        w=region["w"] + DX,
    )
    tools.g_region(raster="elev_lid792_1m")
    tools.r_resamp_interp(
        input="rdem_tmp_shift",
        output="rdem_post_shift",
        method="bilinear",
        overwrite=True,
    )

    # Systematic bias fields.
    tools.r_dem_stats(
        input="elev_lid792_1m",
        output="rdem_roughness",
        metric="roughness_std",
        window=13,
        overwrite=True,
    )
    east, north = DOME_CENTER
    tools.r_mapcalc(
        expression=f"rdem_bias_dome = {DOME_AMPLITUDE} * (1 - "
        f"((x() - {east}) * (x() - {east}) + (y() - {north}) * (y() - {north})) "
        f"/ ({DOME_RADIUS} * {DOME_RADIUS}))",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=f"rdem_bias_rough = {ROUGHNESS_COEFF} * rdem_roughness",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=f"rdem_bias_canopy = if(landcover_1m == {FOREST_CLASS}, {CANOPY_BUMP}, 0)",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression="rdem_bias_truth = rdem_bias_dome + rdem_bias_rough + rdem_bias_canopy",
        overwrite=True,
    )
    tools.r_surf_gauss(
        output="rdem_noise_unit",
        mean=0,
        sigma=1,
        seed=NOISE_SEED,
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=f"rdem_sigma_survey = {NOISE_BASE} + {NOISE_ROUGHNESS_COEFF} *"
        f" rdem_roughness + if(landcover_1m == {FOREST_CLASS},"
        f" {NOISE_CANOPY}, 0)",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression="rdem_noise = rdem_noise_unit * rdem_sigma_survey", overwrite=True
    )

    # Surface A: rigid misregistration only, for the co-registration tools.
    tools.r_mapcalc(
        expression=f"rdem_dsm_offset = rdem_post_shift + {DZ} + rdem_bias_canopy + rdem_noise",
        overwrite=True,
    )

    # Surface B: already aligned, carrying the bias fields and the change.
    tools.r_mapcalc(
        expression="rdem_dsm_post = elev_lid792_1m + rdem_change_truth "
        "+ rdem_bias_truth + rdem_noise",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression="rdem_dod_raw = rdem_dsm_post - elev_lid792_1m", overwrite=True
    )

    # Masks.
    tools.r_mapcalc(
        expression="rdem_change_foot = if(abs(rdem_change_truth) > 0.05, 1, null())",
        overwrite=True,
    )
    stable_test = " || ".join(f"landcover_1m == {c}" for c in STABLE_CLASSES)
    tools.r_mapcalc(
        expression=f"rdem_stable_roads = if(({stable_test}) && isnull(rdem_change_foot), "
        "1, null())",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=f"rdem_stable_terrain = if(landcover_1m != {FOREST_CLASS} "
        f"&& landcover_1m != {POND_CLASS} && isnull(rdem_change_foot), 1, null())",
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=f"rdem_forest = if(landcover_1m == {FOREST_CLASS}, 1, null())",
        overwrite=True,
    )
    # Forest is unchanged terrain, so it is stable for uncertainty
    # estimation even though the canopy bump makes it unusable for the
    # Nuth and Kaab regression. Leaving it out of the LoD mask would leave
    # the noisiest part of the map uncharacterised.
    tools.r_mapcalc(
        expression=f"rdem_stable_lod = if(landcover_1m != {POND_CLASS}"
        " && isnull(rdem_change_foot), 1, null())",
        overwrite=True,
    )
    tools.v_clip(
        flags="r",
        input="streets_wake",
        output="rdem_pgcp_roads",
        overwrite=True,
    )


def tearDownModule():
    tools.g_remove(flags="f", type="raster", name=RASTERS, quiet=True)
    tools.g_remove(flags="f", type="vector", name=VECTORS, quiet=True)


def _masked_stat(raster, mask, stat):
    """Univariate statistic of a raster restricted to a mask."""
    tmp = "rdem_tmp_masked_stat"
    tools.r_mapcalc(
        expression=f"{tmp} = if({mask}, {raster}, null())", overwrite=True, quiet=True
    )
    values = tools.r_univar(map=tmp, flags="e", format="json").json
    tools.g_remove(flags="f", type="raster", name=tmp)
    return values[stat]


def _masked_nmad(raster, mask):
    """Normalized median absolute deviation of a raster under a mask."""
    median = _masked_stat(raster, mask, "median")
    return 1.4826 * _masked_stat(f"abs({raster} - ({median}))", mask, "median")


def _read_transform(path):
    """Parse a key=value transform file written by r.dem.nk or r.dem.icp."""
    values = {}
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = float(value)
    return values


class TestNuthKaab(TestCase):
    """r.dem.nk recovers the applied rigid offset."""

    outputs = ["rdem_nk_out", "rdem_nk_out_resid"]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_recovers_applied_offset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nk.txt")
            self.assertModule(
                "r.dem.nk",
                sfm="rdem_dsm_offset",
                lidar="elev_lid792_1m",
                stable_mask="rdem_stable_terrain",
                output="rdem_nk_out",
                transform_output=path,
                overwrite=True,
            )
            solved = _read_transform(path)

        # r.dem.nk reports the offset to be removed, so the signs are positive
        # for a surface displaced towards the north east.
        self.assertAlmostEqual(solved["dx"], DX, delta=0.05)
        self.assertAlmostEqual(solved["dy"], DY, delta=0.05)
        self.assertAlmostEqual(solved["dz"], DZ, delta=0.02)

    def test_residual_is_reduced(self):
        self.assertModule(
            "r.dem.nk",
            sfm="rdem_dsm_offset",
            lidar="elev_lid792_1m",
            stable_mask="rdem_stable_terrain",
            output="rdem_nk_out",
            overwrite=True,
        )
        before = _masked_stat(
            "rdem_dsm_offset - elev_lid792_1m", "rdem_stable_terrain", "median"
        )
        after = _masked_stat(
            "rdem_nk_out - elev_lid792_1m", "rdem_stable_terrain", "median"
        )
        self.assertGreater(abs(before), 1.0)
        self.assertLess(abs(after), 0.05)


class TestIcp(TestCase):
    """r.dem.icp recovers the applied rigid offset at dof=4."""

    outputs = ["rdem_icp_out"]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_recovers_applied_offset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "icp.txt")
            self.assertModule(
                "r.dem.icp",
                source="rdem_dsm_offset",
                reference="elev_lid792_1m",
                mask="rdem_stable_terrain",
                output="rdem_icp_out",
                dof=4,
                transform_out=path,
                overwrite=True,
            )
            solved = _read_transform(path)

        # r.dem.icp reports the transform that maps the source onto the
        # reference, so its signs are opposite to those of r.dem.nk.
        self.assertAlmostEqual(solved["tx"], -DX, delta=0.05)
        self.assertAlmostEqual(solved["ty"], -DY, delta=0.05)
        self.assertAlmostEqual(solved["tz"], -DZ, delta=0.02)
        self.assertAlmostEqual(solved["yaw"], 0.0, delta=0.01)


class TestCoregister(TestCase):
    """r.dem.coregister recovers the applied vertical offset from PGCPs."""

    outputs = ["rdem_cor_out", "rdem_cor_nk_out"]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_pgcp_vertical_recovers_dz(self):
        self.assertModule(
            "r.dem.coregister",
            dem="rdem_dsm_offset",
            reference="elev_lid792_1m",
            pgcp="rdem_pgcp_roads",
            output="rdem_cor_out",
            method="pgcp_vertical",
            buffer=2.0,
            overwrite=True,
        )
        # Roads are flat, so the horizontal shift contributes almost nothing
        # to the elevation residual there and the median bias is DZ.
        residual = _masked_stat(
            "rdem_cor_out - elev_lid792_1m", "rdem_stable_roads", "median"
        )
        self.assertLess(abs(residual), 0.05)

    def test_nk_chain_removes_horizontal_offset(self):
        self.assertModule(
            "r.dem.coregister",
            dem="rdem_dsm_offset",
            reference="elev_lid792_1m",
            pgcp="rdem_pgcp_roads",
            stable_mask="rdem_stable_terrain",
            output="rdem_cor_nk_out",
            method="nk",
            overwrite=True,
        )
        residual = _masked_stat(
            "rdem_cor_nk_out - elev_lid792_1m", "rdem_stable_terrain", "median"
        )
        self.assertLess(abs(residual), 0.05)


class TestStats(TestCase):
    """r.dem.stats reproduces the reference terrain metrics."""

    outputs = ["rdem_st_slope", "rdem_ref_slope", "rdem_st_rough"]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_slope_matches_r_slope_aspect(self):
        self.assertModule(
            "r.dem.stats",
            input="elev_lid792_1m",
            output="rdem_st_slope",
            metric="slope",
            overwrite=True,
        )
        self.runModule(
            "r.slope.aspect",
            elevation="elev_lid792_1m",
            slope="rdem_ref_slope",
            overwrite=True,
        )
        self.assertRastersNoDifference(
            "rdem_st_slope", "rdem_ref_slope", precision=1e-6
        )

    def test_roughness_is_non_negative(self):
        self.assertModule(
            "r.dem.stats",
            input="elev_lid792_1m",
            output="rdem_st_rough",
            metric="roughness_std",
            window=13,
            overwrite=True,
        )
        info = tools.r_info(map="rdem_st_rough", flags="rg").keyval
        self.assertGreaterEqual(info["min"], 0.0)


class TestBias(TestCase):
    """Each r.dem.bias method removes the bias field it targets."""

    outputs = [
        "rdem_dod_sp",
        "rdem_dod_fo",
        "rdem_dod_rg",
        "rdem_bf_sp",
        "rdem_dod_deb",
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_spline_removes_the_long_wavelength_field(self):
        before = _masked_stat("rdem_dod_raw", "rdem_stable_terrain", "median")
        self.assertModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            bias_field="rdem_bf_sp",
            overwrite=True,
        )
        after = _masked_stat("rdem_dod_sp", "rdem_stable_terrain", "median")
        self.assertGreater(abs(before), 0.1)
        self.assertLess(abs(after), 0.01)

    def test_spline_field_tracks_the_constructed_bias(self):
        self.assertModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            bias_field="rdem_bf_sp",
            overwrite=True,
        )
        # Away from forest the constructed bias is the dome plus the
        # roughness term; the fitted field should match it in the mean.
        error = _masked_stat(
            "rdem_bf_sp - (rdem_bias_dome + rdem_bias_rough)",
            "rdem_stable_terrain",
            "mean",
        )
        self.assertLess(abs(error), 0.02)

    def test_forest_removes_the_canopy_bump(self):
        before = _masked_stat("rdem_dod_raw", "rdem_forest", "median")
        self.runModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        self.assertModule(
            "r.dem.bias",
            dod="rdem_dod_sp",
            output="rdem_dod_deb",
            method="forest",
            mask="rdem_forest",
            window=21,
            overwrite=True,
        )
        after = _masked_stat("rdem_dod_deb", "rdem_forest", "median")
        self.assertGreater(abs(before), 1.0)
        self.assertLess(abs(after), 0.01)

    def test_regression_zeroes_the_stable_residual(self):
        self.assertModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_rg",
            method="regression",
            predictors="rdem_roughness",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        after = _masked_stat("rdem_dod_rg", "rdem_stable_terrain", "mean")
        self.assertLess(abs(after), 0.01)


class TestLod(TestCase):
    """r.dem.lod reproduces the LoD implied by the injected noise."""

    outputs = [
        "rdem_dod_deb",
        "rdem_dod_sp",
        "rdem_lod_g",
        "rdem_lod_l",
        "rdem_sigma_l",
        "rdem_domain_l",
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_sp",
            output="rdem_dod_deb",
            method="forest",
            mask="rdem_forest",
            window=21,
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_global_lod_matches_the_injected_noise(self):
        self.assertModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_g",
            method="global",
            stable_mask="rdem_stable_lod",
            confidence=0.95,
            overwrite=True,
        )
        info = tools.r_info(map="rdem_lod_g", flags="rg").keyval
        lod = info["min"]
        self.assertAlmostEqual(info["max"], lod, places=9)

        # The debiased residual on the stable cells is the injected noise, so
        # the LoD is z(0.95) times that noise's NMAD.
        expected = 1.96 * _masked_nmad("rdem_noise", "rdem_stable_lod")
        self.assertAlmostEqual(lod, expected, delta=0.02)

    def test_local_lod_is_spatially_variable(self):
        self.assertModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_l",
            method="local",
            window=21,
            stable_mask="rdem_stable_lod",
            output_sigma="rdem_sigma_l",
            output_domain="rdem_domain_l",
            confidence=0.95,
            overwrite=True,
        )
        info = tools.r_info(map="rdem_lod_l", flags="rg").keyval
        self.assertGreater(info["max"], info["min"])

        # The spread must be real signal, not estimator noise: the injected
        # sigma varies by more than a factor of two across the map, and the
        # recovered LoD has to follow it.
        spread = tools.r_univar(
            map="rdem_lod_l", flags="e", format="json", percentile=[5, 95]
        ).json
        percentiles = {p["percentile"]: p["value"] for p in spread["percentiles"]}
        self.assertGreater(percentiles[95] / percentiles[5], 2.0)

        # output = z * output_sigma, exactly.
        ratio = _masked_stat("rdem_lod_l / rdem_sigma_l", "rdem_domain_l", "mean")
        self.assertAlmostEqual(ratio, 1.96, delta=0.001)


class TestErrprop(TestCase):
    """r.dem.errprop derives the significance products exactly."""

    outputs = [
        "rdem_dod_sp",
        "rdem_dod_deb",
        "rdem_sigma_l",
        "rdem_lod_l",
        "rdem_domain_l",
        "rdem_ep_sigma",
        "rdem_ep_z",
        "rdem_ep_class",
        "rdem_ep_zcheck",
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_sp",
            output="rdem_dod_deb",
            method="forest",
            mask="rdem_forest",
            window=21,
            overwrite=True,
        )
        cls.runModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_l",
            method="local",
            window=21,
            stable_mask="rdem_stable_lod",
            output_sigma="rdem_sigma_l",
            output_domain="rdem_domain_l",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_zscore_is_dod_over_sigma(self):
        self.assertModule(
            "r.dem.errprop",
            dod="rdem_dod_deb",
            sigma="rdem_sigma_l",
            output_sigma="rdem_ep_sigma",
            output_zscore="rdem_ep_z",
            overwrite=True,
        )
        tools.r_mapcalc(
            expression="rdem_ep_zcheck = abs(abs(rdem_dod_deb) / rdem_ep_sigma - rdem_ep_z)",
            overwrite=True,
        )
        info = tools.r_info(map="rdem_ep_zcheck", flags="rg").keyval
        self.assertLess(info["max"], 1e-9)

    def test_class_raster_spans_the_confidence_levels(self):
        self.assertModule(
            "r.dem.errprop",
            dod="rdem_dod_deb",
            sigma="rdem_sigma_l",
            output_sigma="rdem_ep_sigma",
            output_class="rdem_ep_class",
            overwrite=True,
        )
        info = tools.r_info(map="rdem_ep_class", flags="rg").keyval
        self.assertEqual(int(info["min"]), -4)
        self.assertEqual(int(info["max"]), 4)


class TestChange(TestCase):
    """r.dem.change recovers the analytic volumes of the change features."""

    outputs = [
        "rdem_dod_sp",
        "rdem_dod_deb",
        "rdem_lod_g",
        "rdem_lod_l",
        "rdem_lod_filled",
        "rdem_sig_dod",
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_sp",
            output="rdem_dod_deb",
            method="forest",
            mask="rdem_forest",
            window=21,
            overwrite=True,
        )
        cls.runModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_g",
            method="global",
            stable_mask="rdem_stable_lod",
            confidence=0.95,
            overwrite=True,
        )
        cls.runModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_l",
            method="local",
            window=21,
            stable_mask="rdem_stable_lod",
            overwrite=True,
        )
        # No stable cell falls inside the window in the interior of the
        # change features, so the local limit is undefined exactly where the
        # change is. Fall back to the flight-wide limit there.
        tools.r_mapcalc(
            expression="rdem_lod_filled = if(isnull(rdem_lod_l), rdem_lod_g, rdem_lod_l)",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_volumes_match_the_analytic_truth(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "volumes.csv")
            self.assertModule(
                "r.dem.change",
                dod="rdem_dod_deb",
                lod="rdem_lod_filled",
                output_sig="rdem_sig_dod",
                volume_csv=path,
                flags="n",
                overwrite=True,
            )
            volumes = {}
            with open(path) as handle:
                header = handle.readline()
                self.assertIn("value_m3", header)
                for line in handle:
                    fields = line.strip().split(",")
                    volumes[fields[0]] = float(fields[1])

        # The LoD mask discards the taper of both features, and noise that
        # survives the speckle filter adds a little back.
        self.assertAlmostEqual(volumes["deposition"] / VOL_DEPOSITION, 1.0, delta=0.10)
        self.assertAlmostEqual(volumes["erosion"] / VOL_EROSION, 1.0, delta=0.10)
        self.assertAlmostEqual(
            volumes["net"],
            volumes["deposition"] - volumes["erosion"],
            places=6,
        )


class TestScreen(TestCase):
    """r.dem.screen flags the change footprint in the triage map."""

    outputs = [
        "rdem_dod_sp",
        "rdem_dod_deb",
        "rdem_lod_g",
        "rdem_sig_dod",
        "rdem_dod10",
        "rdem_dod10_masked",
        "rdem_triage",
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_lid792_1m")
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_raw",
            output="rdem_dod_sp",
            method="spline",
            stable_mask="rdem_stable_terrain",
            overwrite=True,
        )
        cls.runModule(
            "r.dem.bias",
            dod="rdem_dod_sp",
            output="rdem_dod_deb",
            method="forest",
            mask="rdem_forest",
            window=21,
            overwrite=True,
        )
        cls.runModule(
            "r.dem.lod",
            dod="rdem_dod_deb",
            output="rdem_lod_g",
            method="global",
            stable_mask="rdem_stable_lod",
            overwrite=True,
        )
        cls.runModule(
            "r.dem.change",
            dod="rdem_dod_deb",
            lod="rdem_lod_g",
            output_sig="rdem_sig_dod",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="raster", name=cls.outputs, quiet=True
        )
        cls.del_temp_region()

    def test_triage_flags_the_change_footprint(self):
        self.runModule("g.region", raster="elev_lid792_1m", res=10, flags="a")
        self.runModule(
            "r.resamp.stats",
            input="rdem_sig_dod",
            output="rdem_dod10_masked",
            method="average",
            overwrite=True,
        )
        # Blocks holding no significant cell come back NULL, which for
        # screening means no change rather than no data.
        tools.r_mapcalc(
            expression="rdem_dod10 = if(isnull(rdem_dod10_masked), 0, rdem_dod10_masked)",
            overwrite=True,
        )
        # Topographic screening only. A spectral test would need bitemporal
        # imagery, which the sample dataset does not carry, and inventing a
        # spectral layer from the known change would only assert itself.
        self.assertModule(
            "r.dem.screen",
            dod="rdem_dod10",
            output="rdem_triage",
            topo_threshold=1.0,
            overwrite=True,
        )
        counts = tools.r_stats(input="rdem_triage", flags="cn").text
        classes = {
            int(line.split()[0]): int(line.split()[1])
            for line in counts.strip().splitlines()
            if line.strip()
        }
        # Class 2 is topographic change, which is what the constructed
        # features are and all that can be verified without a second date.
        self.assertIn(2, classes)
        self.assertGreater(classes[2], 50)


if __name__ == "__main__":
    test()
