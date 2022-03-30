# -*- coding: utf-8 -*-

"""
A class for the Split Window Algorithm for Land Surface Temperature estimation
@author: nik | Created on Wed Mar 18 11:28:45 2015 | Updated on June 2020
"""

from constants import BARREN_LAND_CLASS_STRING
from constants import DUMMY_MAPCALC_STRING_T10
from constants import DUMMY_MAPCALC_STRING_T11
from constants import DUMMY_MAPCALC_STRING_AVG_LSE
from constants import DUMMY_MAPCALC_STRING_DELTA_LSE
from constants import DUMMY_MAPCALC_STRING_FROM_GLC
from constants import DUMMY_MAPCALC_STRING_CWV
from constants import FROM_GLC_CODES
from constants import FROM_GLC_LEGEND
from constants import LST_FORMULA
from data_validation import check_t1x_range
from data_validation import check_cwv
import csv_to_dictionary as coefficients

EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOR = coefficients.get_column_water_vapor()
import random


class SplitWindowLST:
    """
    A class implementing the split-window algorithm for Landsat8 imagery

    Inputs:

    - The class itself requires only a string for 'landcover' which is:

      1) a fixed land cover class string (one from the classes defined in the
         FROM-GLC legend)

      2) a land cover class code (integer) one from the classes defined in the
         FROM-GLC classification scheme.

    - Inputs for individual functions vary, look at their definitions.

    Outputs:

    - Valid expressions for GRASS GIS' r.mapcalc raster processing module
    - Direct computation for...  though not necessary, nor useful for GRASS GIS
      modules directly?


    Details

    The algorithm removes the atmospheric effect through differential
    atmospheric absorption in the two adjacent thermal infrared channels
    centered at about 11 and 12 μm.

    The linear or non-linear combination of the brightness temperatures is
    finally applied for LST estimation based on the equation:

    LST = b0 +
        + ( b1 + b2 * ( 1 - ae ) / ae + b3 * de / ae^2 ) * ( t10 + t11 ) / 2 +
        + ( b4 + b5 * ( 1 - ae ) / ae + b6 * de / ae^2 ) * ( t10 - t11 ) / 2

    or for barren land, add another quadratic term:

    LST = b0 +
        + ( b1 + b2 * ( 1 - ae ) / ae + b3 * de / ae^2 ) * ( t10 + t11 ) / 2 +
        + ( b4 + b5 * ( 1 - ae ) / ae + b6 * de / ae^2 ) * ( t10 - t11 ) / 2 +
        + b7 * ( t10 - t11 )^2


    Note, the last quadratic term is meant to be applied only on bare soil
    surfaces!

    To reduce the influence of the CWV error on the LST, for a CWV within the
    overlap of two adjacent CWV sub-ranges, the coefficients for the two
    adjacent CWV sub-ranges are used to calculate the two initial temperatures.
    Then, the average of these temperatures is assigned to as the pixel LST.

    For example, the LST pixel with a CWV of 2.1 g/cm2 is estimated by using
    the coefficients of [0.0, 2.5] and [2.0, 3.5]. This process initially
    reduces the δLSTinc and improves the spatial continuity of the LST product.
    """

    def __init__(self, landcover):
        """
        Create a class object for Split Window algorithm

        Required inputs:
        - B10
        - B11 -- ToAR?
        - land cover class?
        - average emissivities for B10, B11
        - subrange for column water vapor
        """
        # citation
        self.citation = (
            "Du, Chen; Ren, Huazhong; Qin, Qiming; Meng, "
            "Jinjie; Zhao, Shaohua. 2015. "
            '"A Practical Split-Window Algorithm '
            "for Estimating Land Surface Temperature from "
            'Landsat 8 Data." '
            "Remote Sens. 7, no. 1: 647-665."
        )

        # basic equation (for __str__)
        self._equation = (
            "[b0 + "
            "(b1 + "
            "b2 * (1-ae) / ae + "
            "b3 * de / ae^2) * (t10 + t11) / 2 + "
            "(b4 + "
            "b5 * (1-ae) / ae + "
            "b6 * de / ae^2) * (t10 - t11) / 2 + "
            "b7 * (t10 - t11)^2]"
        )

        # basic model (for... )
        self._model = (
            "[{b0} + "
            "({b1} + "
            "{b2}*((1-{ae})/{ae})) + "
            "{b3}*({de}/{ae}) * (({t10} + {t11})/2) + "
            "({b4} + "
            "{b5}*((1-{ae})/{ae}) + "
            "{b6}*({de}/{ae}^2))*(({t10} - {t11})/2) + "
            "{b7}*({t10} - {t11})^2]"
        )

        if landcover in EMISSIVITIES.keys() or landcover == "Random":

            # a fixed land cover class requested
            assert self._landcover_string_validity(
                landcover_class
            ), "Unknown land cover class name!"
            self.landcover_class = landcover

            # retrieve & set avg emissivities for channels t10, t11
            emissivity_b10, emissivity_b11 = self._retrieve_average_emissivities(
                landcover
            )
            self.emissivity_t10 = float(emissivity_b10)
            self.emissivity_t11 = float(emissivity_b11)

            # average emissivity
            self.average_emissivity = self._compute_average_emissivity(
                self.emissivity_t10, self.emissivity_t11
            )

            # delta emissivity
            self.delta_emissivity = self._compute_delta_emissivity(
                self.emissivity_t10, self.emissivity_t11
            )

        else:

            # if no fixed land cover class requested
            self.landcover_class = False

            # use mapcalc expressions instead,
            # containing DUMMY strings for map names
            self.average_lse_mapcalc = self._build_average_emissivity_mapcalc()
            self.delta_lse_mapcalc = self._build_delta_emissivity_mapcalc()

        # all-in-one split-window lst expression for mapcalc
        self.sw_lst_mapcalc = self._build_swlst_mapcalc()

    def __str__(self):
        """
        Return a string representation of the basic Split Window LST equation
        """
        equation = " > The algorithm's basic equation: " + self._equation
        return equation  # + '\n' + model

    def _landcover_string_validity(self, string):
        """
        Check whether the given string belongs to the list (keys) of known land
        cover class names (to the FROM-GLC classification scheme) or is
        identical to 'Random' and return, accordingly, True or False.

        Parameters
        ----------
        string
            A string among the set of FROM-GLC land cover class strings

        Returns
        -------
        A boolean whether the given string exists or not
        """
        if string in FROM_GLC_LEGEND.keys():
            return True
        elif string == "Random":
            return True
        else:
            return False

    def _retrieve_average_emissivities(self, landcover_class):
        """
        Get land surface average emissivities for the requested landcover class
        from a look-up table.

        Parameters
        ----------
        landcover_class
            Input is one of the standard FROM-GLC land cover classes
            (see CSV file: average_emissivity.csv)

            For testing purposes, the string "Random" is accepted to select a
            random land surface emissivity class.

        Returns
        -------
        This helper function returns a tuple.
        """
        # Random?
        if landcover_class == "Random":
            landcover_class = random.choice(list(EMISSIVITIES.keys()))
            self.landcover_class = landcover_class  # use the 'random' class

        # fields = EMISSIVITIES[landcover_class]._fields
        emissivity_b10 = EMISSIVITIES[landcover_class].TIRS10
        emissivity_b11 = EMISSIVITIES[landcover_class].TIRS11

        return (emissivity_b10, emissivity_b11)

    def _compute_average_emissivity(self, emissivity_t10, emissivity_t11):
        """
        Return the average emissivity value for channels T10, T11.
        """
        average = float(0.5 * (emissivity_t10 + emissivity_t11))
        return average

    def _compute_delta_emissivity(self, emissivity_t10, emissivity_t11):
        """
        Return the difference of emissivity values for channels T10, T11.
        """
        delta = float(emissivity_t10 - emissivity_t11)
        return delta

    def _retrieve_adjacent_cwv_subranges(self, column_water_vapor):
        """
        Select and return adjacent subranges (string to be used as a dictionary
        key) based on the atmospheric column water vapor estimation (float
        ratio) ranging in (0.0, 6.3].

        Input "cwv" is an estimation of the column water vapor (float ratio).
        """
        cwv = column_water_vapor
        check_cwv(cwv)  # check if float?

        # a "subrange" generator
        key_subrange_generator = (
            (key, COLUMN_WATER_VAPOR[key].subrange) for key in COLUMN_WATER_VAPOR.keys()
        )

        # get all but the last -- using a list, after all!
        subranges = list(key_subrange_generator)
        # print " * Subranges:", subranges

        # cwv in one or two subranges?
        result = [range_x for range_x, (low, high) in subranges[:5] if low < cwv < high]

        # if one subrange, return a string
        if len(result) == 1:
            # self._cwv_subrange = result[0]
            # self._cwv_subrange_a = self._cwv_subrange_b = False
            return result[0]

        # if two subranges, return a tuple
        elif len(result) == 2:
            # self._cwv_subrange = False
            # self._cwv_subrange_a, self._cwv_subrange_b = tuple(result)
            return result[0], result[1]

        # what if it fails? -> subrange6
        else:
            # print " * Using the complete CWV range [0, 6.3]"
            return subranges[5][0]

    def _set_adjacent_cwv_subranges(self, column_water_vapor):
        """
        Set the retrieved cwv subranges as an attribute, though not a public
        one.
        """
        result = self._retrieve_adjacent_cwv_subranges(column_water_vapor)
        if len(result) == 1:
            self._cwv_subrange = result[0]
            self._cwv_subrange_a = self._cwv_subrange_b = False

        elif len(result) == 2:
            self._cwv_subrange = False
            self._cwv_subrange_a, self._cwv_subrange_b = tuple(result)

        # what to do for subrange6?

    def _retrieve_cwv_coefficients(self, subrange):
        """
        Retrieve column water vapor coefficients for requested subrange
        """
        b0 = COLUMN_WATER_VAPOR[subrange].b0
        b1 = COLUMN_WATER_VAPOR[subrange].b1
        b2 = COLUMN_WATER_VAPOR[subrange].b2
        b3 = COLUMN_WATER_VAPOR[subrange].b3
        b4 = COLUMN_WATER_VAPOR[subrange].b4
        b5 = COLUMN_WATER_VAPOR[subrange].b5
        b6 = COLUMN_WATER_VAPOR[subrange].b6
        if self.landcover_class == "Barren_Land":
            b7 = COLUMN_WATER_VAPOR[subrange].b7
        else:
            b7 = 0
        cwv_coefficients = (b0, b1, b2, b3, b4, b5, b6, b7)
        return cwv_coefficients

    def _set_cwv_coefficients(self, subrange):
        """
        Set the coefficients as an attribute.
        """
        self.cwv_coefficients = self._retrieve_cwv_coefficients(subrange)

    def get_cwv_coefficients(self):
        """
        Return the column water vapor coefficients from the object's attribute.
        """
        if self.cwv_coefficients:
            return self.cwv_coefficients
        else:
            print("* CWV coefficients have not been set!")

    def _retrieve_rmse(self, subrange):
        """
        Retrieve and set the associated RMSE for the column water vapor
        coefficients for the subrange in question.
        """
        return COLUMN_WATER_VAPOR[subrange].rmse

    def _set_rmse(self, subrange):
        """
        Set the RMSE as an attribute.
        """
        self.rmse = self._retrieve_rmse(subrange)

    def report_rmse(self):
        """
        Report the associated R^2 value for the coefficients in question
        """
        msg = "Associated RMSE: "
        return msg + str(self.rmse)

    def compute_lst(self, t10, t11, coefficients):
        """
        Compute Land Surface Temperature based on the Split-Window algorithm.
        Inputs are brightness temperatures measured in channels i (~11.0 μm)
        and j (~12.0 μm).

        *Note*, this is a single value computation function and does not read
        or return a map.

        LST = b0 +
            + (b1 + b2 * ((1-ae)/ae) + b3 * (de/ae^2)) * ((t10 + t11)/2) +
            + (b4 + b5 * ((1-ae)/ae) + b6 * (de/ae^2)) * ((t10 - t11)/2) +

        or over 'Barren land':

        LST = b0 +
            + (b1 + b2 * ((1-ae)/ae) + b3 * (de/ae^2)) * ((t10 + t11)/2) +
            + (b4 + b5 * ((1-ae)/ae) + b6 * (de/ae^2)) * ((t10 - t11)/2) +
            + b7 * (t10 - t11)^2
        """

        # check validity of t10, t11
        check_t1x_range(t10)
        check_t1x_range(t11)

        # check validity of subrange (string)?

        # set cwv coefficients
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients

        # average and delta emissivity
        avg = self.average_emissivity
        delta = self.delta_emissivity

        # addends
        a = b0
        b1 = b1 + b2 * (1 - avg) / avg + b3 * delta / avg**2
        b2 = (t10 + t11) / 2
        b = b1 * b2
        c1 = b4 + b5 * (1 - avg) / avg + b6 * delta / avg**2
        c2 = (t10 - t11) / 2
        c = c1 * c2
        d = b7 * (t10 - t11) ** 2
        lst = a + b + c + d
        return lst

    def _set_lst(self):
        """
        Set the result of the single value computation function as an attribute
        (?)
        """
        pass

    def compute_average_lst(self, t10, t11, subrange_a, subrange_b):
        """
        Compute average LST, similar as the compute_lst function.
        """

        # retrieve coefficients for first subrange and compute lst for it
        coefficients_a = self._retrieve_cwv_coefficients(subrange_a)
        lst_a = self.compute_lst(t10, t11, coefficients_a)

        # repeat for second subrange
        coefficients_b = self._retrieve_cwv_coefficients(subrange_b)
        lst_b = self.compute_lst(t10, t11, coefficients_b)

        # average land surface temperature
        return (lst_a + lst_b) / 2

    def _set_average_lst(self):
        """
        Set the average LST pixel value as an attribute (?)
        """
        pass

    def _build_average_emissivity_mapcalc(self):
        """
        ToDo: shorten the following!
        """
        # average emissivities
        e10_t10, e10_t11 = self._retrieve_average_emissivities("Cropland")
        avg_e10 = self._compute_average_emissivity(e10_t10, e10_t11)

        e20_t10, e20_t11 = self._retrieve_average_emissivities("Forest")
        avg_e20 = self._compute_average_emissivity(e20_t10, e20_t11)

        e30_t10, e30_t11 = self._retrieve_average_emissivities("Grasslands")
        avg_e30 = self._compute_average_emissivity(e30_t10, e30_t11)

        e40_t10, e40_t11 = self._retrieve_average_emissivities("Shrublands")
        avg_e40 = self._compute_average_emissivity(e40_t10, e40_t11)

        e60_t10, e60_t11 = self._retrieve_average_emissivities("Waterbodies")
        avg_e60 = self._compute_average_emissivity(e60_t10, e60_t11)

        e80_t10, e80_t11 = self._retrieve_average_emissivities("Impervious")
        avg_e80 = self._compute_average_emissivity(e80_t10, e80_t11)

        e90_t10, e90_t11 = self._retrieve_average_emissivities("Barren_Land")
        avg_e90 = self._compute_average_emissivity(e90_t10, e90_t11)

        e100_t10, e100_t11 = self._retrieve_average_emissivities("Snow_and_ice")
        avg_e100 = self._compute_average_emissivity(e100_t10, e100_t11)

        expression = (  # Cropland: (10, 11, 12, 13)
            "eval( class_10 = {landcover} >= 10 && {landcover} < 20,"
            # Forest: (20, 21, 22, 23, 24)
            "\ \n class_20 = {landcover} >= 20 && {landcover} < 30,"
            # Grasslands: (30, 31, 32, 51, 72)
            "\ \n class_30 = {landcover} == 51 || {landcover} == 72 || {landcover} >= 30 && {landcover} < 40,"
            # Shrublands: (40, 71)
            "\ \n class_40 = {landcover} == 71 || {landcover} >= 40 && {landcover} < 50,"
            # Wetlands: 50  --  Assigned below the 'average_60'
            "\ \n class_50 = {landcover} >= 50 && {landcover} < 52,"
            # Waterbodies: (50, 60, 61, 62, 63)
            "\ \n class_60 = {landcover} >= 60 && {landcover} < 70,"
            # Tundra: 70  --  Assigned belot the 'average_40'
            "\ \n class_70 = {landcover} >= 70 && {landcover} < 72,"
            # Impervious: (80, 81, 82)
            "\ \n class_80 = {landcover} >= 80 && {landcover} < 90,"
            # Barren Land: (90, 52, 91, 92, 93, 94, 95, 96)
            "\ \n class_90 = {landcover} == 52 || {landcover} >= 90 && {landcover} < 100,"
            # Snow and ice: (100, 101, 102)
            "\ \n class_100 = {landcover} >= 100 && {landcover} < 120,"
            # Cloud: (120) -- Should be masked, thus not included
            "\ \n if( class_10, {average_10},"
            "\ \n if( class_20, {average_20},"
            "\ \n if( class_30, {average_30},"
            "\ \n if( class_40, {average_40},"
            "\ \n if( class_50, {average_60},"
            "\ \n if( class_60, {average_60},"
            "\ \n if( class_70, {average_40},"
            "\ \n if( class_80, {average_80},"
            "\ \n if( class_90, {average_90},"
            "\ \n if( class_100, {average_100},"
            " null() )))))))))))"
        )

        mapcalc = expression.format(
            landcover=DUMMY_MAPCALC_STRING_FROM_GLC,
            average_10=avg_e10,
            average_20=avg_e20,
            average_30=avg_e30,
            average_40=avg_e40,
            average_60=avg_e60,
            average_80=avg_e80,
            average_90=avg_e90,
            average_100=avg_e100,
        )

        return mapcalc

    def _build_delta_emissivity_mapcalc(self):
        """
        ToDo: shorten the following!
        """
        # delta emissivities
        e10_t10, e10_t11 = self._retrieve_average_emissivities("Cropland")
        delta_e10 = self._compute_delta_emissivity(e10_t10, e10_t11)

        e20_t10, e20_t11 = self._retrieve_average_emissivities("Forest")
        delta_e20 = self._compute_delta_emissivity(e20_t10, e20_t11)

        e30_t10, e30_t11 = self._retrieve_average_emissivities("Grasslands")
        delta_e30 = self._compute_delta_emissivity(e30_t10, e30_t11)

        e40_t10, e40_t11 = self._retrieve_average_emissivities("Shrublands")
        delta_e40 = self._compute_delta_emissivity(e40_t10, e40_t11)

        e60_t10, e60_t11 = self._retrieve_average_emissivities("Waterbodies")
        delta_e60 = self._compute_delta_emissivity(e60_t10, e60_t11)

        e80_t10, e80_t11 = self._retrieve_average_emissivities("Impervious")
        delta_e80 = self._compute_delta_emissivity(e80_t10, e80_t11)

        e90_t10, e90_t11 = self._retrieve_average_emissivities("Barren_Land")
        delta_e90 = self._compute_delta_emissivity(e90_t10, e90_t11)

        e100_t10, e100_t11 = self._retrieve_average_emissivities("Snow_and_ice")
        delta_e100 = self._compute_delta_emissivity(e100_t10, e100_t11)

        expression = (  # Cropland: (10, 11, 12, 13)
            "eval( class_10 = {landcover} >= 10 && {landcover} < 20,"
            # Forest: (20, 21, 22, 23, 24)
            "\ \n class_20 = {landcover} >= 20 && {landcover} < 30,"
            # Grasslands: (30, 31, 32, 51, 72)
            "\ \n class_30 = {landcover} == 51 || {landcover} == 72 || {landcover} >= 30 && {landcover} < 40,"
            # Shrublands: (40, 71)
            "\ \n class_40 = {landcover} == 71 || {landcover} >= 40 && {landcover} < 50,"
            # Wetlands: 50  -- Assigned below the 'delta_60'
            "\ \n class_50 = {landcover} >= 50 && {landcover} < 52,"
            # Waterbodies: (50, 60, 61, 62, 63)
            "\ \n class_60 = {landcover} >= 60 && {landcover} < 70,"
            # Tundra: 70  --  Assigned belot the 'delta_40'
            "\ \n class_70 = {landcover} >= 70 && {landcover} < 72,"
            # Impervious: (80, 81, 82)
            "\ \n class_80 = {landcover} >= 80 && {landcover} < 90,"
            # Barren Land: (90, 52, 91, 92, 93, 94, 95, 96)
            "\ \n class_90 = {landcover} == 52 || {landcover} >= 90 && {landcover} < 100,"
            # Snow and ice: (100, 101, 102)
            "\ \n class_100 = {landcover} >= 100 && {landcover} < 120,"
            # Cloud: (120) -- Should be masked, thus not included
            "\ \n if( class_10, {delta_10},"
            "\ \n if( class_20, {delta_20},"
            "\ \n if( class_30, {delta_30},"
            "\ \n if( class_40, {delta_40},"
            "\ \n if( class_50, {delta_60},"
            "\ \n if( class_60, {delta_60},"
            "\ \n if( class_70, {delta_40},"
            "\ \n if( class_80, {delta_80},"
            "\ \n if( class_90, {delta_90},"
            "\ \n if( class_100, {delta_100},"
            " null() )))))))))))"
        )

        mapcalc = expression.format(
            landcover=DUMMY_MAPCALC_STRING_FROM_GLC,
            delta_10=delta_e10,
            delta_20=delta_e20,
            delta_30=delta_e30,
            delta_40=delta_e40,
            delta_60=delta_e60,
            delta_80=delta_e80,
            delta_90=delta_e90,
            delta_100=delta_e100,
        )

        return mapcalc

    def _build_model(self, coefficients):
        """
        Build model for __str__
        """
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients
        model = self._model.format(
            b0=b0,
            b1=b1,
            b2=b2,
            ae=self.average_emissivity,
            de=self.delta_emissivity,
            b3=b3,
            b4=b4,
            b5=b5,
            b6=b6,
            b7=b7,
            t10=self.emissivity_t10,
            t11=self.emissivity_t11,
        )
        return model

    def _build_subrange_mapcalc(self, subrange):
        """
        Build formula for GRASS GIS' mapcalc for the given cwv subrange.

        ToDo: Review and Improve the mechanism which selects emissivities from
        either a fixed land cover class  OR  a land cover map.
        """
        try:
            if self.landcover_class:  # Fixed land cover class
                emissivity_t10 = float(self.emissivity_t10)
                emissivity_t11 = float(self.emissivity_t11)
                avg_lse = self._compute_average_emissivity(
                    emissivity_t10,
                    emissivity_t11,
                )
                delta_lse = self._compute_delta_emissivity(
                    emissivity_t10,
                    emissivity_t11,
                )
        except:
            pass

        if not self.landcover_class:
            # This is required for when a fixed emissivity_class is used,
            # instead of a FROM-GLC (landcover) map.
            avg_lse = DUMMY_MAPCALC_STRING_AVG_LSE
            delta_lse = DUMMY_MAPCALC_STRING_DELTA_LSE

        b0, b1, b2, b3, b4, b5, b6, b7 = self._retrieve_cwv_coefficients(subrange)
        mapcalc = LST_FORMULA.format(
            b0=b0,
            b1=b1,
            b2=b2,
            ae=avg_lse,
            de=delta_lse,
            b3=b3,
            b4=b4,
            b5=b5,
            b6=b6,
            b7=b7,
            DUMMY_T10=DUMMY_MAPCALC_STRING_T10,
            DUMMY_T11=DUMMY_MAPCALC_STRING_T11,
        )

        return mapcalc

    def _build_swlst_mapcalc(self):
        """
        Build and return a valid expression for GRASS GIS' r.mapcalc to
        determine LST.
        """
        # subrange limits, low, high
        low_1, high_1 = COLUMN_WATER_VAPOR["Range_1"].subrange
        low_2, high_2 = COLUMN_WATER_VAPOR["Range_2"].subrange
        low_3, high_3 = COLUMN_WATER_VAPOR["Range_3"].subrange
        low_4, high_4 = COLUMN_WATER_VAPOR["Range_4"].subrange
        low_5, high_5 = COLUMN_WATER_VAPOR["Range_5"].subrange
        low_6, high_6 = COLUMN_WATER_VAPOR["Range_6"].subrange  # unused

        # build mapcalc expression for each subrange
        expression_range_1 = self._build_subrange_mapcalc("Range_1")
        expression_range_2 = self._build_subrange_mapcalc("Range_2")
        expression_range_3 = self._build_subrange_mapcalc("Range_3")
        expression_range_4 = self._build_subrange_mapcalc("Range_4")
        expression_range_5 = self._build_subrange_mapcalc("Range_5")

        # complete range
        expression_range_6 = self._build_subrange_mapcalc("Range_6")

        # build one big expression using mighty eval
        expression = (
            "eval( sw_lst_1 = {exp_1},"
            "\ \n sw_lst_2 = {exp_2},"
            "\ \n sw_lst_12 = (sw_lst_1 + sw_lst_2) / 2,"
            "\ \n sw_lst_3 = {exp_3},"
            "\ \n sw_lst_23 = (sw_lst_2 + sw_lst_3) / 2,"
            "\ \n sw_lst_4 = {exp_4},"
            "\ \n sw_lst_34 = (sw_lst_3 + sw_lst_4) / 2,"
            "\ \n sw_lst_5 = {exp_5},"
            "\ \n sw_lst_45 = (sw_lst_4 + sw_lst_5) / 2,"
            "\ \n sw_lst_6 = {exp_6},"
            "\ \n in_range_1 = {low_1} < {DUMMY_CWV} && {DUMMY_CWV} < {high_1},"
            "\ \n in_range_2 = {low_2} < {DUMMY_CWV} && {DUMMY_CWV} < {high_2},"
            "\ \n in_range_3 = {low_3} < {DUMMY_CWV} && {DUMMY_CWV} < {high_3},"
            "\ \n in_range_4 = {low_4} < {DUMMY_CWV} && {DUMMY_CWV} < {high_4},"
            "\ \n in_range_5 = {low_5} < {DUMMY_CWV} && {DUMMY_CWV} < {high_5},"
            "\ \n if( in_range_1 && in_range_2, sw_lst_12,"
            "\ \n if( in_range_2 && in_range_3, sw_lst_23,"
            "\ \n if( in_range_3 && in_range_4, sw_lst_34,"
            "\ \n if( in_range_4 && in_range_5, sw_lst_45,"
            "\ \n if( in_range_1, sw_lst_1,"
            "\ \n if( in_range_2, sw_lst_2,"
            "\ \n if( in_range_3, sw_lst_3,"
            "\ \n if( in_range_4, sw_lst_4,"
            "\ \n if( in_range_5, sw_lst_5,"
            " sw_lst_6 ))))))))))"
        )  # ' null() ))))))))))')

        # replace keywords appropriately
        swlst_expression = expression.format(
            exp_1=expression_range_1,
            low_1=low_1,
            DUMMY_CWV=DUMMY_MAPCALC_STRING_CWV,
            high_1=high_1,
            exp_2=expression_range_2,
            low_2=low_2,
            high_2=high_2,
            exp_3=expression_range_3,
            low_3=low_3,
            high_3=high_3,
            exp_4=expression_range_4,
            low_4=low_4,
            high_4=high_4,
            exp_5=expression_range_5,
            low_5=low_5,
            high_5=high_5,
            exp_6=expression_range_6,
        )

        return swlst_expression


# reusable & stand-alone
if __name__ == "__main__":
    print(
        "Split-Window Algorithm for Estimating Land Surface Temperature "
        "from Landsat8 OLI/TIRS imagery."
        " (Running as stand-alone tool?)\n"
    )
