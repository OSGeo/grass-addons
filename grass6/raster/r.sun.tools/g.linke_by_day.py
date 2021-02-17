#!/usr/bin/python
############################################################################
#
# MODULE:       g.linke_by_day.py
#
# AUTHOR(S):    Hamish Bowman, Dunedin, New Zealand
#
# PURPOSE:      Interpolate day of year into Linke turbidity value
#
# COPYRIGHT:    (c) 2009 Hamish Bowman, and The GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
############################################################################
#
# Requires Numeric module (NumPy) and SciPy from  http://numpy.scipy.org/
#   (older versions only implement linear interpolation & will throw an error)
# Assumes monthly value corresponds to the actual mid-month value
#
# USAGE: g.linke_by_day [day number (1-365)]
#

import sys

if len(sys.argv) != 2:
    print "USAGE: g.linke_by_day [day number (1-365)]"
    sys.exit(1)
else:
    day = float(sys.argv[1])

if day < 1 or day > 365:
    print "USAGE: g.linke_by_day [day number (1-365)]"
    sys.exit(1)


def main():
    import numpy
    from scipy.interpolate import interpolate

    ##### put monthly data here
    # e.g. northern hemisphere mountains:  (from the r.sun help page)
    #    [jan,feb,mar,...,dec]
    linke_data = numpy.array ([1.5,1.6,1.8,1.9,2.0,2.3,2.3,2.3,2.1,1.8,1.6,1.5])
    ####

    linke_data_wrap = numpy.concatenate((linke_data[9:12],
                                         linke_data,
                                         linke_data[0:3]))

    monthDays = numpy.array ([0,31,28,31,30,31,30,31,31,30,31,30,31])
    #init empty
    midmonth_day = numpy.array ([0,0,0,0,0,0,0,0,0,0,0,0])
    for i in range(1, 12+1):
        midmonth_day[i-1] = 15 + sum(monthDays[0:i])

    midmonth_day_wrap = numpy.concatenate((midmonth_day[9:12]-365, \
                                           midmonth_day,
                                           midmonth_day[0:3]+365))

    linke = interpolate.interp1d(midmonth_day_wrap, 
                                 linke_data_wrap,
                                 kind='cubic')
    # print data for full year:
    #for i in range(1,365+1):
    #    print("%d %.4f" % (i, linke(i)) )

    print("%.4f" % linke(day) )


if __name__ == "__main__":
    main()
