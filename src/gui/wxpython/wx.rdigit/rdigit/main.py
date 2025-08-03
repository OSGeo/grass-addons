"""!
@package vdigit.main

@brief wxGUI vector digitizer

Classes:
 - main::VDigit

(C) 2007-2011 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Martin Landa <landa.martin gmail.com>
"""

try:
    from rdigit.wxdigit import IRDigit, GV_LINES, CFUNCTYPE

    haveRDigit = True
    errorMsg = ""
except (ImportError, NameError) as err:
    haveRDigit = False
    errorMsg = err
    print(errorMsg)
    GV_LINES = -1

    class IRDigit:
        def __init__(self):
            pass


class RDigit(IRDigit):
    def __init__(self, mapwindow):
        """!Base class of vector digitizer

        @param mapwindow reference to mapwindow (mapdisp_window.BufferedWindow) instance
        """
        IRDigit.__init__(self, mapwindow)
