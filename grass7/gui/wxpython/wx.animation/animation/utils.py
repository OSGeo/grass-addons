"""!
@package animation.utils

@brief Miscellaneous functions and enum classes

Classes:
 - utils::TemporalMode
 - utils::TemporalType
 - utils::Orientation
 - utils::ReplayMode


(C) 2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Anna Kratochvilova <kratochanna gmail.com>
"""
import grass.temporal as tgis
import grass.script as grass

from core.gcmd import GException

class TemporalMode:
    TEMPORAL = 1
    NONTEMPORAL = 2

class TemporalType:
    ABSOLUTE = 1
    RELATIVE = 2

class Orientation:
    FORWARD = 1
    BACKWARD = 2

class ReplayMode:
    ONESHOT = 1
    REVERSE = 2
    REPEAT = 3

def validateTimeseriesName(timeseries, etype = 'strds'):
    """!Checks if space time dataset exists and completes missing mapset.

    Raises GException if dataset doesn't exist.
    """
    trastDict = tgis.tlist_grouped(etype)
    if timeseries.find("@") >= 0:
        nameShort, mapset = timeseries.split('@', 1)
        if nameShort in trastDict[mapset]:
            return timeseries
        else:
            raise GException(_("Space time dataset <%s> not found.") % timeseries)


    for mapset, names in trastDict.iteritems():
        if timeseries in names:
            return timeseries + "@" + mapset

    raise GException(_("Space time dataset <%s> not found.") % timeseries)

def validateMapNames(names, etype):
    """!Checks if maps exist and completes missing mapset.

    Input is list of map names.
    Raises GException if map doesn't exist.
    """
    mapDict = grass.list_grouped(etype)

    newNames = []
    for name in names:
        if name.find("@") >= 0:
            nameShort, mapset = name.split('@', 1)
            if nameShort in mapDict[mapset]:
                newNames.append(name)
            else:
                raise GException(_("Map <%s> not found.") % name)
        else:
            found = False
            for mapset, mapNames in mapDict.iteritems():
                if name in mapNames:
                    found = True
                    newNames.append(name + "@" + mapset)
            if not found:
                raise GException(_("Map <%s> not found.") % name)
    return newNames
