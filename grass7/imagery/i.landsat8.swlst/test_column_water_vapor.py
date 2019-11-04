#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""

# required librairies
import random
from column_water_vapor import *


# helper functions
def random_window_size():
    """
    """
    return random.randint(7, 21)

def random_adjacent_pixel_values(pixel_modifiers):
    """
    """
    return [random.randint(250, 350) for dummy_idx in
            range(len(pixel_modifiers))]


def test_column_water_vapor():

    print('Equations for Column Water Vapor retrieval based on...')
    print()

    print ('  * Considering N adjacent pixels, the CWV in the MSWCVR method '
           'is estimated as:')
    print()
    print ('    cwv  =  c0  +  c1  *  (tj / ti)  +  c2  *  (tj / ti)^2')
    print()
    print ('    where:\n\n   - tj/ti ~ Rji = '
           'SUM [ ( Tik - Ti_mean ) * ( Tjk - Tj_mean ) ] / '
           'SUM [ ( Tik - Tj_mean )^2 ]')

    print()
    print("Testing the Column_Water_Vapor class")
    print()

    window_size = random_window_size()
    # window_size = 7
    obj = Column_Water_Vapor(window_size, 'A', 'B')
    print(" | Testing the '__str__' method:\n\n ", obj)
    print()

    print(" | Adjacent pixels:", obj.adjacent_pixels)
    print()

    print(" | Map Ti:", obj.ti)

    print(" | Map Tj:", obj.tj)
    print()

    print(" | N pixels window modifiers for Ti:", obj.modifiers_ti)

    print(" | N pixels window Modifiers for Tj:", obj.modifiers_tj)

    print(" | Zipped modifiers_tij (used in a function for the Ratio ji):", end=' ')
    print(obj.modifiers)
    print()

    print("   ~ Random N pixel values for Ti:", end=' ')
    random_ti_values = random_adjacent_pixel_values(obj.modifiers_ti)
    print(random_ti_values)
    
    print("   ~ Random N pixel values for Tj:", end=' ')
    random_tj_values = random_adjacent_pixel_values(obj.modifiers_ti)
    print(random_tj_values)

    print(('   ~ Testing "compute_column_water_vapor" '
           'based on the above random values):'), end=' ')
    print(obj.compute_column_water_vapor(random_ti_values, random_tj_values))
    print()
    
    print(" | Expression for Ti mean:", obj.mean_ti_expression)
    
    print(" | Expression for Tj mean:", obj.mean_tj_expression)
    print()
    
    print("   ~ Mean of random N pixel values for Ti:", end=' ')
    print(sum(random_ti_values) / len(random_ti_values))
    
    print("   ~ Mean of random N pixel values for Tj:", end=' ')
    print(sum(random_tj_values) / len(random_tj_values))
    print()

    print(" | Note, the following mapcalc expressions use dummy strings, meant to be replaced in the main program by the names of the maps in question")
    print()

    print(" | Expression for Numerator for Ratio (method):", obj._numerator_for_ratio('Ti_Mean', 'Tj_Mean'))
    print()
    
    print ('   ~ Add example for Numerator based on '
           'Mean of random N pixel values for Ti, Tj:')
    print()
    
    
    print(" | Expression for Denominator for Ratio (method):", obj._denominator_for_ratio('Ti_Mean'))
    print()
    
    print ('   ~ Add example for Denominator based on '
           'Mean of random N pixel values for Tj:')
    print()

    print(" | Ratio ji expression for mapcalc:", obj.ratio_ji_expression)
    print()

    print ('   ~ Add example for Ratio ji expression based on '
           'numerator and denominator as defined above:')
    print()
    
    print(" | One big mapcalc expression:\n\n", obj._big_cwv_expression())
    print()

# reusable & stand-alone
if __name__ == "__main__":
    print ('Testing the SplitWindowLST class')
    print()
    test_column_water_vapor()
