from helpers import extract_number_from_string
from helpers import tmp_map_name
from landsat8_mtl import Landsat8_MTL
from radiance import digital_numbers_to_radiance
from radiance import radiance_to_brightness_temperature
from grass.pygrass.modules.shortcuts import general as g
from dummy_mapcalc_strings import replace_dummies
from constants import DUMMY_MAPCALC_STRING_AVG_LSE
from constants import DUMMY_MAPCALC_STRING_DELTA_LSE
from constants import DUMMY_MAPCALC_STRING_CWV
from constants import DUMMY_MAPCALC_STRING_T10
from constants import DUMMY_MAPCALC_STRING_T11
from constants import EQUATION
import grass.script as grass
from helpers import run

def tirs_to_at_satellite_temperature(
        tirs_1x,
        mtl_file,
        brightness_temperature_prefix=None,
        null=False,
        quiet=True):
    """
    Helper function to convert TIRS bands 10 or 11 in to at-satellite
    temperatures.

    This function uses the pre-defined functions:

    - extract_number_from_string()
    - digital_numbers_to_radiance()
    - radiance_to_brightness_temperature()

    The inputs are:

    - a name for the input tirs band (10 or 11)
    - a Landsat8 MTL file

    The output is a temporary at-Satellite Temperature map.
    """
    # which band number and MTL file
    band_number = extract_number_from_string(tirs_1x)
    tmp_radiance = tmp_map_name('radiance') + '.' + band_number
    tmp_brightness_temperature = tmp_map_name('brightness_temperature') + '.' + \
        band_number
    landsat8 = Landsat8_MTL(mtl_file)

    # rescale DNs to spectral radiance
    radiance_expression = landsat8.toar_radiance(band_number)
    digital_numbers_to_radiance(
            tmp_radiance,
            tirs_1x,
            radiance_expression,
            null,
            quiet,
    )

    # convert spectral radiance to at-satellite temperature
    temperature_expression = landsat8.radiance_to_temperature(band_number)
    radiance_to_brightness_temperature(
            tmp_brightness_temperature,
            tmp_radiance,
            temperature_expression,
            quiet,
    )

    # save Brightness Temperature map?
    if brightness_temperature_prefix:
        bt_output = brightness_temperature_prefix + band_number
        run('g.rename', raster=(tmp_brightness_temperature, bt_output))
        tmp_brightness_temperature = bt_output

    return tmp_brightness_temperature


def estimate_lst(
        outname,
        t10,
        t11,
        landcover_map,
        landcover_class,
        avg_lse_map,
        delta_lse_map,
        cwv_map,
        lst_expression,
        rounding,
        celsius,
        quiet=True,
    ):
    """
    Produce a Land Surface Temperature map based on a mapcalc expression
    returned from a SplitWindowLST object.

    Parameters
    ----------
    outname

    t10

    t11

    landcover_map

    landcover_class

    avg_lse_map

    delta_lse_map

    cwv_map

    lst_expression

    rounding

    celsius

    quiet

    Inputs are:

    - brightness temperature maps t10, t11
    - column water vapor map
    - a temporary filename
    - a valid mapcalc expression
    """
    msg = '\n|i Estimating land surface temperature '
    g.message(msg)

    if not quiet:
        msg += "| Expression:\n"
        msg = lst_expression
        msg += '\n'
        g.message(msg)

    if landcover_map:
        split_window_expression = replace_dummies(lst_expression,
                                                  in_avg_lse=DUMMY_MAPCALC_STRING_AVG_LSE,
                                                  out_avg_lse=avg_lse_map,
                                                  in_delta_lse=DUMMY_MAPCALC_STRING_DELTA_LSE,
                                                  out_delta_lse=delta_lse_map,
                                                  in_cwv=DUMMY_MAPCALC_STRING_CWV,
                                                  out_cwv=cwv_map,
                                                  in_ti=DUMMY_MAPCALC_STRING_T10,
                                                  out_ti=t10,
                                                  in_tj=DUMMY_MAPCALC_STRING_T11,
                                                  out_tj=t11)
    elif landcover_class:
        split_window_expression = replace_dummies(lst_expression,
                                                  in_cwv=DUMMY_MAPCALC_STRING_CWV,
                                                  out_cwv=cwv_map,
                                                  in_ti=DUMMY_MAPCALC_STRING_T10,
                                                  out_ti=t10,
                                                  in_tj=DUMMY_MAPCALC_STRING_T11,
                                                  out_tj=t11)

    if rounding:
        split_window_expression = '(round({swe}, 2, 0.5))'.format(swe=split_window_expression)

    if celsius:
        split_window_expression = '({swe}) - 273.15'.format(swe=split_window_expression)


    split_window_equation = EQUATION.format(
            result=outname,
            expression=split_window_expression,
    )
    grass.mapcalc(
            split_window_equation,
            overwrite=True,
    )
    if not quiet:
        run('r.info', map=outname, flags='r')
