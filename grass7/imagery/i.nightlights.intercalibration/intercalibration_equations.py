# -*- coding: utf-8 -*-
"""
Convert (and export -- needs uncommenting!) intercalibration equations
(strings), sourced in form of csv, to human readable string representations
(__str__ method of a model's class) and r.mapcalc compatible expressions.

@author: nik | Created on Wed Mar 11 18:34:03 2015
"""

import os
from io import StringIO
import csv
import collections

csvstring = """csvauthor|model|formula
ELVIDGE2009|DNadj. = ({c0}) + ({c1}) * DN + ({c2}) * DN^2|({c0}) + ({c1})*{dummy} + ({c2})*{dummy}^2
ELVIDGE2014|DNadj. = ({c0}) + ({c1}) * DN + ({c2}) * DN^2|({c0}) + ({c1})*{dummy} + ({c2})*{dummy}^2
LIU2012|DNadj. = {c0} + {c1} * DN + {c2} * DN^2|({c0}) + ({c1})*{dummy} +({c2})*{dummy}^2
WU2013|DNc + 1 = {a} * (DNm + 1)^{b}|({a}) * ({dummy} + 1)^({b})"""

# fake it...
csvfile = StringIO(csvstring)


def csv_to_dictionary(csvfile):
    """
    """
    equations = {}  # empty dictionary
    #csvFile = open(csvfile, 'rb')
    csvReader = csv.reader(csvfile, delimiter='|')

    rows = []
    fields = []
    for row in csvReader:
        rows.append(row)
    fields = rows.pop(0)[1:]  # header

    def transform(row):
        """
        """
        author = row[0].replace(" ", "_")  # key: class name, replace ''w/ _

        # namedtuple
        strings = collections.namedtuple(author, [fields[0], fields[1]])

        # feed namedtuples
        strings.model, strings.formula = (str(row[1]), str(row[2]))

        # feed EQUATION
        equations[author] = equations.get(author, strings)

    # apply helper function to all rows
    map(transform, rows)

    # return requestred dictionary
    return equations


def export_to_ascii(dictionary, filename, separator):
    """
    Exporting ... to an ASCII file
    """

    # convert dictionary to string
    dictionary = str(dictionary)

    # define filename
    filename += '.py'

    # don't overwrite!
    if not os.path.exists(filename):

        # structure informative message
        msg = '> Exporting python dictionary as is...'
        print(msg)

        # open, write and close file
        asciif = open(filename, 'w')
        asciif.write(dictionary)
        asciif.close()

    else:
        print('{f} already exists!'.format(f=filename))


def main():
    """
    Execute main program. Note, filename is hardcoded!
    """
    # csvfile = 'equations.csv'
    dictionary = csv_to_dictionary(csvfile)
    # print dictionary

    # uncomment to export, hardcoded filename
    # doesn't make sense with named tuples though!
    # asciifile = 'intercalibration_equations.ascii'
    # export_to_ascii(dictionary, asciifile, # separator='|')
    return dictionary


if __name__ == "__main__":
    main()
