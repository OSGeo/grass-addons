# -*- coding: utf-8 -*-
"""
Functions to test Python classes for inter-satellite calibration of nighttime
lights time series.

@author = nik
"""

# required librairies
import random
from intercalibration_coefficients import COEFFICIENTS
from intercalibration_models import Elvidge, Liu2012, Wu2013


# helper functions
def random_digital_numbers(count=3):
    """
    Return a user-requested amount of random Digital Number values for testing
    purposes
    """
    digital_numbers = []

    for dn in range(0, count):
        digital_numbers.append(random.randint(0, 63))

    return digital_numbers


def random_digital_number():
    """
    Return one random of Digital Number values for testing purposes
    """
    return random.randint(0, 63)


def calibrate_digital_number(dn, c0, c1, c2):
    """
    Calibrate a "raw" digital number based on Elvidge's calibration
    polynomial model
    """
    if not isinstance(dn, int):
        raise ValueError("The provided Digital Number value is NOT an " "integer!")

    if 0 > dn or dn > 63:
        raise ValueError(
            "The provided Digital Number value is out of the " "expected range [0, 63]"
        )

    return c0 + (c1 * dn) + (c2 * (dn**2))


def test_model(author):
    """
    Testing the "?" model
    """
    print(">>> Testing -----------------------------------------------------\n")

    # -----------------------------------------------------------------------
    # set required values
    print(" >> Pre-Setting (randomly) required values for testing purposes:")
    print()

    print(" * Assigning (random) author, model version and parameters...")
    version = ""
    if not author:
        version = random.choice(["2009", "2014"])
        author = "ELVIDGE" + str(version)
    else:
        version = author[7:]

    satellite = random.choice(list(COEFFICIENTS[author].keys()))
    year = random.choice(list(COEFFICIENTS[author][satellite].keys()))
    c0 = COEFFICIENTS[author][satellite][year][0]
    c1 = COEFFICIENTS[author][satellite][year][1]

    print(f"   Author: {author}")
    print(f"   Version: {version}")
    print(f"   Satellite: {satellite}")
    print(f"   Year: {year}")
    print(f"   c0: {c0}")
    print(f"   c1: {c1}")

    c2 = float()
    if "WU" not in author:
        print()
        print(" * Assiging a random c2 coefficient...")
        c2 = COEFFICIENTS[author][satellite][year][2]
        print(f"   {c2}")

    #    R2 = coefficients[author][satellite][year][3]
    #    print " Associated R^2 value: ", R2
    print()

    # -----------------------------------------------------------------------
    print(" >> Testing model class:")
    print()
    print(
        "   Usage:  <ModelName>(satellite, year, model version)\n"
        "   where:  DN: input Digital Number value (integer)\n"
        "           Coefficients: a pair or triplet of floating point values (tuple)\n"
        "   eg:     liu2010_model = Liu2012(F10, 1992, 2009)"
    )
    print()
    if "ELVIDGE" in author:
        test_model = Elvidge(satellite, year, version)
    elif "LIU" in author:
        test_model = Liu2012(satellite, year)
    elif "WU" in author:
        test_model = Wu2013(satellite, year)

    print(" * Testing 'citation'  method:\n\n  ", test_model.citation)
    print()
    print(" * Testing '__str__' of class:\n\n  ", test_model)
    print(" * Testing 'satellite': ", test_model.satellite)
    print(" * Testing 'year':      ", test_model.year)
    print(" * Testing 'veify_year': ", test_model.verify_year(author, satellite, year))
    print(" * Testing 'coefficients': ", test_model.coefficients)
    print(" * Testing 'r2': ", test_model.r2)
    print(" * Testing 'report_r2' method: ", test_model.report_r2())
    dn = random_digital_number()
    print(" > A random digital number: ", dn)
    print(" * Testing 'is_dn_valid': ", test_model.is_dn_valid(dn))
    print(" * Testing 'calibrate' method:  ", test_model.calibrate(dn))
    print(" * Testing '_model' (hidden): ", test_model._model)
    print(" * Testing 'mapcalc': ", test_model.mapcalc)
    print(" * Testing 'get_mapcalc': ", test_model.get_mapcalc())
    print()

    # -----------------------------------------------------------------------
    print(" >> Testing helper functions: ")
    print()
    dn = random_digital_number()
    print(
        " * Testing 'random_digital_number()' method (and type()): ", dn, "|", type(dn)
    )
    print(
        " * Testing 'calibrate_digital_number' method: ",
        calibrate_digital_number(dn, c0, c1, c2),
    )
    # -----------------------------------------------------------------------
    print(" * Testing three random Digital number values:\n")
    for dn in random_digital_numbers(3):
        print("   (Random) DN: ", dn)
        print("   Coefficients: ", test_model.coefficients)
        print("   Model: ", test_model.calibrate(dn), "\n")


# reusable & stand-alone
if __name__ == "__main__":
    print(
        "Testing classes for calibration models for DMSP-OLS NightTime "
        "Lights Time Series"
    )
    print()

    # uncomment to test
    test_model("ELVIDGE2009")
    test_model("ELVIDGE2014")
    test_model("LIU2012")
    test_model("WU2013")
