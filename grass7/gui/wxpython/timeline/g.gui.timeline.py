#!/usr/bin/env python
############################################################################
#
# MODULE:    g.gui.timeline.py
# AUTHOR(S): Anna Kratochvilova
# PURPOSE:   Timeline Tool is a wxGUI component (based on matplotlib)
#            which allows the user to compare temporal datasets' extents.
# COPYRIGHT: (C) 2012 by Anna Kratochvilova, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

#%module
#% description: Allows to compare temporal datasets by displaying their temporal extents in a plot.
#%end
#%option G_OPT_STDS_INPUTS
#% required: no
#%end
#%flag
#% key: 3
#% description: Show also 3D plot of spatio-temporal extents
#%end


import os
import sys

import  wx
import gettext

import grass.script as grass

if __name__ == '__main__':
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "gui", "wxpython"))

from timeline.frame import TimelineFrame

def main():
    gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode = True)

    options, flags = grass.parser()

    datasets = options['inputs'].strip().split(',')
    datasets = [data for data in datasets if data]
    view3d = flags['3']

    app = wx.PySimpleApp()
    frame = TimelineFrame(None)
    frame.SetDatasets(datasets)
    frame.Show3D(view3d)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()

