"""
Convert csv data to a dictionary with namedtuples as values. However, a string
csv-file look-a-like may be used directly. Currently, the latter option is
used.

ToDo:
* Add usage examples!
* Clean up which test to use for which csv file!
* Clean up which transform function to use according to csv file!
* Clean again...
* Deduplication!
"""

# based on: <http://pastebin.com/tnyhmCJz>
# see: <http://stackoverflow.com/q/29141609/1172302>

# real data
AE_STRING = """Emissivity Class|TIRS10|TIRS11
Cropland|0.971|0.968
Forest|0.995|0.996
Grasslands|0.97|0.971
Shrublands|0.969|0.97
Wetlands|0.992|0.998
Waterbodies|0.992|0.998
Tundra|0.98|0.984
Impervious|0.973|0.981
Barren Land|0.969|0.978
Snow and ice|0.992|0.998"""

CWV_STRING = """Range|CWV|b0|b1|b2|b3|b4|b5|b6|b7|RMSE
Range 1|(0.0, 2.5)|-2.78009|1.01408|0.15833|-0.34991|4.04487|3.55414|-8.88394|0.09152|0.34
Range 2|(2.0, 3.5)|11.00824|0.95995|0.17243|-0.28852|7.11492|0.42684|-6.62025|-0.06381|0.60
Range 3|(3.0, 4.5)|9.62610|0.96202|0.13834|-0.17262|7.87883|5.17910|-13.26611|-0.07603|0.71
Range 4|(4.0, 5.5)|0.61258|0.99124|0.10051|-0.09664|7.85758|6.86626|-15.00742|-0.01185|0.86
Range 5|(5.0, 6.3)|-0.34808|0.98123|0.05599|-0.03518|11.96444|9.06710|-14.74085|-0.20471|0.93
Range 6|(0.0, 6.3)|-0.41165|1.00522|0.14543|-0.27297|4.06655|-6.92512|-18.27461|0.24468|0.87"""

# required librairies
import sys
import csv
from collections import namedtuple
import random
import functools


# helper functions
def set_csvfile():
    """
    Set user defined csvfile, if any
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return False


def is_number(value):
    """
    Check if input is a number
    """
    try:
        float(value)  # for int, long and float
    except ValueError:
        try:
            complex(value)  # for complex
        except ValueError:
            return False
    return float(value)


def to_tuple(string):
    """
    Convert string to tuple.
    """
    return tuple(map(float, string[1:-1].split(",")))


def replace_dot_comma_space(string):
    """
    Source: <http://stackoverflow.com/a/9479972/1172302>
    """
    replacements = (
        (".", ""),
        (", ", "_"),
        (",", "_"),
        (" ", "_"),
        ("(", ""),
        (")", ""),
        ("/", "_"),
    )
    return functools.reduce(
        lambda alpha, omega: alpha.replace(*omega), replacements, string
    )


def csv_reader(csv_file):
    '''
    Transforms csv from a file into a multiline string. For example,
    the following csv

    --%<---
    Emissivity Class|TIRS10|TIRS11
    Cropland|0.971|0.968
    Forest|0.995|0.996
    Grasslands|0.97|0.971
    Shrublands|0.969|0.97
    Wetlands|0.992|0.998
    Waterbodies|0.992|0.998
    Tundra|0.98|0.984
    Impervious|0.973|0.981
    Barren Land|0.969|0.978
    Snow and ice|0.992|0.998
    --->%--

    will be returned as:

    """Emissivity Class|TIRS10|TIRS11
    Cropland|0.971|0.968
    Forest|0.995|0.996
    Grasslands|0.97|0.971
    Shrublands|0.969|0.97
    Wetlands|0.992|0.998
    Waterbodies|0.992|0.998
    Tundra|0.98|0.984
    Impervious|0.973|0.981
    Barren Land|0.969|0.978
    Snow and ice|0.992|0.998"""
    '''
    with open(csv_file, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter="|")  # delimiter?
        string = str()
        for row in csvreader:
            string += "\n" + str("|".join(row))
        string = string.strip("\n")  # remove first newline!
        return string


def csv_to_dictionary(csv):
    """
    Transform input from "special" csv into a python dictionary with namedtuples
    as values. Note, "strings" of interest are hardcoded!

    Also, fix the re-definition of the function transform(). See
    <http://stackoverflow.com/q/30204197/1172302>

    Parameters
    ----------
    csv

    Returns
    -------
    A dictionary with named tuples

    """
    # split input in rows
    rows = csv.split("\n")
    dictionary = {}  # empty dictionary
    fields = rows.pop(0).split("|")[1:]  # header

    strings = ("TIRS10", "TIRS11")
    if any(string in fields for string in strings):

        def transform(row):
            """
            Transform an input row in to a named tuple, then feed it in to a
            dictionary.
            """
            # split row in elements
            elements = row.split("|")

            # key: 1st column, replace
            key = replace_dot_comma_space(elements[0])

            # namedtuple
            ect = namedtuple(key, [fields[0], fields[1]])

            # feed namedtuples
            ect.TIRS10 = is_number(elements[1])
            ect.TIRS11 = is_number(elements[2])

            # feed dictionary
            dictionary[key] = dictionary.get(key, ect)

    strings = ("b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7")
    if any(string in fields for string in strings):

        def transform(row):
            """
            Transform an input row in to a named tuple, then feed it in to a
            dictionary.
            """
            # split row in elements
            elements = row.split("|")

            # key: 1st column, replace
            key = replace_dot_comma_space(elements[0])

            # *** small modification for the CWV field ***
            fields[0] = "cwv"

            # named tuples
            cwv = namedtuple(
                key,
                [
                    replace_dot_comma_space(fields[0]),
                    replace_dot_comma_space(fields[1]),
                    replace_dot_comma_space(fields[2]),
                    replace_dot_comma_space(fields[3]),
                    replace_dot_comma_space(fields[4]),
                    replace_dot_comma_space(fields[5]),
                    replace_dot_comma_space(fields[6]),
                    replace_dot_comma_space(fields[7]),
                    replace_dot_comma_space(fields[8]),
                    replace_dot_comma_space(fields[9]),
                ],
            )

            # feed named tuples
            cwv.subrange = to_tuple(elements[1])
            cwv.b0 = is_number(elements[2])
            cwv.b1 = is_number(elements[3])
            cwv.b2 = is_number(elements[4])
            cwv.b3 = is_number(elements[5])
            cwv.b4 = is_number(elements[6])
            cwv.b5 = is_number(elements[7])
            cwv.b6 = is_number(elements[8])
            cwv.b7 = is_number(elements[9])
            cwv.rmse = is_number(elements[10])
            dictionary[key] = dictionary.get(key, cwv)  # feed dictionary

    list(map(transform, rows))
    return dictionary


def get_average_emissivities():
    """
    Read comma separated values for average emissivities and return a
    dictionary wiht named tuples
    """

    try:
        # read csv for average emissivities, convert to string
        csvstring = csv_reader("average_emissivity.csv")

    except:
        csvstring = AE_STRING

    # convert string to dictionary
    average_emissivities = csv_to_dictionary(csvstring)

    # return the dictionary with coefficients
    return average_emissivities


def get_column_water_vapor():
    """
    Read comma separated values for column water vapor coefficients and return
    a dictionary wiht named tuples
    """

    try:
        # read csv for average emissivities, convert to string
        csvstring = csv_reader("cwv_coefficients.csv")
    except:
        csvstring = CWV_STRING

    # convert string to dictionary
    column_water_vapor_coefficients = csv_to_dictionary(csvstring)

    # return the dictionary with coefficients
    return column_water_vapor_coefficients


# main
def main():
    """
    Main function:
    - reads a special csv file (or a multi-line string)
    - converts and returns a dictionary which contains named tupples

    - accepted csv are:
      - average emissivity coefficients
      - column water vapor
    """

    # user requested file?
    global CSVFILE

    if set_csvfile():
        CSVFILE = set_csvfile()
        print(" * Reading comma separated values from:", CSVFILE)

    else:
        raise IOError("Please define a file to read comma-separated-values from!")

    # convert csv file to string
    csvstring = csv_reader(CSVFILE)

    # convert string to dictionary
    coefficients_dictionary = csv_to_dictionary(csvstring)  # csv < from string

    # report on user requested file
    if set_csvfile():
        msg = "   > Dictionary with coefficients "
        msg += str("(note, it contains named tuples):\n\n")
        print(msg, coefficients_dictionary)

    # return the dictionary with coefficients
    return coefficients_dictionary


# Test data
def test_csvfile(infile):
    """
    Test helper and main functions using as input a csv file.
    """
    global CSVFILE
    CSVFILE = infile
    print("CSVFILE (global variable) = ", CSVFILE)

    print("Test helper and main functions using as input a csv file.")
    print()

    number = random.randint(1.0, 10.0)
    print(" * Testing helper function 'is_number':", is_number(number))

    if not infile:
        csvfile = "average_emissivity.csv"
    else:
        csvfile = infile

    print(" * Testing 'csv_reader' on", csvfile, ":\n\n", csv_reader(csvfile))
    print()

    csvstring = csv_reader(csvfile)
    print(" * Testing 'csv_to_dictionary':\n\n", csv_to_dictionary(csvstring))
    print()

    d = csv_to_dictionary(csvstring)
    somekey = random.choice(list(d.keys()))
    print("* Some random key:", somekey)

    fields = d[somekey]._fields
    print("* Fields of namedtuple:", fields)

    random_field = random.choice(fields)
    print("* Some random field:", random_field)
    # print "* Return values (namedtuple):", d[somekey].TIRS10, d[somekey].TIRS11
    print(
        "* Return values (namedtuple):",
        (
            "subrange",
            d[somekey].subrange,
            "b0",
            d[somekey].b0,
            "b1",
            d[somekey].b1,
            "b2",
            d[somekey].b2,
            "b3",
            d[somekey].b3,
            "b4",
            d[somekey].b4,
            "b5",
            d[somekey].b5,
            "b6",
            d[somekey].b6,
            "b7",
            d[somekey].b7,
            "rmse",
            d[somekey].rmse,
        ),
    )


# test_using_file(CSVFILE)  # Ucomment to run test function!
# CSVFILE = "cwv_coefficients.csv"
# test_csvfile("cwv_coefficients.csv")
# CSVFILE = ''


def test(testdata):
    """
    Test helper and main functions using as input a multi-line string.
    """
    number = random.randint(1.0, 10.0)
    print(" * Testing 'is_number':", is_number(number))
    print()

    """
    Testing the process...
    """
    d = csv_to_dictionary(testdata)
    print("Dictionary is:\n", d)
    print()

    somekey = random.choice(list(d.keys()))
    print("Some random key:", somekey)
    print()

    fields = d[somekey]._fields
    print("Fields of namedtuple:", fields)
    print()

    random_field = random.choice(fields)
    print("Some random field:", random_field)
    print("Return values (namedtuple):", d[somekey].TIRS10, d[somekey].TIRS11)


testdata = """LandCoverClass|TIRS10|TIRS11
Cropland|0.971|0.968
Forest|0.995|0.996
Grasslands|0.970|0.971
Shrublands|0.969|0.970
Wetlands|0.992|0.998
Waterbodies|0.992|0.998
Tundra|0.980|0.984
Impervious|0.973|0.981
Barren_Land|0.969|0.978
Snow_and_Ice|0.992|0.998"""

# test(testdata)  # Ucomment to run the test function!

""" Output ------------------------------
{'Wetlands': <class '__main__.Wetlands'>,
 'Snow_and_Ice': <class '__main__.Snow_and_Ice'>,
 'Impervious': <class '__main__.Impervious'>,
 'Grasslands': <class '__main__.Grasslands'>,
 'Shrublands': <class '__main__.Shrublands'>,
 'Cropland': <class '__main__.Cropland'>,
 'Tundra': <class '__main__.Tundra'>,
 'Barren_Land': <class '__main__.Barren_Land'>,
 'Forest': <class '__main__.Forest'>,
 'Waterbodies': <class '__main__.Waterbodies'>}
------------------------------------ """

if __name__ == "__main__":
    main()
