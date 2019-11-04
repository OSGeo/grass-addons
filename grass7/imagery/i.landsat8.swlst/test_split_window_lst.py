#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik | 2015-04-18 03:48:20
"""

# required librairies
import random
import csv_to_dictionary as coefficients
from split_window_lst import *

# globals
EMISSIVITIES = coefficients.get_average_emissivities()
COLUMN_WATER_VAPOR = coefficients.get_column_water_vapor()

# helper function(s)
def random_digital_numbers(count=2):
    """
    Return a user-requested amount of random Digital Number values for testing
    purposes ranging in 12-bit
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(1, 2**12))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers


def random_brightness_temperature_values(count=2):
    """
    Return a user-requested amount of random Brightness Temperature values for testing
    purposes ranging in [250, 330].
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(250, 330))

    if count == 1:
        return digital_numbers[0]

    return digital_numbers

def random_column_water_vapor():
    """
    Return a rational number ranging in [0.0, 6.3] to assisst in selecting
    an atmospheric column water vapor subrange, as part of testing the
    Split-WindowLST class.
    """
    return random.uniform(0.0 -1, 6.3 + 1)


def test_split_window_lst():
    """
    Testing the SplitWindowLST class
    """

    #
    # Helpers
    #

    print()
    print(">>> [Helper functions]")
    print()
    t10 = random_brightness_temperature_values(1)
    t11 = random.choice(((t10 + 50), (t10 - 50)))  # check some failures as well
    print(" * Random brightness temperature values for T10, T11:", t10, t11)
    print (' * NOTE: Some out of a reasonable range T10, T11 values, which '
           'cause the current test to fail, are tolerated on-purpose in order '
           'to test the range checking function `check_t1x_range()`.')
    print()
    print()

    #
    # EMISSIVITIES
    #

    # get emissivities
    print("[ EMISSIVITIES ]")
    print()
    EMISSIVITIES = coefficients.get_average_emissivities()
    print(" * Dictionary for average emissivities:\n\n", EMISSIVITIES)
    print()

    somekey = random.choice(list(EMISSIVITIES.keys()))
    print(" * Some random key from EMISSIVITIES:", somekey)

    fields = EMISSIVITIES[somekey]._fields
    print(" * Fields of namedtuple:", fields)

    random_field = random.choice(fields)
    print(" * Some random field:", random_field)

    command = 'EMISSIVITIES.[{key}].{field} ='
    command = command.format(key=somekey, field=random_field)
    print(" * Example of retrieving values (named tuple): " + command, end=' ')
    print(EMISSIVITIES[somekey].TIRS10, EMISSIVITIES[somekey].TIRS11)

    emissivity_b10 = EMISSIVITIES[somekey].TIRS10
    print(" * Average emissivity for B10:", emissivity_b10, "|Type:", type(emissivity_b10))
    emissivity_b11 = EMISSIVITIES[somekey].TIRS11
    print(" * Average emissivity for B11:", emissivity_b11)
    print()
    print()
    print()

    #
    # COLUMN_WATER_VAPOR
    #

    print("[ COLUMN_WATER_VAPOR ]")
    print()
    print (' * NOTE: Some out of range values which cause the current test to '
           'fail, are tolerated on-purpose in order to check for the CWV '
           'range checking function.  Check for the range of the '
           'random_column_water_vapor() function.')
    
    COLUMN_WATER_VAPOR = coefficients.get_column_water_vapor()
    print("\n * Dictionary for column water vapor coefficients:\n\n", end=' ')
    print(COLUMN_WATER_VAPOR)
    print()

    cwvobj = Column_Water_Vapor(3, 'TiRS10', 'TiRS11')
    print(" * Retrieval of column water vapor via class, example: ", end=' ')  #, cwvobj
    print("   cwvobj = Column_Water_Vapour(3, MapName_for_T10, MapName_for_T11)")
    print(" * Mapcalc expression for it: ", cwvobj.column_water_vapor_expression)
    print()

    cwv = random_column_water_vapor()
    print(" * For the test, some random atmospheric column water vapor '(g/cm^2):", cwv)

    #
    cwv_range_x = random.choice([key for key in list(COLUMN_WATER_VAPOR.keys())])

    cwvfields = COLUMN_WATER_VAPOR[cwv_range_x]._fields
    print(" * Fields of namedtuple (same for all subranges):", cwvfields)

    random_cwvfield = random.choice(cwvfields)
    print(" * Some random field:", random_cwvfield)

    command = 'COLUMN_WATER_VAPOR.[{key}].{field} ='
    command = command.format(key=cwv_range_x, field=random_cwvfield)
    print(" * Example of retrieving values (named tuple): " + command, end=' ')
    print(COLUMN_WATER_VAPOR[cwv_range_x].subrange)
    print()
    print()
    print()

    #
    # class
    #

    print("[ class SplitWindowLST ]")
    print()

    # cwv_range_x = column_water_vapor_range(cwv)
    # print " * Atmospheric column water vapor range:", cwv_range_x

    swlst = SplitWindowLST(somekey)  # somekey generated above
    print("Create object and test '__str__' of SplitWindowLST() class:\n\n", swlst)

    print(" > The 'citation' attribute:", swlst.citation)
    print()

    # get a column water vapor subrange
    cwv_range_x = swlst._retrieve_adjacent_cwv_subranges(cwv)

    # special case for Subrange 6
    if cwv_range_x == 'Range_6':
        msg = (' * The CWV value {cwv} falls outside of one of the subranges. '
               'Using the complete CWV range [0.0, 6.3] described as')
        msg = msg.format(cwv=cwv)
        print(msg, cwv_range_x)
    else:
        print(" * The CWV value {cwv} falls inside:".format(cwv=cwv), cwv_range_x, "|Type:", type(cwv_range_x))
   
### First, test all _retrieve functions ###
    
    print()
    print("( Testing unpacking of values )")
    print()

    if type(cwv_range_x) == str:

        cwv_coefficients_x = swlst._retrieve_cwv_coefficients(cwv_range_x)
        b0, b1, b2, b3, b4, b5, b6, b7 = cwv_coefficients_x
        
        print(" * Column Water Vapor coefficients (b0, b1, ..., b7) in <", cwv_range_x, end=' ')
        
        print("> :", b0, b1, b2, b3, b4, b5, b6, b7)
        
        print(" * Model:", swlst._build_model(cwv_coefficients_x))
        
        print(" * Checking the '_retrieve_rmse' method:", swlst._retrieve_rmse(cwv_range_x))
        
        print(" * Testing the '_set_rmse' and 'report_rmse' methods:", end=' ')

        swlst._set_rmse(cwv_range_x)
        print(swlst.report_rmse())
            
        print(" * Testing the 'compute_lst' method:", swlst.compute_lst(t10, t11, cwv_coefficients_x))


    elif type(cwv_range_x) == tuple and len(cwv_range_x) == 2:

        print(" * Two subranges returned:", end=' ')

        cwv_subrange_a, cwv_subrange_b = tuple(cwv_range_x)[0], tuple(cwv_range_x)[1]
        print(" Subrange a:", cwv_subrange_a, "| Subrange b:", cwv_subrange_b)
    
        #
        # Subrange A
        #
        
        print()
        print(" > Tests for subrange a")
        print()

        coefficients_a = swlst._retrieve_cwv_coefficients(cwv_subrange_a)
        
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients_a
        
        print("   * Column Water Vapor coefficients for", cwv_subrange_a, end=' ')

        print("> ", b0, b1, b2, b3, b4, b5, b6, b7)
        
        print("   * Testing the '_set' and 'get' methods:", end=' ')
        swlst._set_cwv_coefficients(cwv_subrange_a)  # does not return anything
        
        print(swlst.get_cwv_coefficients())

        print("   * Model:", swlst._build_model(coefficients_a))

        print("   * Checking the '_retrieve_rmse' method:", swlst._retrieve_rmse(cwv_subrange_a))
        print("   * Testing the '_set_rmse' and 'report_rmse' methods:", end=' ')
        swlst._set_rmse(cwv_subrange_a)
        
        print(swlst.report_rmse())



        #
        # Subrange B
        #

        print()
        print(" > Tests for subrange b")
        print()

        coefficients_b = swlst._retrieve_cwv_coefficients(cwv_subrange_b)
        
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients_b
        
        print("   * Column Water Vapor coefficients for", cwv_subrange_b, end=' ')

        print("> ", b0, b1, b2, b3, b4, b5, b6, b7)
        
        print("   * Testing the 'get' and '_set' methods:", end=' ')
        swlst._set_cwv_coefficients(cwv_subrange_b)
        
        print(swlst.get_cwv_coefficients())
        
        print("   * Model:", swlst._build_model(coefficients_b))
        
        print("   * Checking the '_retrieve_rmse' method:", swlst._retrieve_rmse(cwv_subrange_a))
        print("   * Testing the '_set_rmse' and 'report_rmse' methods:", end=' ')
        swlst._set_rmse(cwv_subrange_a)
        
        print(swlst.report_rmse())



        #
        # Average LST
        #

        print()
        print("( Computing average LST )")
        print()

        print(" * Compute the average LST: 'compute_average_lst()' >>>", end=' ')

        print(swlst.compute_average_lst(t10, t11, cwv_subrange_a, cwv_subrange_b))

        print()

    print()
    print("[ Subranges ]")
    print()

    key_subrange_generator = ((key, COLUMN_WATER_VAPOR[key].subrange) for key in list(COLUMN_WATER_VAPOR.keys()))


    sw_lst_expression = swlst.sw_lst_mapcalc
    print("Big expression:\n\n", sw_lst_expression)


# reusable & stand-alone
if __name__ == "__main__":
    print ('Testing the SplitWindowLST class')
    print()
    test_split_window_lst()
