#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
MODULE:    v.autokrige2

AUTHOR(S): Anne Ghisla <a.ghisla AT gmail.com>

PURPOSE:   Performs ordinary kriging

DEPENDS:  R (version?), package automap (geoR? gstat?)

COPYRIGHT: (C) 2009 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

import wx
import sys
import grass

#classes in alphabetical order

class KrigingPanel(wx.Panel):
    """
    Main panel. Contains all widgets except Menus and Statusbar.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent 
        # obtain info about location mapset and so on.
        self.gisenv = grass.gisenv()
        
#    1. Input data 
        InputBoxSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Input Data'), wx.HORIZONTAL)

        self.SampleList = self.__getVectors()
        self.InputDataLabel = wx.StaticText(self, -1, "Point dataset")
        self.InputDataChoicebox = wx.Choice(self, -1, (-1,-1), (-1,-1), self.SampleList)
        InputBoxSizer.Add(self.InputDataLabel, -1, wx.ALIGN_LEFT, 1)
        InputBoxSizer.Add(self.InputDataChoicebox, -1, wx.EXPAND, 1)

#    2. Kriging. In book pages one for each R package. Includes variogram fit.
        KrigingSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Kriging'), wx.HORIZONTAL)
        self.RPackagesBook = RPackagesBook(parent= self)
        KrigingSizer.Add(self.RPackagesBook, wx.EXPAND)
        
#    Main Sizer. Add each child sizer as soon as it is ready.
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(InputBoxSizer, 0, wx.EXPAND, 5)
        Sizer.Add(KrigingSizer, 0, wx.EXPAND, 5)

        self.SetSizerAndFit(Sizer)
        
    def __getVectors(self, *args, **kwargs):
        """Get list of tables for given location and mapset"""
        vectors = grass.list_grouped('vect')[self.gisenv['MAPSET']]
        #@TODO: filter maps and drop the vectors without points
        if vectors == []:
            wx.MessageBox(parent=self,
                          message=("Unable to get list of vectors. Check if the location is correct."),
                          caption=("Error"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
        return sorted(vectors)

class KrigingModule(wx.Frame):
    """
    Kriging module for GRASS GIS. Depends on R and its packages gstat and geoR.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        # setting properties and all widgettery
        self.SetTitle("Kriging Module")
        self.log = Log(self) # writes on statusbar
        self.CreateStatusBar()
        # debug: remove before flight
        self.log.write("Under construction.")
        
        #@TODO(anne): set minimum size around objects.
        
        self.Panel = KrigingPanel(self)
        self.Fit()        
    
class Log:
    """
    The log output is redirected to the status bar of the containing frame.
    """
    def __init__(self, parent):
        self.parent = parent

    def write(self, text_string):
        """Update status bar"""
        self.parent.SetStatusText(text_string.strip())

class RPackagesBook(wx.Notebook):
    """
    Book whose pages are the three R packages providing kriging facilities.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Notebook.__init__(self, parent, *args, **kwargs)
        self.__createAutomapPage()
        self.__createGstatPage()
        self.__createGeoRPage()
    
    # consider refactor this!
    def __createAutomapPage(self):
        self.AutomapPanel = wx.Panel(self, -1)
        self.AddPage(page=self.AutomapPanel, text="automap")
        
        self.VariogramList = ["Auto-fit variogram", "Choose variogram parameters"]
        VariogramRadioBox = wx.RadioBox(self.AutomapPanel, -1, "Variogram Fitting", (-1,-1), wx.DefaultSize, 
            self.VariogramList, 1, wx.RA_SPECIFY_COLS)
        self.KrigingList = ["Ordinary kriging"]
        KrigingRadioBox = wx.RadioBox(self.AutomapPanel, -1, "Kriging techniques", (-1,-1), wx.DefaultSize, 
            self.KrigingList, 1, wx.RA_SPECIFY_COLS)
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(VariogramRadioBox, 0, wx.EXPAND, 5)
        Sizer.Add(KrigingRadioBox, 0, wx.EXPAND, 5)   
        self.AutomapPanel.SetSizerAndFit(Sizer)
        
        # add stuff to panel
    def __createGstatPage(self):
        self.GstatPanel = wx.Panel(self, -1)
        self.AddPage(page=self.GstatPanel, text="gstat")
        # add stuff to panel
    def __createGeoRPage(self):
        self.GeoRPanel = wx.Panel(self, -1)
        self.AddPage(page=self.GeoRPanel, text="geoR")
        # add stuff to panel
       
    def __getColumns(self, driver, database, table):
        """Get list of column of given table"""
        columns = [] 
#        change accordingly
#        cmdColumn = gcmd.Command(['db.columns',
#                                  '--q',
#                                  'driver=%s' % driver,
#                                  'database=%s' % database,
#                                  'table=%s' % table],
#                                 rerr = None)
        for column in cmdColumn.ReadStdOutput():
            columns.append(column)
        return columns
        
#main
def main(argv=None):
    if argv is None:
        argv = sys.argv

    """if len(argv) != 2:
        print >> sys.stderr, __doc__
        sys.exit()"""

    # Command line arguments of the script to be run are preserved by the
    # hotswap.py wrapper but hotswap.py and its options are removed that
    # sys.argv looks as if no wrapper was present.
    #print "argv:", `argv`

    # commmented, as I don't know if the module will need it.
    ##some applications might require image handlers
    #wx.InitAllImageHandlers()

#    app = wx.PySimpleApp() # deprecated?
    app = wx.App()
    k = KrigingModule(parent=None, size=(600,300))
    k.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
