#!/usr/bin/env python

"""
ASHREA methodology
------------------

"""
from collections import namedtuple
from os import getpid

from numpy import log, pi

from grass.pygrass.utils import get_mapset_raster
from grass.script import core as gcore
from grass.script import raster as grast

BASENAME = "tmprgreen{pid:05d}_".format(pid=getpid())

# Coefficients for Tp correlation
TP = [
    7.8189e00,
    -6.4270e01,
    1.5387e02,
    -8.4809e01,
    3.4610e00,
    -9.4753e-01,
    -6.0416e-02,
    1.5631e00,
    -8.9416e-03,
    1.9061e-05,
    -2.2890e00,
    1.0187e-01,
    6.5690e-03,
    -4.0918e01,
    1.5557e01,
    -1.9107e01,
    1.0529e-01,
    2.5501e01,
    -2.1177e00,
    7.7529e01,
    -5.0454e01,
    7.6352e01,
    -5.3719e-01,
    -1.3200e02,
    1.2878e01,
    1.2697e-01,
    -4.0284e-04,
    -7.2065e-02,
    9.5184e-04,
    -2.4167e-02,
    9.6811e-05,
    2.8317e-02,
    -1.0905e-03,
    1.2207e-01,
    -7.1050e-03,
    -1.1129e-03,
    -4.5566e-04,
]


FUNCTIONS = {
    "6h": [
        0.6619352,
        -4.815693,
        15.03571,
        -0.09879421,
        0.02917889,
        0.1138498,
        0.005610933,
        0.7796329,
        -0.3243880,
        -0.01824101,
    ],
    "1m": [
        0.4132728,
        0.2912981,
        0.07589286,
        0.1563978,
        -0.2289355,
        -0.004927554,
        -0.002694979,
        -0.6380360,
        0.2950815,
        0.1493320,
    ],
    "10y": [
        0.3057646,
        0.08987446,
        -0.09151786,
        -0.03872451,
        0.1690853,
        -0.02881681,
        -0.002886584,
        -0.1723169,
        0.03112034,
        -0.1188438,
    ],
}


# define named tuple to struct data/characteristics
GroundLoads = namedtuple("GroundLoads", field_names=["hourly", "monthly", "yearly"])


GroundProperties = namedtuple(
    "GroundProperties", field_names=["conductivity", "diffusivity", "temperature"]
)
FluidProperties = namedtuple(
    "FluidProperties", field_names=["capacity", "massflow", "inlettemp"]
)


Borehole = namedtuple(
    "Borehole",
    field_names=[
        "radius",
        "pipe_inner_radius",
        "pipe_outer_radius",
        "k_grout",
        "k_pipe",
        "distance",
        "convection",
    ],
)


BoreholeExchanger = namedtuple(
    "BoreholeExchanger", field_names=["ground_loads", "ground", "fluid", "borehole"]
)

BoreholeField = namedtuple(
    "BoreholeField", field_names=["distance", "number", "ratio", "bhe"]
)


InfoVars = namedtuple(
    "InfoVars",
    field_names=["long_term", "medium_term", "short_term", "fluid_temp", "resistence"],
)


def exists(raster_name):
    """Return True if the map already exist"""
    raster, mapset = raster_name.split("@") if "@" in raster_name else (raster_name, "")
    return bool(get_mapset_raster(raster_name, mapset))


def rename(mtype, from_mname, to_mname):
    from_to = "{from_name},{to_name}"
    gcore.run_command(
        "g.rename", **{mtype: from_to.format(from_name=from_mname, to_name=to_mname)}
    )


def ground_resistence(ground, borehole, period="6h"):
    """Return the effective ground thermal resistances:

    :math:`R_{period}` [m K W-1]

    Parameters
    ----------

    ground: GroundProperties
        GroundProperties tuple with the main characteristics of the ground
    borehole: rbore [m]
        borehole radius
    period: str
        Six periods are supported:
            * 6h (short term),
            * 1m (medium term),
            * 10y (long term)

    Example
    -------
    >>> ground = GroundProperties(conductivity=2, diffusivity=0.086,
    ...                           temperature=10.)
    >>> ground_resistence(ground, borehole=0.06, period='6h')
    0.11445903013141503
    >>> ground_resistence(ground, borehole=0.06, period='1m')
    0.18020547706451287
    >>> ground_resistence(ground, borehole=0.06, period='10y')
    0.19083864808240175

    >>> ground = GroundProperties(conductivity=2.25, diffusivity=0.06757039008,
    ...                           temperature=10.)
    >>> ground_resistence(ground, borehole=0.054, period='6h')
    0.10067477057511355
    >>> ground_resistence(ground, borehole=0.054, period='1m')
    0.1600011827001955
    >>> ground_resistence(ground, borehole=0.054, period='10y')
    0.16963475237210959
    """
    c0, c1, c2, c3, c4, c5, c6, c7, c8, c9 = FUNCTIONS[period]
    conductivity, diffusivity, temperature = ground
    log_diff = log(diffusivity)
    return (
        1.0
        / conductivity
        * (
            c0
            + c1 * borehole
            + c2 * borehole**2.0
            + c3 * diffusivity
            + c4 * diffusivity**2.0
            + c5 * log_diff
            + c6 * log_diff**2
            + c7 * borehole * diffusivity
            + c8 * borehole * log_diff
            + c9 * diffusivity * log_diff
        )
    )


def _log(out, value, execute=True, show=False, **kwargs):
    """Return the natural log of a number/raster

    Example
    -------
    >>> _log('log_elev', 'elevation', execute=False, show=True)
    log_elev = log(elevation)
    'log_elev'
    >>> _log('log_elev', 1, execute=False)
    0.0
    """
    if isinstance(value, str):
        # use rmapcalc and return raster name
        rcmd = "{out} = log({name})".format(out=out, name=value)
        if show:
            print(rcmd)
        if execute:
            grast.mapcalc(rcmd, **kwargs)
        return out
    else:
        return log(value)


def r_ground_resistence(out, ground, borehole, period="6h", execute=True, **kwargs):
    """Return the effective ground thermal resistances:

    :math:`R_{period}` [m K W-1]

    Parameters
    ----------

    ground: GroundProperties
        GroundProperties tuple with the main characteristics of the ground
    borehole: rbore [m]
        borehole radius
    period: str
        Three periods are supported:
            * 6h (short term),
            * 1m (medium term),
            * 10y (long term)

    Example
    -------
    >>> ground = GroundProperties(conductivity=2, diffusivity=0.086,
    ...                           temperature=10.)
    >>> r_ground_resistence('g_resistence_6h', ground, borehole=0.06,
    ...                     period='6h', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_6h = (1. / 2 *
                        (0.6619352 +
                         -4.815693 * 0.06 +
                         15.03571 * 0.06^2. +
                         -0.09879421 * 0.086 +
                         0.02917889 * 0.086^2. +
                         0.1138498 * -2.45340798273 +
                         0.005610933 * -2.45340798273^2 +
                         0.7796329 * 0.06 * 0.086 +
                         -0.324388 * 0.06 * -2.45340798273 +
                         -0.01824101 * 0.086 * -2.45340798273))'
    >>> r_ground_resistence('g_resistence_1m', ground, borehole=0.06,
    ...                     period='1m', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_1m = (1. / 2 *
                        (0.4132728 +
                         0.2912981 * 0.06 +
                         0.07589286 * 0.06^2. +
                         0.1563978 * 0.086 +
                         -0.2289355 * 0.086^2. +
                         -0.004927554 * -2.45340798273 +
                         -0.002694979 * -2.45340798273^2 +
                         -0.638036 * 0.06 * 0.086 +
                         0.2950815 * 0.06 * -2.45340798273 +
                         0.149332 * 0.086 * -2.45340798273))'
    >>> r_ground_resistence('g_resistence_10y', ground, borehole=0.06,
    ...                     period='10y', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_10y = (1. / 2 *
                         (0.3057646 +
                          0.08987446 * 0.06 +
                          -0.09151786 * 0.06^2. +
                          -0.03872451 * 0.086 +
                          0.1690853 * 0.086^2. +
                          -0.02881681 * -2.45340798273 +
                          -0.002886584 * -2.45340798273^2 +
                          -0.1723169 * 0.06 * 0.086 +
                          0.03112034 * 0.06 * -2.45340798273 +
                          -0.1188438 * 0.086 * -2.45340798273))'


    >>> ground = GroundProperties(conductivity='g_conductivity',
    ...                           diffusivity='g_diffusivity',
    ...                           temperature='g_temperature')
    >>> r_ground_resistence('g_resistence_6h', ground, borehole=0.06,
    ...                     period='6h', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_6h = (1. / g_conductivity *
                        (0.6619352 +
                         -4.815693 * 0.06 +
                         15.03571 * 0.06^2. +
                         -0.09879421 * g_diffusivity +
                         0.02917889 * g_diffusivity^2. +
                         0.1138498 * g_resistence_6h_log +
                         0.005610933 * g_resistence_6h_log^2 +
                         0.7796329 * 0.06 * g_diffusivity +
                         -0.324388 * 0.06 * g_resistence_6h_log +
                         -0.01824101 * g_diffusivity * g_resistence_6h_log))'
    >>> r_ground_resistence('g_resistence_1m', ground, borehole=0.06,
    ...                     period='1m', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_1m = (1. / g_conductivity *
                        (0.4132728 +
                         0.2912981 * 0.06 +
                         0.07589286 * 0.06^2. +
                         0.1563978 * g_diffusivity +
                         -0.2289355 * g_diffusivity^2. +
                         -0.004927554 * g_resistence_1m_log +
                         -0.002694979 * g_resistence_1m_log^2 +
                         -0.638036 * 0.06 * g_diffusivity +
                         0.2950815 * 0.06 * g_resistence_1m_log +
                         0.149332 * g_diffusivity * g_resistence_1m_log))'
    >>> r_ground_resistence('g_resistence_10y', ground, borehole=0.06,
    ...                     period='10y', execute=False)
    ...                                       # doctest: +NORMALIZE_WHITESPACE
    'g_resistence_10y = (1. / g_conductivity *
                         (0.3057646 +
                          0.08987446 * 0.06 +
                          -0.09151786 * 0.06^2. +
                          -0.03872451 * g_diffusivity +
                          0.1690853 * g_diffusivity^2. +
                          -0.02881681 * g_resistence_10y_log +
                          -0.002886584 * g_resistence_10y_log^2 +
                          -0.1723169 * 0.06 * g_diffusivity +
                          0.03112034 * 0.06 * g_resistence_10y_log +
                          -0.1188438 * g_diffusivity * g_resistence_10y_log))'
    """
    c0, c1, c2, c3, c4, c5, c6, c7, c8, c9 = FUNCTIONS[period]
    conductivity, diffusivity, temperature = ground
    log_diff = _log(out + "_log", diffusivity, execute=execute, **kwargs)
    res = (
        "{out} = (1. / {conductivity} *"
        " ({c0} +"
        "  {c1} * {borehole} +"
        "  {c2} * {borehole}^2. +"
        "  {c3} * {diffusivity} +"
        "  {c4} * {diffusivity}^2. +"
        "  {c5} * {log_diff} +"
        "  {c6} * {log_diff}^2 +"
        "  {c7} * {borehole} * {diffusivity} +"
        "  {c8} * {borehole} * {log_diff} +"
        "  {c9} * {diffusivity} * {log_diff}))"
    )
    rcmd = res.format(
        out=out,
        c0=c0,
        c1=c1,
        c2=c2,
        c3=c3,
        c4=c4,
        c5=c5,
        c6=c6,
        c7=c7,
        c8=c8,
        c9=c9,
        conductivity=conductivity,
        diffusivity=diffusivity,
        borehole=borehole,
        log_diff=log_diff,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def fluid_temperature_hp_outlet(fluid, peak):
    """Return heat pump outlet temperature :math:`T_{outHP}` [°C]

    Parameters
    ----------
    fluid: FluidProperties
        FluidProperties named tuple with the  fluid characteristics
    peak: qh [W]
        peak hourly ground load

    Example
    -------
    >>> fluid = FluidProperties(capacity=4200, massflow=0.050,
    ...                         inlettemp=40.2)
    >>> fluid_temperature_hp_outlet(fluid, 12000)
    44.96190476190476

    >>> fluid = FluidProperties(capacity=4000, massflow=0.074,
    ...                         inlettemp=4.44)
    >>> fluid_temperature_hp_outlet(fluid, -392250)
    1.0616216216216219
    """
    return fluid.inlettemp + peak / (
        fluid.massflow * abs(peak) / 1000.0 * fluid.capacity
    )


def r_fluid_temperature_hp_outlet(out, fluid, peak, execute=True, **kwargs):
    """Return heat pump outlet temperature :math:`T_{outHP}` [°C]

    Parameters
    ----------
    fluid: FluidProperties
        FluidProperties named tuple with the  fluid characteristics
    peak: qh [W]
        peak hourly ground load

    Example
    -------
    >>> fluid = FluidProperties(capacity=4200, massflow=0.050,
    ...                         inlettemp=40.2)
    >>> r_fluid_temperature_hp_outlet('fluid_tmp_hp_outlet', fluid, 'peak',
    ...                               execute=False)
    'fluid_tmp_hp_outlet = 40.2 + peak / (0.05 * abs(peak) / 1000. * 4200)'
    """
    res = (
        "{out} = {fluid_inlettemp} + "
        "{peak} / "
        "({fluid_massflow} * abs({peak}) / 1000. * {fluid_capacity})"
    )
    rcmd = res.format(
        out=out,
        peak=peak,
        fluid_inlettemp=fluid.inlettemp,
        fluid_massflow=fluid.massflow,
        fluid_capacity=fluid.capacity,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def fluid_temperature_borehole(fluid, peak):
    """Return the average fluid temperature in the borehole:
    :math:`T_m` [°C]

    Parameters
    ----------
    peak: qh [W]
        peak hourly ground load

    Example
    -------
    >>> fluid = FluidProperties(capacity=4200, massflow=0.050,
    ...                         inlettemp=40.2)
    >>> fluid_temperature_borehole(fluid, 12000)
    42.58095238095238

    >>> fluid = FluidProperties(capacity=4000, massflow=0.074,
    ...                         inlettemp=4.44)
    >>> fluid_temperature_borehole(fluid, -392250)
    2.750810810810811
    """
    return (fluid.inlettemp + fluid_temperature_hp_outlet(fluid, peak)) / 2.0


def r_fluid_temperature_borehole(out, fluid, peak, execute=True, **kwargs):
    """Return the average fluid temperature in the borehole:
    :math:`T_m` [°C]

    Parameters
    ----------
    peak: qh [W]
        peak hourly ground load

    Example
    -------
    >>> fluid = FluidProperties(capacity=4200, massflow=0.050,
    ...                         inlettemp=40.2)
    >>> r_fluid_temperature_borehole('fluid_temp', fluid, 'peak',
    ...                              execute=False)
    'fluid_temp = (40.2 + fluid_temp_hp_outlet) / 2.'
    """
    res = "{out} = ({fluid_inlettemp} + {fluid_temperature_hp_outlet}) / 2."
    fluid_temperature_hp_outlet = out + "_hp_outlet"
    r_fluid_temperature_hp_outlet(
        fluid_temperature_hp_outlet, fluid, peak, execute=execute
    )
    rcmd = res.format(
        out=out,
        fluid_inlettemp=fluid.inlettemp,
        fluid_temperature_hp_outlet=fluid_temperature_hp_outlet,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def bh_resistence_convetive(bh):
    """Return the conductie resistence: :math:`R_{conv}` [m K W-1]

    .. math::

        R_{conv} = \frac{1}{2\\pi \\dot r_{pin} \\dot h_{conv}}

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> bh_resistence_convetive(bh)
    0.011659702790615043
    """
    return 1.0 / (2.0 * pi * bh.pipe_inner_radius * bh.convection)


def bh_resistence_pipe(bh):
    """Return pipe resistence: :math:`R_{pipe}` [m K W-1]

    .. math::

        R_{pipe} = \frac{\frac{r_{pext}}{r_{pint}}}{2\\pi \\dot k_{pipe}}

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> bh_resistence_pipe(bh)
    0.076420594518887289

    >>> bh = Borehole(radius=0.054,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...               convection=1000.)
    >>> bh_resistence_pipe(bh)
    0.071325888217628128
    """
    return log(bh.pipe_outer_radius / bh.pipe_inner_radius) / (2.0 * pi * bh.k_pipe)


def bh_resistence_grout(bh, ground_conductivity):
    """Return grout resistence: :math:`R_{grout}` [m K W-1]

    .. math::

        R_{grout} = \frac{1}{4\\pi \\dot k_{grout}} \\dot
                    \\ln(\frac{r_{bore}}{r_{pint}}) +
                    \\ln(\frac{r_{bore}}{LU}) +
                    \frac{k_{grout} - k_{ground}}{k_{grout} + k_{ground}} *
                    \\ln(\frac{r_{bore}^4}{r_{bore}^4 - (\frac{LU}{2})^4})

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> bh_resistence_grout(bh, ground_conductivity=2.)
    0.076114233912862317

    >>> bh = Borehole(radius=0.054,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...               convection=1000.)
    >>> bh_resistence_grout(bh, ground_conductivity=2.25)
    0.060049831980162838
    """
    return (
        1.0
        / (4.0 * pi * bh.k_grout)
        * (
            log(bh.radius / bh.pipe_outer_radius)
            + log(bh.radius / bh.distance)
            + (bh.k_grout - ground_conductivity)
            / (bh.k_grout + ground_conductivity)
            * log(bh.radius**4.0 / (bh.radius**4.0 - (bh.distance / 2.0) ** 4.0))
        )
    )


def r_bh_resistence_grout(out, bh, ground_conductivity, execute=True, **kwargs):
    """Return grout resistence: :math:`R_{grout}` [m K W-1]

    .. math::

        R_{grout} = \frac{1}{4\\pi \\dot k_{grout}} \\dot
                    \\ln(\frac{r_{bore}}{r_{pint}}) +
                    \\ln(\frac{r_{bore}}{LU}) +
                    \frac{k_{grout} - k_{ground}}{k_{grout} + k_{ground}} *
                    \\ln(\frac{r_{bore}^4}{r_{bore}^4 - (\frac{LU}{2})^4})

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> r_bh_resistence_grout('bh_resistence_grout',
    ...                       bh, ground_conductivity='g_conductivity',
    ...                       execute=False)   # doctest: +NORMALIZE_WHITESPACE
    'bh_resistence_grout = (1. /
                            (4. * 3.14159265359 * 1.5) *
                            (log(0.06 / 0.0167) + log(0.06 / 0.0511) +
                            (1.5 - g_conductivity) /
                            (1.5 + g_conductivity) *
                            log(0.06^4. /      (0.06^4. - (0.0511/ 2.)^4.))))'
    """
    res = (
        "{out} = (1. / (4. * {pi} * {bh.k_grout}) * "
        "(log({bh.radius} / {bh.pipe_outer_radius}) +"
        " log({bh.radius} / {bh.distance}) +"
        " ({bh.k_grout} - {ground_conductivity}) /"
        "  ({bh.k_grout} + {ground_conductivity}) *"
        "  log({bh.radius}^4. /"
        "      ({bh.radius}^4. - ({bh.distance}/ 2.)^4.))))"
    )
    rcmd = res.format(out=out, bh=bh, ground_conductivity=ground_conductivity, pi=pi)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def bh_resistence(bh, ground_conductivity):
    """Return the effective borehole thermal resistance: Rb [m K W-1]

    .. math::

        R_{b} = R_{grout} + \frac{R_{conv} + R_{pipe}}{2}

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> bh_resistence(bh, ground_conductivity=2.)
    0.12015438256761349

    >>> bh = Borehole(radius=0.054,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...               convection=1000.)
    >>> bh_resistence(bh, ground_conductivity=2.25)
    0.10154262748428441
    """
    return (
        bh_resistence_grout(bh, ground_conductivity)
        + (bh_resistence_convetive(bh) + bh_resistence_pipe(bh)) / 2.0
    )


def r_bh_resistence(out, bh, ground_conductivity, execute=True, **kwargs):
    """Return the effective borehole thermal resistance: Rb [m K W-1]

    .. math::

        R_{b} = R_{grout} + \frac{R_{conv} + R_{pipe}}{2}

    Example
    -------
    >>> bh = Borehole(radius=0.06,
    ...               pipe_inner_radius=0.01365, pipe_outer_radius=0.0167,
    ...               k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...               convection=1000.)
    >>> r_bh_resistence('bh_resistence', bh,
    ...                 ground_conductivity='g_conductivity', execute=False)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    'bh_resistence = (bh_resistence_grout +
                      (0.0116597027906 + 0.0764205945189) / 2.)'
    """
    bh_resistence_grout = out + "_grout"
    r_bh_resistence_grout(
        bh_resistence_grout, bh, ground_conductivity, execute=execute, **kwargs
    )
    res = (
        "{out} = ({bh_resistence_grout} +"
        "         ({bh_resistence_convetive} + {bh_resistence_pipe}) / 2.)"
    )
    rcmd = res.format(
        out=out,
        bh_resistence_grout=bh_resistence_grout,
        bh_resistence_convetive=bh_resistence_convetive(bh),
        bh_resistence_pipe=bh_resistence_pipe(bh),
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def bhe_length(bhe):
    """Return the total length calculation assuming no borehole thermal
    interference: L [m]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=12000,
    ...                                    monthly=6000,
    ...                                    yearly=1500),
    ...           ground=GroundProperties(conductivity=2, diffusivity=0.086,
    ...                                   temperature=15.),
    ...           fluid=FluidProperties(capacity=4200, massflow=0.050,
    ...                                 inlettemp=40.2),
    ...           borehole=Borehole(radius=0.06,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...                             convection=1000.)
    ...           )
    >>> bhe_length(bhe)
    151.65726437306537

    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=-392250,
    ...                                    monthly=-100000,
    ...                                    yearly=-1762),
    ...           ground=GroundProperties(conductivity=2.25, diffusivity=0.06757039008,
    ...                                   temperature=12.41),
    ...           fluid=FluidProperties(capacity=4000, massflow=0.074,
    ...                                 inlettemp=4.44),
    ...           borehole=Borehole(radius=0.054,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...                             convection=1000.)
    ...           )
    >>> bhe_length(bhe)
    9899.2562646476617
    """
    long_term = ground_resistence(bhe.ground, bhe.borehole.radius, period="10y")
    medium_term = ground_resistence(bhe.ground, bhe.borehole.radius, period="1m")
    short_term = ground_resistence(bhe.ground, bhe.borehole.radius, period="6h")
    fluid_temp = fluid_temperature_borehole(bhe.fluid, bhe.ground_loads.hourly)
    resistence = bh_resistence(bhe.borehole, bhe.ground.conductivity)
    return (
        bhe.ground_loads.yearly * long_term
        + bhe.ground_loads.monthly * medium_term
        + bhe.ground_loads.hourly * short_term
        + bhe.ground_loads.hourly * resistence
    ) / (fluid_temp - bhe.ground.temperature)


def get_vars(out, bhe, basename, execute=True, **kwargs):
    basename = basename if basename else BASENAME
    # compute the temporary maps
    long_term = basename + out + "_long_term"
    r_ground_resistence(
        long_term,
        bhe.ground,
        bhe.borehole.radius,
        period="10y",
        execute=execute,
        **kwargs,
    )
    medium_term = basename + out + "_medium_term"
    r_ground_resistence(
        medium_term,
        bhe.ground,
        bhe.borehole.radius,
        period="1m",
        execute=execute,
        **kwargs,
    )
    short_term = basename + out + "_short_term"
    r_ground_resistence(
        short_term,
        bhe.ground,
        bhe.borehole.radius,
        period="6h",
        execute=execute,
        **kwargs,
    )
    fluid_temp = basename + out + "_fluid_temp"
    r_fluid_temperature_borehole(
        fluid_temp, bhe.fluid, bhe.ground_loads.hourly, execute=execute, **kwargs
    )
    resistence = basename + out + "_resistence"
    r_bh_resistence(
        resistence, bhe.borehole, bhe.ground.conductivity, execute=execute, **kwargs
    )
    return InfoVars(long_term, medium_term, short_term, fluid_temp, resistence)


def r_bhe_length(out, bhe, infovars, execute=True, **kwargs):
    """Return the total length calculation assuming no borehole thermal
    interference: L [m]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly='g_loads_6h',
    ...                                    monthly='g_loads_1m',
    ...                                    yearly='g_loads_1y'),
    ...           ground=GroundProperties(conductivity='g_conductivity',
    ...                                   diffusivity='g_diffusivity',
    ...                                   temperature='g_temperature'),
    ...           fluid=FluidProperties(capacity=4200, massflow=0.050,
    ...                                 inlettemp=40.2),
    ...           borehole=Borehole(radius=0.06,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.42, k_grout=1.5, distance=0.0511,
    ...                             convection=1000.)
    ...           )
    >>> infovars = InfoVars('l_term', 'm_term', 's_term', 'f_temp', 'res')
    >>> r_bhe_length('bhe_length', bhe, infovars, execute=False)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    'bhe_length = ((g_loads_1y * l_term +
                    g_loads_1m * m_term +
                    g_loads_6h * s_term +
                    g_loads_6h * res) /
                   (f_temp - g_temperature))'
    """
    # compute the BHE length
    res = (
        "{out} = (({bhe.ground_loads.yearly} * {iv.long_term} +"
        "          {bhe.ground_loads.monthly} * {iv.medium_term} +"
        "          {bhe.ground_loads.hourly} * {iv.short_term} +"
        "          {bhe.ground_loads.hourly} * {iv.resistence}) /"
        "           ({iv.fluid_temp} - {bhe.ground.temperature}))"
    )
    rcmd = res.format(out=out, bhe=bhe, iv=infovars)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def distance_depth_ratio(field, length):
    """Return the distance-depth ratio: B/H

    Example
    -------

    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=None)
    >>> distance_depth_ratio(field, length=9899.2562646476617)
    ...                                                    # doctest: +ELLIPSIS
    0.07394494903764...
    """
    return field.distance / (length / field.number)


def r_distance_depth_ratio(out, field, length, execute=True, **kwargs):
    """Return the distance-depth ratio: B/H

    Example
    -------

    >>> field = BoreholeField(distance='f_dist', number='f_numb',
    ...                       ratio='f_ratio', bhe=None)
    >>> r_distance_depth_ratio('dist_depth_ratio', field,
    ...                        length='bh_length', execute=False)
    'dist_depth_ratio = f_dist / (bh_length / f_numb)'
    """
    res = "{out} = {field.distance} / ({length} / {field.number})"
    rcmd = res.format(out=out, field=field, length=length)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def log_dimless_time(field, length):
    """Return the logarithm of dimensionless time: [ln(t10y/ts)]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=None,
    ...           ground=GroundProperties(conductivity=None,
    ...                                   diffusivity=0.06757039008,
    ...                                   temperature=None),
    ...           fluid=None,
    ...           borehole=None)
    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=bhe)
    >>> log_dimless_time(field, length=9899.2562646476617)
    -1.1196400189685967
    """
    return log(
        365.25
        * 10
        / ((length / field.number) ** 2 / (9 * field.bhe.ground.diffusivity))
    )


def r_log_dimless_time(out, field, length, execute=True, **kwargs):
    """Return the logarithm of dimensionless time: [ln(t10y/ts)]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=None,
    ...           ground=GroundProperties(conductivity=None,
    ...                                   diffusivity='g_diffusivity',
    ...                                   temperature=None),
    ...           fluid=None,
    ...           borehole=None)
    >>> field = BoreholeField(distance='f_dist', number='f_numb',
    ...                       ratio='f_ratio', bhe=bhe)
    >>> r_log_dimless_time('ln_dimless_time', field, length='bh_length',
    ...                    execute=False)      # doctest: +NORMALIZE_WHITESPACE
    'ln_dimless_time = log(365.25 * 10 /
                           ((bh_length / f_numb)^2 / (9 * g_diffusivity)))'
    """
    res = (
        "{out} = log(365.25 * 10 /"
        "            (({length} / {field.number})^2 /"
        "             (9 * {field.bhe.ground.diffusivity})))"
    )
    rcmd = res.format(out=out, field=field, length=length)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def _temperature_penality(
    yearly_load, ground_conductivity, length, dd_ratio, ln_dim_time, number, ratio
):
    """Return the temperature penality of a BHE field

    Example
    -------
    >>> _temperature_penality(yearly_load=-1762,
    ...                       ground_conductivity=2.25,
    ...                       length=9899.25626464766,
    ...                       dd_ratio=0.0739449490376491,
    ...                       ln_dim_time=-1.1196400189686,
    ...                       number=120, ratio=1.2)
    -0.24002529024227007
    """
    return (
        yearly_load
        / (2 * pi * ground_conductivity * length)
        * (
            TP[0]
            + TP[1] * dd_ratio
            + TP[2] * dd_ratio**2
            + TP[3] * dd_ratio**3
            + TP[4] * ln_dim_time
            + TP[5] * ln_dim_time**2
            + TP[6] * ln_dim_time**3
            + TP[7] * number
            + TP[8] * number**2
            + TP[9] * number**3
            + TP[10] * ratio
            + TP[11] * ratio**2
            + TP[12] * ratio**3
            + TP[13] * dd_ratio * ln_dim_time
            + TP[14] * dd_ratio * ln_dim_time**2
            + TP[15] * dd_ratio * number
            + TP[16] * dd_ratio * number**2
            + TP[17] * dd_ratio * ratio
            + TP[18] * dd_ratio * ratio**2
            + TP[19] * dd_ratio**2 * ln_dim_time
            + TP[20] * dd_ratio**2 * ln_dim_time**2
            + TP[21] * dd_ratio**2 * number
            + TP[22] * dd_ratio**2 * number**2
            + TP[23] * dd_ratio**2 * ratio
            + TP[24] * dd_ratio**2 * ratio**2
            + TP[25] * ln_dim_time * number
            + TP[26] * ln_dim_time * number**2
            + TP[27] * ln_dim_time * ratio
            + TP[28] * ln_dim_time * ratio**2
            + TP[29] * ln_dim_time**2 * number
            + TP[30] * ln_dim_time**2 * number**2
            + TP[31] * ln_dim_time**2 * ratio
            + TP[32] * ln_dim_time**2 * ratio**2
            + TP[33] * number * ratio
            + TP[34] * number * ratio**2
            + TP[35] * number**2 * ratio
            + TP[36] * number**2 * ratio**2
        )
    )


def _r_temperature_penality(
    out,
    yearly_load,
    ground_conductivity,
    length,
    dd_ratio,
    ln_dim_time,
    number,
    ratio,
    execute=True,
    **kwargs,
):
    """Return the temperature penality of a BHE field

    Example
    -------
    >>> _r_temperature_penality('temp_pen', yearly_load='y_load',
    ...                         ground_conductivity='g_cond', length='length',
    ...                         dd_ratio='dd_ratio', ln_dim_time='ln_dim_time',
    ...                         number='numb', ratio='ratio', execute=False)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    'temp_pen = (y_load /
                 (2 * 3.14159265359 * g_cond * length) *
                 (7.8189 +
                  -64.27 * dd_ratio +
                  153.87 * dd_ratio^2 +
                  -84.809 * dd_ratio^3 +
                  3.461 * ln_dim_time +
                  -0.94753 * ln_dim_time^2 +
                  -0.060416 * ln_dim_time^3 +
                  1.5631 * numb +
                  -0.0089416 * numb^2 +
                  1.9061e-05 * numb^3 +
                  -2.289 * ratio +
                  0.10187 * ratio^2 +
                  0.006569 * ratio^3 +
                  -40.918 * dd_ratio * ln_dim_time +
                  15.557 * dd_ratio * ln_dim_time^2 +
                  -19.107 * dd_ratio * numb +
                  0.10529 * dd_ratio * numb^2 +
                  25.501 * dd_ratio * ratio +
                  -2.1177 * dd_ratio * ratio^2 +
                  77.529 * dd_ratio^2 * ln_dim_time +
                  -50.454 * dd_ratio^2 * ln_dim_time^2 +
                  76.352 * dd_ratio^2 * numb +
                  -0.53719 * dd_ratio^2 * numb^2 +
                  -132.0 * dd_ratio^2 * ratio +
                  12.878 * dd_ratio^2 * ratio^2 +
                  0.12697 * ln_dim_time * numb +
                  -0.00040284 * ln_dim_time * numb^2 +
                  -0.072065 * ln_dim_time * ratio +
                  0.00095184 * ln_dim_time * ratio^2 +
                  -0.024167 * ln_dim_time^2 * numb +
                  9.6811e-05 * ln_dim_time^2 * numb^2 +
                  0.028317 * ln_dim_time^2 * ratio +
                  -0.0010905 * ln_dim_time^2 * ratio^2 +
                  0.12207 * numb * ratio +
                  -0.007105 * numb * ratio^2 +
                  -0.0011129 * numb^2 * ratio +
                  -0.00045566 * numb^2 * ratio^2))'
    """
    res = (
        "{out} = ({yearly_load} /"
        " (2 * {pi} * {ground_conductivity} * {length}) *"
        " ({TP[0]} +"
        "  {TP[1]} * {dd_ratio} +"
        "  {TP[2]} * {dd_ratio}^2 +"
        "  {TP[3]} * {dd_ratio}^3 +"
        "  {TP[4]} * {ln_dim_time} +"
        "  {TP[5]} * {ln_dim_time}^2 +"
        "  {TP[6]} * {ln_dim_time}^3 +"
        "  {TP[7]} * {number} +"
        "  {TP[8]} * {number}^2 +"
        "  {TP[9]} * {number}^3 +"
        "  {TP[10]} * {ratio} +"
        "  {TP[11]} * {ratio}^2 +"
        "  {TP[12]} * {ratio}^3 +"
        "  {TP[13]} * {dd_ratio} * {ln_dim_time} +"
        "  {TP[14]} * {dd_ratio} * {ln_dim_time}^2 +"
        "  {TP[15]} * {dd_ratio} * {number} +"
        "  {TP[16]} * {dd_ratio} * {number}^2 +"
        "  {TP[17]} * {dd_ratio} * {ratio} +"
        "  {TP[18]} * {dd_ratio} * {ratio}^2 +"
        "  {TP[19]} * {dd_ratio}^2 * {ln_dim_time} +"
        "  {TP[20]} * {dd_ratio}^2 * {ln_dim_time}^2 +"
        "  {TP[21]} * {dd_ratio}^2 * {number} +"
        "  {TP[22]} * {dd_ratio}^2 * {number}^2 +"
        "  {TP[23]} * {dd_ratio}^2 * {ratio} +"
        "  {TP[24]} * {dd_ratio}^2 * {ratio}^2 +"
        "  {TP[25]} * {ln_dim_time} * {number} +"
        "  {TP[26]} * {ln_dim_time} * {number}^2 +"
        "  {TP[27]} * {ln_dim_time} * {ratio} +"
        "  {TP[28]} * {ln_dim_time} * {ratio}^2 +"
        "  {TP[29]} * {ln_dim_time}^2 * {number} +"
        "  {TP[30]} * {ln_dim_time}^2 * {number}^2 +"
        "  {TP[31]} * {ln_dim_time}^2 * {ratio} +"
        "  {TP[32]} * {ln_dim_time}^2 * {ratio}^2 +"
        "  {TP[33]} * {number} * {ratio} +"
        "  {TP[34]} * {number} * {ratio}^2 +"
        "  {TP[35]} * {number}^2 * {ratio} +"
        "  {TP[36]} * {number}^2 * {ratio}^2))"
    )
    rcmd = res.format(
        out=out,
        yearly_load=yearly_load,
        ground_conductivity=ground_conductivity,
        length=length,
        dd_ratio=dd_ratio,
        ln_dim_time=ln_dim_time,
        number=number,
        ratio=ratio,
        TP=TP,
        pi=pi,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def _get_length(
    yearly,
    long_term,
    monthly,
    medium_term,
    peak,
    short_term,
    borehole_res,
    ftemp,
    gtemp,
    temp_penality,
):
    """Return a first attempt of the BHE field lenght

    Example
    -------
    >>> _get_length(yearly=-1762, long_term=0.16963475237211000,
    ...             monthly=-100000, medium_term=0.16000118270019600,
    ...             peak=-392250, short_term=0.10067477057511400,
    ...             borehole_res=0.1015426274842840,
    ...             ftemp=2.750810810810810, gtemp=12.41,
    ...             temp_penality=-0.2400252902422710)
    10151.515582310705
    """
    # print(dict(yearly=yearly, long_term=long_term, monthly=monthly,
    #            medium_term=medium_term, peak=peak, short_term=short_term,
    #            borehole_res=borehole_res, ftemp=ftemp, gtemp=gtemp,
    #            temp_penality=temp_penality))
    return (
        yearly * long_term
        + monthly * medium_term
        + peak * short_term
        + peak * borehole_res
    ) / (ftemp - gtemp - temp_penality)


def _r_get_length(
    out,
    yearly_load,
    long_term,
    monthly_load,
    medium_term,
    peak_load,
    short_term,
    borehole_resistence,
    fluid_temp,
    ground_temp,
    temperature_penality,
    execute=True,
    **kwargs,
):
    """Return a first attempt of the BHE field lenght

    Example
    -------
    >>> _r_get_length('length', yearly_load='y_load', long_term='l_term',
    ...               monthly_load='m_load', medium_term='m_term',
    ...               peak_load='p_load', short_term='s_term',
    ...               borehole_resistence='bh_resistence',
    ...               fluid_temp='f_temp', ground_temp='g_temp',
    ...               temperature_penality='temp_pen', execute=False)
    ...                                        # doctest: +NORMALIZE_WHITESPACE
    'length = ((y_load * l_term +
                m_load * m_term +
                p_load * s_term +
                p_load * bh_resistence) /
               (f_temp - g_temp - temp_pen))'
    """
    res = (
        "{out} = (({yearly_load} * {long_term} +"
        "          {monthly_load} * {medium_term} +"
        "          {peak_load} * {short_term} +"
        "          {peak_load} * {borehole_resistence}) /"
        "         ({fluid_temp} - {ground_temp} - {temp_penality}))"
    )
    rcmd = res.format(
        out=out,
        yearly_load=yearly_load,
        long_term=long_term,
        monthly_load=monthly_load,
        medium_term=medium_term,
        peak_load=peak_load,
        short_term=short_term,
        borehole_resistence=borehole_resistence,
        fluid_temp=fluid_temp,
        ground_temp=ground_temp,
        temp_penality=temperature_penality,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def temperature_penality(field, length):
    """Return the temperature penalty: Tp [°C]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=-392250,
    ...                                    monthly=-100000,
    ...                                    yearly=-1762),
    ...           ground=GroundProperties(conductivity=2.25,
    ...                                   diffusivity=0.06757039008,
    ...                                   temperature=12.41),
    ...           fluid=FluidProperties(capacity=4000, massflow=0.074,
    ...                                 inlettemp=4.44),
    ...           borehole=Borehole(radius=0.054,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...                             convection=1000.)
    ...           )
    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=bhe)
    >>> temperature_penality(field, 9899.25626464766)
    -0.24002529024227098
    """
    dd_ratio = distance_depth_ratio(field, length)
    ln_dim_time = log_dimless_time(field, length)
    return _temperature_penality(
        field.bhe.ground_loads.yearly,
        field.bhe.ground.conductivity,
        length,
        dd_ratio,
        ln_dim_time,
        field.number,
        field.ratio,
    )


def r_temperature_penality(out, field, length, execute=True, **kwargs):
    """Return the temperature penalty: Tp [°C]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=-392250,
    ...                                    monthly=-100000,
    ...                                    yearly=-1762),
    ...           ground=GroundProperties(conductivity=2.25,
    ...                                   diffusivity=0.06757039008,
    ...                                   temperature=12.41),
    ...           fluid=FluidProperties(capacity=4000, massflow=0.074,
    ...                                 inlettemp=4.44),
    ...           borehole=Borehole(radius=0.054,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...                             convection=1000.)
    ...           )
    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=bhe)
    >>> r_temperature_penality('temp_pen', field, 'length', execute=False)
    ...                                                    # doctest: +ELLIPSIS
    'temp_pen = (...)'
    """
    dd_ratio = BASENAME + "dd_ratio"
    r_distance_depth_ratio(dd_ratio, field, length, execute=execute, **kwargs)
    dimless_time = BASENAME + "ln_dimless_time"
    r_log_dimless_time(dimless_time, field, length, execute=execute, **kwargs)
    return _r_temperature_penality(
        out,
        field.bhe.ground_loads.yearly,
        field.bhe.ground.conductivity,
        length,
        dd_ratio,
        dimless_time,
        field.number,
        field.ratio,
        execute=execute,
        **kwargs,
    )


def field_length(field, tol=1e-3):
    """Return the total borefield length: L [m]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=-392250,
    ...                                    monthly=-100000,
    ...                                    yearly=-1762),
    ...           ground=GroundProperties(conductivity=2.25,
    ...                                   diffusivity=0.06757039008,
    ...                                   temperature=12.41),
    ...           fluid=FluidProperties(capacity=4000, massflow=0.074,
    ...                                 inlettemp=4.44),
    ...           borehole=Borehole(radius=0.054,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...                             convection=1000.)
    ...           )
    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=bhe)
    >>> field_length(field)
    10149.682910753265
    """
    # extract common variables
    long_term = ground_resistence(
        field.bhe.ground, field.bhe.borehole.radius, period="10y"
    )
    medium_term = ground_resistence(
        field.bhe.ground, field.bhe.borehole.radius, period="1m"
    )
    short_term = ground_resistence(
        field.bhe.ground, field.bhe.borehole.radius, period="6h"
    )
    borehole_res = bh_resistence(field.bhe.borehole, field.bhe.ground.conductivity)
    peak = field.bhe.ground_loads.hourly
    monthly = field.bhe.ground_loads.monthly
    yearly = field.bhe.ground_loads.yearly
    ftemp = fluid_temperature_borehole(field.bhe.fluid, peak)
    gtemp = field.bhe.ground.temperature
    # start iteration get length for a single BHE
    length0 = bhe_length(field.bhe)

    # get correct length considering the bhe interferences
    length1 = _get_length(
        yearly,
        long_term,
        monthly,
        medium_term,
        peak,
        short_term,
        borehole_res,
        ftemp,
        gtemp,
        temperature_penality(field, length0),
    )
    while abs(length1 - length0) > tol:
        length0 = length1
        length1 = _get_length(
            yearly,
            long_term,
            monthly,
            medium_term,
            peak,
            short_term,
            borehole_res,
            ftemp,
            gtemp,
            temperature_penality(field, length0),
        )
    return length1


def abs_diff_gt_tol(out, raster_a, raster_b, tol=1e-3, execute=True, **kwargs):
    res = "{out} = if(abs({raster_a} - {raster_b}) > {tol}, 1, 0)"
    rcmd = res.format(out=out, raster_a=raster_a, raster_b=raster_b, tol=tol)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
        info = grast.raster_info(out)
    else:
        info = dict(max=0)
    return True if info["max"] == 1 else False


def r_field_length(
    out,
    field,
    infovars,
    basename=BASENAME,
    length_single=None,
    tol=1e-3,
    execute=True,
    **kwargs,
):
    """Return the total borefield length: L [m]

    Example
    -------
    >>> bhe = BoreholeExchanger(
    ...           ground_loads=GroundLoads(hourly=-392250,
    ...                                    monthly=-100000,
    ...                                    yearly=-1762),
    ...           ground=GroundProperties(conductivity=2.25,
    ...                                   diffusivity=0.06757039008,
    ...                                   temperature=12.41),
    ...           fluid=FluidProperties(capacity=4000, massflow=0.074,
    ...                                 inlettemp=4.44),
    ...           borehole=Borehole(radius=0.054,
    ...                             pipe_inner_radius=0.01365,
    ...                             pipe_outer_radius=0.0167,
    ...                             k_pipe=0.45, k_grout=1.73, distance=0.0471,
    ...                             convection=1000.)
    ...           )
    >>> field = BoreholeField(distance=6.1, number=120, ratio=1.2, bhe=bhe)
    >>> infovars = get_vars('bhe_field_length', bhe, BASENAME, execute=False)
    >>> r_field_length('bhe_field_length', field, infovars, execute=False)
    'bhe_field_length'
    """
    # extract common variables
    peak = field.bhe.ground_loads.hourly
    monthly = field.bhe.ground_loads.monthly
    yearly = field.bhe.ground_loads.yearly
    gtemp = field.bhe.ground.temperature
    # start iteration get length for a single BHE
    len_template = basename + out + "_lenght_{:02d}"
    length0 = len_template.format(0) if length_single is None else length_single
    if not exists(length0):
        r_bhe_length(length0, field.bhe, infovars, execute=execute, **kwargs)

    temp_penality = basename + out + "_temp_penality"
    r_temperature_penality(temp_penality, field, length0, execute=execute, **kwargs)

    # get correct length considering the bhe interferences
    length1 = len_template.format(1)
    _r_get_length(
        length1,
        yearly,
        infovars.long_term,
        monthly,
        infovars.medium_term,
        peak,
        infovars.short_term,
        infovars.resistence,
        infovars.fluid_temp,
        gtemp,
        temp_penality,
        execute=execute,
        **kwargs,
    )
    diff_template = basename + out + "_absdiff_{:02d}"
    index = 1
    diff = diff_template.format(index)
    while abs_diff_gt_tol(diff, length0, length1, tol=tol, execute=execute, **kwargs):
        index += 1
        length0 = length1
        length1 = len_template.format(index)
        _r_get_length(
            length1,
            yearly,
            infovars.long_term,
            monthly,
            infovars.medium_term,
            peak,
            infovars.short_term,
            infovars.resistence,
            infovars.fluid_temp,
            gtemp,
            temp_penality,
            execute=execute,
            **kwargs,
        )
    rename("raster", length1, out)
    return out


if __name__ == "__main__":
    import doctest

    doctest.testmod()
