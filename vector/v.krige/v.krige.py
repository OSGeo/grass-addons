#!/usr/bin/env python
"""
MODULE:    v.krige

AUTHOR(S): Anne Ghisla <a.ghisla AT gmail.com>

PURPOSE:   Performs ordinary kriging

DEPENDS:   R 2.8, package automap or geoR or gstat

COPYRIGHT: (C) 2009 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import wx
import os, sys
#@FIXME(anne): this commented statement gives error: no module named script.
# @martinl: what does grass.script mean?
#import grass.script as grass 
import grass 

import wx.lib.flatnotebook as FN

try:
    import rpy2.robjects as robjects
    haveRpy2 = True
except ImportError:
    print >> sys.stderr, "Rpy2 not found. Please install it and re-run."
    haveRpy2 = False

#@TODO(anne): check all dependencies and data at the beginning.
# a nice splash screen like QGIS does can fit the purpose, with a log message on the bottom and
# popup windows for missing stuff messages.
# For the moment, deps are checked when creating the notebook pages for each package, and the
# data availability when clicking Run button. Quite late.

#$TODO(anne): add gettext

#global variables
gisenv = grass.gisenv()

#classes in alphabetical order
class KrigingPanel(wx.Panel):
    """
    Main panel. Contains all widgets except Menus and Statusbar.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent 
        self.border = 7
        
#    1. Input data 
        InputBoxSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label='Input Data'), 
            orient=wx.HORIZONTAL)

        self.SampleList = self.__getVectors()
        self.InputDataLabel = wx.StaticText(self, id=wx.ID_ANY, label="Point dataset")
        self.InputDataChoicebox = wx.Choice(self, id=wx.ID_ANY, pos=wx.DefaultPosition, 
            choices=self.SampleList)
        InputBoxSizer.Add(self.InputDataLabel, proportion=0, flag=wx.CENTER | wx.ALL, border=self.border)
        InputBoxSizer.Add(self.InputDataChoicebox, proportion=0, flag=wx.CENTER| wx.ALL, border=self.border)

#    2. Kriging. In book pages one for each R package. Includes variogram fit.
        KrigingSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label='Kriging'), wx.HORIZONTAL)

        self.RPackagesBook = FN.FlatNotebook(parent=self, id=wx.ID_ANY,
                                        style=FN.FNB_BOTTOM |
                                        FN.FNB_NO_NAV_BUTTONS |
                                        FN.FNB_FANCY_TABS | FN.FNB_NO_X_BUTTON)

        self.__createAutomapPage()
        self.__createGstatPage()
        self.__createGeoRPage()
        
        if self.RPackagesBook.GetPageCount() == 0:
            wx.MessageBox(parent=self,
                          message=("No R package with kriging functions available. Install either automap, gstat or geoR."),
                          caption=("Missing Dependency"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
        
        self.RPackagesBook.SetSelection(0)
        KrigingSizer.Add(self.RPackagesBook, proportion=1, flag=wx.EXPAND)
        
#    3. Run Button and Quit Button
        ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        QuitButton = wx.Button(self, id=wx.ID_EXIT)
        QuitButton.Bind(wx.EVT_BUTTON, self.OnCloseWindow)
        RunButton = wx.Button(self, id=wx.ID_ANY, label='Run')
        RunButton.Bind(wx.EVT_BUTTON, self.OnRunButton)
        ButtonSizer.Add(QuitButton, proportion=0, flag=wx.ALIGN_RIGHT | wx.ALL, border=self.border)
        ButtonSizer.Add(RunButton, proportion=0, flag=wx.ALIGN_RIGHT | wx.ALL, border=self.border)
        
        
#    Main Sizer. Add each child sizer as soon as it is ready.
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(InputBoxSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=self.border)
        Sizer.Add(KrigingSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=self.border)
        Sizer.Add(ButtonSizer, proportion=0, flag=wx.ALIGN_RIGHT | wx.ALL, border=self.border)
        self.SetSizerAndFit(Sizer)
        
    # consider refactor this!
    def __createAutomapPage(self):
        # 1. check if the package automap exists
        if robjects.r.require('automap') and robjects.r.require('spgrass6'):
            self.AutomapPanel = wx.Panel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.AutomapPanel, text="automap")
            
            # unlock options as soon as they are available. Stone soup!
            self.VariogramList = ["Auto-fit variogram"]#, "Choose variogram parameters"] 
            VariogramRadioBox = wx.RadioBox(self.AutomapPanel, id=wx.ID_ANY, label="Variogram Fitting", 
                pos=wx.DefaultPosition, #size=wx.DefaultSize,
                choices=self.VariogramList, majorDimension=1, style=wx.RA_SPECIFY_COLS)
            self.KrigingList = ["Ordinary kriging"]
            KrigingRadioBox = wx.RadioBox(self.AutomapPanel, id=wx.ID_ANY, label="Kriging techniques", 
                pos=wx.DefaultPosition,# size=wx.DefaultSize,
                choices=self.KrigingList, majorDimension=1, style=wx.RA_SPECIFY_COLS)
            
            Sizer = wx.BoxSizer(wx.VERTICAL)
            Sizer.Add(VariogramRadioBox, proportion=0, flag=wx.EXPAND | wx.ALL, border=0)
            Sizer.Add(KrigingRadioBox,  proportion=0, flag=wx.EXPAND | wx.ALL, border=0)
            
            self.AutomapPanel.SetSizerAndFit(Sizer)

        else:
            pass

    def __createGstatPage(self):
        if robjects.r.require('gstat'):
            self.GstatPanel = wx.Panel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.GstatPanel, text="gstat")
            # add stuff to panel
        else:
            pass

    def __createGeoRPage(self):
        if robjects.r.require('geoR'):
            self.GeoRPanel = wx.Panel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.GeoRPanel, text="geoR")
            # add stuff to panel
        else:
            pass


        
    def __getVectors(self, *args, **kwargs):
        """Get list of tables for given location and mapset"""
        vectors = grass.list_grouped('vect')[gisenv['MAPSET']]
        #@WARNING: this cycle is quite time-consuming. 
        # see if it is possible to postpone this filtering, and immediately show the dialog.
        if vectors == []:
            wx.MessageBox(parent=self,
                          message=("No vector maps available. Check if the location is correct."),
                          caption=("Missing Input Data"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)        
        pointVectors = []
        for n in vectors:
            try:
                if grass.vector_info_topo(n)['points'] > 0:
                    pointVectors.append(n)
            except KeyError:
                pass
        if pointVectors == []:
            wx.MessageBox(parent=self,
                          message=("No point vector maps available. Check if the location is correct."),
                          caption=("Missing Input Data"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
        return sorted(pointVectors)
    
    def OnRunButton(self,event):
        """ Execute R analysis. """
        #0. require packages. See creation of the notebook pages and note after import directives.
        
        #1. get the data in R format, i.e. SpatialPointsDataFrame
        self.InputData = robjects.r.readVECT6(self.InputDataChoicebox.GetStringSelection(), type= 'point')
        #2. collect options
        #@TODO(anne): let user pick up the column name from a list. this is hardwired code.
        self.Column = 'elev' 
        #3. Fit variogram
        self.parent.log.write('Variogram fitting')
       
        self.Formula = robjects.r['as.formula'](robjects.r.paste(self.Column, "~ 1"))        
        self.Variogram= robjects.r.autofitVariogram(self.Formula, self.InputData)
        # print variogram somehow
        robjects.r.plot(self.Variogram)
        
        self.parent.log.write('Variogram fitted.')

        #4. Kriging
        self.parent.log.write('Kriging...')
        #@TODO(anne): the prediced values grid is autogenerated without projection. wait for patch.
        self.KrigingResult = robjects.r.autoKrige(self.Formula, self.InputData)
        self.parent.log.write('Kriging performed..')
        
        #5. Format output
        
    def OnCloseWindow(self, event):
        """ Cancel button pressed"""
        self.parent.Close()
        event.Skip()

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
        
        self.Panel = KrigingPanel(self)
        # size. It is the minimum size. No way to get it in a single command.
        self.SetMinSize(self.GetBestSize())
        self.SetSize(self.GetBestSize())
        
    
class Log:
    """
    The log output is redirected to the status bar of the containing frame.
    """
    def __init__(self, parent):
        self.parent = parent

    def write(self, text_string):
        """Update status bar"""
        self.parent.SetStatusText(text_string.strip())
        
#main
def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    #@TODO(anne): add command line arguments acceptance.

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

    if not haveRpy2:
        sys.exit(1)

    app = wx.App()
    k = KrigingModule(parent=None)
    k.Centre()
    k.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
