from grass.pygrass.modules.shortcuts import general as g
from dummy_mapcalc_strings import replace_dummies
from constants import DUMMY_MAPCALC_STRING_FROM_GLC
from constants import EQUATION
import grass.script as grass
from helpers import run

def determine_average_emissivity(
        outname,
        emissivity_output,
        landcover_map,
        avg_lse_expression,
        quiet=True,
        ):
    """
    Produce an average emissivity map based on FROM-GLC map covering the region
    of interest.
    """
    msg = ('\n|i Determining average land surface emissivity based on a look-up table ')
    if not quiet:
        msg += ('| Expression:\n\n {exp}')
        msg = msg.format(exp=avg_lse_expression)
    g.message(msg)
    avg_lse_expression = replace_dummies(
            avg_lse_expression,
            instring=DUMMY_MAPCALC_STRING_FROM_GLC,
            outstring=landcover_map,
    )
    avg_lse_equation = EQUATION.format(
            result=outname,
            expression=avg_lse_expression,
    )
    grass.mapcalc(avg_lse_equation, overwrite=True)

    if not quiet:
        run('r.info', map=outname, flags='r')


    # save land surface emissivity map?
    if emissivity_output:
        run('g.rename', raster=(outname, emissivity_output))


def determine_delta_emissivity(
        outname,
        delta_emissivity_output,
        landcover_map,
        delta_lse_expression,
        quiet=True,
    ):
    """
    Produce a delta emissivity map based on the FROM-GLC map covering the
    region of interest.
    """
    msg = ('\n|i Determining delta land surface emissivity based on a '
           'look-up table ')
    if not quiet:
        msg += ('| Expression:\n\n {exp}')
        msg = msg.format(exp=delta_lse_expression)
    g.message(msg)

    delta_lse_expression = replace_dummies(delta_lse_expression,
                                           instring=DUMMY_MAPCALC_STRING_FROM_GLC,
                                           outstring=landcover_map)

    delta_lse_equation = EQUATION.format(result=outname,
                                         expression=delta_lse_expression)

    grass.mapcalc(delta_lse_equation, overwrite=True)

    if not quiet:
        run('r.info', map=outname, flags='r')


    # save delta land surface emissivity map?
    if delta_emissivity_output:
        run('g.rename', raster=(outname, delta_emissivity_output))
