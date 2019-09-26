#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""

import sys
from collections import namedtuple


# globals
MTLFILE = ''
DUMMY_MAPCALC_STRING_RADIANCE = 'Radiance'
DUMMY_MAPCALC_STRING_DN = 'DigitalNumber'


# helper functions
def set_mtlfile():
    """
    Set user defined MTL file, if any
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return False


class Landsat8_MTL():
    """
    Retrieve metadata from a Landsat8 MTL file.
    See <http://landsat.usgs.gov/Landsat8_Using_Product.php>.

    ToDo:

    - Implement toar_reflectance
    - Implement mechanism to translate QA pixel values to QA bits, and vice
      versa?
    - Other Landsat8 related functions/algorithms?
    """

    def __init__(self, mtl_filename):
        """
        Initialise class object based on a Landsat8 MTL filename.
        """
        # read lines
        with open(mtl_filename, 'r') as mtl_file:
                mtl_lines = mtl_file.readlines()

        # close and remove 'mtl_file'
        mtl_file.close()
        del(mtl_file)

        # clean and convert MTL lines in to a named tuple
        self.mtl = self._to_namedtuple(mtl_lines, 'metadata')
        self._set_attributes()

        # shorten LANDSAT_SCENE_ID, SENSOR_ID
        self.scene_id = self.mtl.LANDSAT_SCENE_ID
        self.sensor = self.mtl.SENSOR_ID

        # bounding box related
        self.corner_ul = (self.mtl.CORNER_UL_LAT_PRODUCT,
                          self.mtl.CORNER_UL_LON_PRODUCT)
        self.corner_lr = (self.mtl.CORNER_LR_LAT_PRODUCT,
                          self.mtl.CORNER_LR_LON_PRODUCT)
        self.corner_ul_projection = (self.mtl.CORNER_UL_PROJECTION_X_PRODUCT,
                                     self.mtl.CORNER_UL_PROJECTION_Y_PRODUCT)
        self.corner_lr_projection = (self.mtl.CORNER_LR_PROJECTION_X_PRODUCT,
                                     self.mtl.CORNER_LR_PROJECTION_Y_PRODUCT)
        self.cloud_cover = self.mtl.CLOUD_COVER

    def _to_namedtuple(self, list_of_lines, name_for_tuple):
        """
        This function performs the following actions on the given
        'list_of_lines':
        - excludes lines containing the strings 'GROUP' and 'END'
        - removes whitespaces and doublequotes from strings
        - converts list of lines in to a named tuple
        """
        import string

        # exclude lines containing 'GROUP', 'END'
        lines = [line.strip() for line in list_of_lines
                 if not any(x in line for x in ('GROUP', 'END'))]

        # keep a copy, maybe useful?
        self._mtl_lines = lines
        del(list_of_lines)

        # empty variables to hold values
        field_names = []
        field_values = []

        # loop over lines, do some cleaning
        for idx in range(len(lines)):

            # split line in '='
            line = lines[idx]
            line_split = line.split('=')

            # get field name & field value, clean whitespaces and "
            field_name = line_split[0].strip()
            field_names.append(field_name)
            field_value = line_split[1].strip()
            field_value = field_value.translate(string.maketrans("", "",), '"')
            field_values.append(field_value)

        # named tuple
        named_tuple = namedtuple(name_for_tuple, field_names)

        # return named tuple
        return named_tuple(*field_values)

    def _set_attributes(self):
        """
        Set all parsed field names and values, from the MTL file, fed to the
        named tuple 'self.mtl', as attributes to the object.
        """
        for field in self.mtl._fields:
            field_lowercase = field.lower()
            field_value = getattr(self.mtl, field)
            setattr(self, field_lowercase, field_value)

    def __str__(self):
        """
        Return a string representation of the scene's id.
        """
        msg = 'Landsat8 scene ID:'
        return msg + ' ' + self.scene_id

    def _get_mtl_lines(self):
        """
        Return the "hidden" copy of the MTL lines before cleaning (lines
        containing 'GROUP' or 'END' are though excluded).
        """
        return self._mtl_lines

    def toar_radiance(self, bandnumber):
        """
        Note, this function returns a valid expression for GRASS GIS' r.mapcalc
        raster processing module.

        Conversion of Digital Numbers to TOA Radiance. OLI and TIRS band data
        can be converted to TOA spectral radiance using the radiance rescaling
        factors provided in the metadata file:

        Lλ = ML * Qcal + AL

        where:

        - Lλ = TOA spectral radiance (Watts/( m2 * srad * μm))

        - ML = Band-specific multiplicative rescaling factor from the metadata
        (RADIANCE_MULT_BAND_x, where x is the band number)

        - AL = Band-specific additive rescaling factor from the metadata
        (RADIANCE_ADD_BAND_x, where x is the band number)

        - Qcal = Quantized and calibrated standard product pixel values (DN)

        Some code borrowed from
        <https://github.com/micha-silver/grass-landsat8/blob/master/r.in.landsat8.py>
        """
        multiplicative_factor = getattr(self.mtl, ('RADIANCE_MULT_BAND_' +
                                        str(bandnumber)))
        # print("ML:", multiplicative_factor)

        additive_factor = getattr(self.mtl, 'RADIANCE_ADD_BAND_' +
                                  str(bandnumber))
        # print("AL:", additive_factor)

        formula = '{ML}*{DUMMY_DN} + {AL}'
        mapcalc = formula.format(ML=multiplicative_factor,
                                 DUMMY_DN=DUMMY_MAPCALC_STRING_DN,
                                 AL=additive_factor)

        return mapcalc

    def toar_reflectance(self, bandnumber):
        """
        Note, this function returns a valid expression for GRASS GIS' r.mapcalc
        raster processing module.

        Conversion to TOA Reflectance OLI band data can also be converted to
        TOA planetary reflectance using reflectance rescaling coefficients
        provided in the product metadata file (MTL file).  The following
        equation is used to convert DN values to TOA reflectance for OLI data
        as follows:

                ρλ' = MρQcal + Aρ

        where:

        - ρλ' = TOA planetary reflectance, without correction for solar angle.
          Note that ρλ' does not contain a correction for the sun angle.

        - Mρ  = Band-specific multiplicative rescaling factor from the metadata
          (REFLECTANCE_MULT_BAND_x, where x is the band number)

        - Aρ  = Band-specific additive rescaling factor from the metadata
          (REFLECTANCE_ADD_BAND_x, where x is the band number)

        - Qcal = Quantized and calibrated standard product pixel values (DN)

        TOA reflectance with a correction for the sun angle is then:

        ρλ = ρλ' = ρλ'  ### Fix This!
        cos(θSZ) sin(θSE) ### Fix This!

        where:

        - ρλ = TOA planetary reflectance
        - θSE = Local sun elevation angle. The scene center sun elevation angle
          in degrees is provided in the metadata (SUN_ELEVATION).
        - θSZ = Local solar zenith angle;
        - θSZ = 90° - θSE

        For more accurate reflectance calculations, per pixel solar angles
        could be used instead of the scene center solar angle, but per pixel
        solar zenith angles are not currently provided with the Landsat 8
        products.
        """
        pass

    def radiance_to_temperature(self, bandnumber):
        """
        Note, this function returns a valid expression for GRASS GIS' r.mapcalc
        raster processing module.

        Conversion to At-Satellite Brightness Temperature
        TIRS band data can be converted from spectral radiance to brightness
        temperature using the thermal constants provided in the metadata file:

        T = K2 / ln( (K1/Lλ) + 1 )

        where:

        - T = At-satellite brightness temperature (K)

        - Lλ = TOA spectral radiance (Watts/( m2 * srad * μm)), below
          'DUMMY_RADIANCE'

        - K1 = Band-specific thermal conversion constant from the metadata
          (K1_CONSTANT_BAND_x, where x is the band number, 10 or 11)

        - K2 = Band-specific thermal conversion constant from the metadata
          (K2_CONSTANT_BAND_x, where x is the band number, 10 or 11)
        """
        k2 = getattr(self.mtl, ('K2_CONSTANT_BAND_' + str(bandnumber)))
        k1 = getattr(self.mtl, ('K1_CONSTANT_BAND_' + str(bandnumber)))

        formula = '{K2} / ( log({K1} / {DUMMY_RADIANCE} + 1))'
        mapcalc = formula.format(K2=k2,
                                 K1=k1,
                                 DUMMY_RADIANCE=DUMMY_MAPCALC_STRING_RADIANCE)

        return mapcalc


def main():
    """
    Main program.
    """
    if set_mtlfile():
        MTLFILE = set_mtlfile()
        print("| Reading metadata from:", MTLFILE)
    else:
        MTLFILE = ''


if __name__ == "__main__":
    main()
