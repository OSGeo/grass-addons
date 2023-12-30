#!/usr/bin/env python

"""
@author:
    - code: Pietro Zambelli
    - methodology: Alessandro Casasso & Rajandrea Sethi


Alessandro Casasso, Rajandrea Sethi, 2016,
"G.POT: A quantitative method for the assessment and mapping of the
shallow geothermal potential"
Energy 106, p 765 -- 773
http://dx.doi.org/10.1016/j.energy.2016.03.091


Variables
---------

QBHE is the yearly average thermal load that can sustainably be exchanged by a
Borehole Heat Exchanger with a certain length, for a given ground condition.

The geothermal potential can be calculated both for cooling and
or heating mode and it depends on:

ground thermal properties:
    - thermal conductivity (l),
    - thermal capacity (rc) and
    - undisturbed ground temperature (T0);
geometrical and thermal properties of BHE:
    - borehole depth (L),
    - borehole radius (rb) and
    - thermal resistance (Rb);
operative criteria:
    - minimum temperature of the carrier fluid during heating mode (Tlim)
    - maximum temperature of the carrier fluid during cooling mode
    - length of heating season (tc);
    - lenght of cooling season (tc);
simulation parameters:
    - simulation time (ts): time over which the sustainability of the
      geo-exchange is evaluated.

"""
from numpy import log, pi, sqrt

from grass.script import raster as grast


def get_borehole_resistence(
    borehole_radius, pipe_radius, number_pipes, grout_conductivity
):
    """Borehole thermal resistence, following the Shonder and Beck (2000)
    method.

    Example
    -------
    >>> get_borehole_resistence(borehole_radius=0.075, pipe_radius=0.016,
    ...                         number_pipes=4, grout_conductivity=2.)
    ...                                                   # doctest: +ELLIPSIS
    0.067780287314088528
    """
    return (
        1.0
        / (2 * pi * grout_conductivity)
        * log(borehole_radius / (sqrt(number_pipes) * pipe_radius))
    )


def norm_time(time, borehole_radius, ground_conductivity, ground_capacity):
    """Normalized time in s

    Example
    -------
    >>> norm_time(180 * 24 * 60 * 60, borehole_radius=0.075,
    ...           ground_conductivity=2., ground_capacity=2.5)
    ...                                                   # doctest: +ELLIPSIS
    0.00011302806712962963
    >>> norm_time(50 * 365 * 24 * 60 * 60, borehole_radius=0.075,
    ...           ground_conductivity=2., ground_capacity=2.5)
    ...                                                   # doctest: +ELLIPSIS
    1.1147973744292237e-06
    """
    return borehole_radius**2.0 / (
        4 * ground_conductivity / ground_capacity * 0.000001 * time
    )


def r_norm_time(
    out,
    time,
    borehole_radius,
    ground_conductivity,
    ground_capacity,
    execute=True,
    **kwargs,
):
    """Normalized time in s

    Example
    -------
    >>> r_norm_time('norm_time', 180 * 24 * 60 * 60, borehole_radius=0.075,
    ...           ground_conductivity=2., ground_capacity=2.5, execute=False)
    'norm_time = (0.075^2. / (4 * 2.0 / 2.5 * 0.000001 * 15552000))'
    >>> r_norm_time('norm_time', 50 * 365 * 24 * 60 * 60, borehole_radius=0.075,
    ...             ground_conductivity='ground_conductivity',
    ...             ground_capacity='ground_capacity', execute=False)
    'norm_time = (0.075^2. / (4 * ground_conductivity / ground_capacity * 0.000001 * 1576800000))'
    """
    res = (
        "{out} = ({borehole_radius}^2. / (4 * {ground_conductivity} / "
        "{ground_capacity} * 0.000001 * {time}))"
    )
    rcmd = res.format(
        out=out,
        borehole_radius=borehole_radius,
        ground_conductivity=ground_conductivity,
        ground_capacity=ground_capacity,
        time=time,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def r_tc(out, heating_season, execute=True, **kwargs):
    """
    Example
    -------
    >>> r_tc('tc', 180, execute=False)
    'tc = 180 / 365.'
    """
    res = "{out} = {heating_season} / 365."
    rcmd = res.format(out=out, heating_season=heating_season)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def norm_thermal_alteration(tc, uc, us):
    """Normalized thermal alteration

    Example
    -------

    >>> norm_thermal_alteration(tc=180./365., uc=1.130280671296e-4,
    ...                         us=1.114797374429e-6)     # doctest: +ELLIPSIS
    8.69904482466...

    """
    # -0.619*180./365. * log(1.114797374429e-6) + (0.532* 180./365. - 0.962) *
    # log(1.130280671296e-4)-0.455 * 180./ 365.- 1.619
    return -0.619 * tc * log(us) + (0.532 * tc - 0.962) * log(uc) - 0.455 * tc - 1.619


def r_norm_thermal_alteration(out, tc, uc, us, execute=True, **kwargs):
    """Normalized thermal alteration

    Example
    -------

    >>> r_norm_thermal_alteration(out='gmax', tc=180./365.,
    ...                           uc=1.114797374429E-06,
    ...                           us=1.130280671296E-04, execute=False)
    ...                                                   # doctest: +ELLIPSIS
    'gmax = (-0.619 * 0.493150684... * log(0.000113028...) + (0.532 * 0.4931506849... - 0.962) * log(1.11479737...e-06) - 0.455 * 0.493150684... - 1.619)'
    >>> r_norm_thermal_alteration(out='gmax', tc=180./365., uc='uc',
    ...                           us='us', execute=False) # doctest: +ELLIPSIS
    'gmax = (-0.619 * 0.493150684... * log(us) + (0.532 * 0.4931506849... - 0.962) * log(uc) - 0.455 * 0.493150684... - 1.619)'
    """
    res = (
        "{out} = (-0.619 * {tc} * log({us}) + "
        "(0.532 * {tc} - 0.962) * log({uc}) - 0.455 * {tc} - 1.619)"
    )
    rcmd = res.format(out=out, tc=tc, us=us, uc=uc)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def power(
    tc,
    ground_conductivity,
    ground_temperature,
    fluid_limit_temperature,
    borehole_length,
    borehole_resistence,
    gmax,
):
    """Return the potential power using the g.pot method in W

    Example
    -------
    >>> power(tc=180./365., ground_conductivity=2., ground_temperature=10.,
    ...       fluid_limit_temperature=-2.,
    ...       borehole_length=100., borehole_resistence=0.1,
    ...       gmax=8.6990448246621082)                     # doctest: +ELLIPSIS
    844.472333...
    """
    return (
        8.0
        * (ground_temperature - fluid_limit_temperature)
        * ground_conductivity
        * borehole_length
        * tc
    ) / (gmax + 4 * pi * ground_conductivity * borehole_resistence)


def r_power(
    out,
    tc,
    ground_conductivity,
    ground_temperature,
    fluid_limit_temperature,
    borehole_length,
    borehole_resistence,
    gmax,
    execute=True,
    **kwargs,
):
    """Return the potential power using the g.pot method in W

    Example
    -------
    >>> r_power(out='power', tc=180./365.,
    ...         ground_conductivity='ground_conductivity',
    ...         ground_temperature='ground_temperature',
    ...         fluid_limit_temperature=-2.,
    ...         borehole_length=100., borehole_resistence=0.1,
    ...         gmax='gmax', execute=False)                # doctest: +ELLIPSIS
    'power = ((8. * (ground_temperature - -2.0) * ground_conductivity * 100.0 * 0.493150684...) / (gmax + 4 * 3.141592653... * ground_conductivity * 0.1))'
    """
    res = (
        "{out} = ((8. * ({ground_temperature} - {fluid_limit_temperature}) * "
        "{ground_conductivity} * {borehole_length} * {tc}) / "
        "({gmax} + 4 * {pi} * {ground_conductivity} * {borehole_resistence}))"
    )
    rcmd = res.format(
        out=out,
        tc=tc,
        ground_conductivity=ground_conductivity,
        ground_temperature=ground_temperature,
        fluid_limit_temperature=fluid_limit_temperature,
        pi=pi,
        borehole_length=borehole_length,
        borehole_resistence=borehole_resistence,
        gmax=gmax,
    )
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


def r_energy(out, power, execute=True, **kwargs):
    """Return the potential energy using the g.pot method in MWh/year

    Example
    -------
    >>> r_energy('energy', 'power', execute=False)
    'energy = 0.00876 * power'
    """
    res = "{out} = 0.00876 * {power}"
    rcmd = res.format(out=out, power=power)
    if execute:
        grast.mapcalc(rcmd, **kwargs)
    return rcmd


if __name__ == "__main__":
    import doctest

    doctest.testmod()
