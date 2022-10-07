"""!
@package LoadConfig.py

@brief Python function to load configuration file for
wmsmenu.py and addserver.py.

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

Functions:
 - loadConfigFile

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

import os
import grass


def loadConfigFile(self):
    """
    @description: Called by the init method of the class wmsFrame.
    Loads the config file and initializes corresponding parameters.
    @todo:None
    @param self: reference variable
    @return: Boolean, True is config file is loaded successfully, else False
    """
    try:
        f = open("config", "r")
        lines = f.readlines()
        f.close()
        # patch4s
        try:
            if len(lines) != 3:
                message = "Insufficient number of arguments,3 parameters required name_url_delimiter, timeoutValueSeconds, urlLength"
                grass.fatal_error(message)
                raise Exception
            self.name_url_delimiter = lines[0].split(":")[1]
            self.timeoutValueSeconds = int(lines[1].split(":")[1])
            self.urlLength = int(lines[2].split(":")[1])
        except Exception as e:
            self.name_url_delimiter = "#"
            self.timeoutValueSeconds = 5
            self.urlLength = 50

        return True
    except:
        return False
