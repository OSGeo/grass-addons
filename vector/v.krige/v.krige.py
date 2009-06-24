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

import os, sys

try:
    import rpy2.robjects as robjects
    haveRpy2 = True
except ImportError:
    print >> sys.stderr, "Rpy2 not found. Please install it and re-run."
    haveRpy2 = False

import grass.script as grass 

GUIModulesPath = os.path.join(os.getenv("GISBASE"), "etc", "wxpython", "gui_modules")
sys.path.append(GUIModulesPath)

import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import gselect

import wx
import wx.lib.flatnotebook as FN

#@TODO(anne): check all dependencies and data at the beginning:
# grass - rpy2 - R - one of automap/gstat/geoR
# a nice splash screen like QGIS does can fit the purpose, with a log message on the bottom and
# popup windows for missing stuff messages.
# For the moment, deps are checked when creating the notebook pages for each package, and the
# data availability when clicking Run button. Quite late.

### i18N
import gettext
gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode=True)

#global variables
gisenv = grass.gisenv()

#classes in alphabetical order

class KrigingPanel(wx.Panel):
    """ Main panel. Contains all widgets except Menus and Statusbar. """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent 
        self.border = 5
        
#    1. Input data 
        InputBoxSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label=_("Input Data")), 
                                          orient=wx.HORIZONTAL)
        
        flexSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        flexSizer.AddGrowableCol(1)

        flexSizer.Add(item = wx.StaticText(self, id=wx.ID_ANY, label=_("Point dataset:")),
                      flag = wx.ALIGN_CENTER_VERTICAL)
        self.InputDataMap = gselect.VectorSelect(parent = self,
                                                 ftype = 'points',
                                                 updateOnPopup = False)
        wx.CallAfter(self.InputDataMap.GetElementList)
        
        flexSizer.Add(item = self.InputDataMap)
        
        flexSizer.Add(item = wx.StaticText(self, id=wx.ID_ANY, label=_("Column:")),
                      flag=wx.ALIGN_CENTER_VERTICAL)
        self.InputDataColumn = gselect.ColumnSelect(self, id=wx.ID_ANY)
        flexSizer.Add(item = self.InputDataColumn)
        
        self.InputDataMap.GetChildren()[0].Bind(wx.EVT_TEXT, self.OnInputDataChanged)
        
        InputBoxSizer.Add(item = flexSizer)
        
#    2. Kriging. In book pages one for each R package. Includes variogram fit.
        KrigingSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label=_("Kriging")), wx.HORIZONTAL)

        self.RPackagesBook = FN.FlatNotebook(parent=self, id=wx.ID_ANY,
                                        style=FN.FNB_BOTTOM |
                                        FN.FNB_NO_NAV_BUTTONS |
                                        FN.FNB_FANCY_TABS | FN.FNB_NO_X_BUTTON)

        self.__createAutomapPage()
        self.__createGstatPage()
        self.__createGeoRPage()
        
        #@TODO(anne): check this dependency at the beginning.
        if self.RPackagesBook.GetPageCount() == 0:
            wx.MessageBox(parent=self,
                          message=_("No R package with kriging functions available. Install either automap, gstat or geoR."),
                          caption=_("Missing Dependency"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
        
        self.RPackagesBook.SetSelection(0)
        KrigingSizer.Add(self.RPackagesBook, proportion=1, flag=wx.EXPAND)
        
#    3. Run Button and Quit Button
        ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        QuitButton = wx.Button(self, id=wx.ID_EXIT)
        QuitButton.Bind(wx.EVT_BUTTON, self.OnCloseWindow)
        RunButton = wx.Button(self, id=wx.ID_ANY, label=_("Run")) # no stock ID for Run button.. 
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
            self.AutomapPanel = RBookAutomapPanel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.AutomapPanel, text="automap")
        else:
            pass

    def __createGstatPage(self):
        if robjects.r.require('gstat'):
            self.GstatPanel = RBookPanel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.GstatPanel, text="gstat")
        else:
            pass

    def __createGeoRPage(self):
        if robjects.r.require('geoR'):
            self.GeoRPanel = RBookPanel(self, id=wx.ID_ANY)
            self.RPackagesBook.AddPage(page=self.GeoRPanel, text="geoR")
        else:
            pass

    def OnInputDataChanged(self, event):
        """Refreshes list of columns

        @todo: layer select
        """
        self.InputDataColumn.InsertColumns(vector = event.GetString(),
                                           layer = 1, excludeKey = True,
                                           type = ['integer', 'double precision'])
        
    def OnRunButton(self,event):
        """ Execute R analysis. """
        
        #-1: get the selected notebook page. The user shall know that he/she can modify settings in all
        # pages, but only the selected one will be executed when Run is pressed.
        self.SelectedPanel = self.RPackagesBook.GetCurrentPage()
        
        #0. require packages. See creation of the notebook pages and note after import directives.
        
        #1. get the data in R format, i.e. SpatialPointsDataFrame
        self.InputData = robjects.r.readVECT6(self.InputDataMap.GetValue(), type= 'point')
        #2. collect options
        self.Column = self.InputDataColumn.GetValue() 
        #@TODO(anne): pick up parameters if user chooses to set variogram parameters.
        #3. Fit variogram
        self.parent.log.write(_("Variogram fitting"))
        self.Formula = robjects.r['as.formula'](robjects.r.paste(self.Column, "~ 1"))        
        Variogram = self.SelectedPanel.FitVariogram(self.Formula, self.InputData)
        # print variogram?
#        robjects.r.plot(Variogram.r['exp_var'], Variogram.r['var_model'])
        self.parent.log.write(_("Variogram fitted."))

        #4. Kriging
#        self.parent.log.write('Kriging...')
        ## AUTOMAP
        #@TODO(anne): the prediced values grid is autogenerated without projection. wait for patch.
        #self.KrigingResult = robjects.r.autoKrige(self.Formula, self.InputData)
#        self.parent.log.write('Kriging performed..')
        
        #5. Format output
        
    def OnCloseWindow(self, event):
        """ Cancel button pressed"""
        self.parent.Close()
        event.Skip()

class KrigingModule(wx.Frame):
    """ Kriging module for GRASS GIS. Depends on R and its packages gstat and geoR. """
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        # setting properties and all widgettery
        self.SetTitle(_("Kriging Module"))
        self.log = Log(self) # writes on statusbar
        self.CreateStatusBar()
        self.log.write(_("Ready."))
        
        self.Panel = KrigingPanel(self)
        # size. It is the minimum size. No way to get it in a single command.
        self.SetMinSize(self.GetBestSize())
        self.SetSize(self.GetBestSize())
        
    
class Log:
    """ The log output is redirected to the status bar of the containing frame. """
    def __init__(self, parent):
        self.parent = parent

    def write(self, text_string):
        """ Updates status bar """
        self.parent.SetStatusText(text_string.strip())

class RBookPanel(wx.Panel):
    """ Generic notebook page with all widgets and empty kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        # unlock options as soon as they are available. Stone soup!
        VariogramSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, 
                                                                label=_("Variogram fitting")), wx.VERTICAL)
        VariogramCheckBox = wx.CheckBox(self, id=wx.ID_ANY, label=_("Auto-fit variogram"))
        VariogramCheckBox.SetValue(state = True) # check it by default
        ParametersSizer = wx.FlexGridSizer(cols=3, hgap=5, vgap=5)        
        
        for n in ["Sill", "Nugget", "Range"]:
            setattr(self, n+"Sizer", (wx.BoxSizer(wx.HORIZONTAL)))
            setattr(self, n+"Text", (wx.StaticText(self, id= wx.ID_ANY, label = _(n))))
            setattr(self, n+"Ctrl", (wx.SpinCtrl(self, id = wx.ID_ANY, max=sys.maxint)))
            a = getattr(self, n+"Sizer")
            a.Add(getattr(self, n+"Text"), proportion=0, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER | wx.ALL, border=3)
            a.Add(getattr(self, n+"Ctrl"), proportion=0, flag=wx.ALIGN_RIGHT | wx.ALL, border=3)
            ParametersSizer.Add(a)#, proportion = 0, flag=wx.EXPAND | wx.ALL, border=3)
        
        VariogramSizer.Add(VariogramCheckBox, proportion=1, flag=wx.EXPAND | wx.ALL, border=3)
        VariogramSizer.Add(ParametersSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        #@TODO(anne); hides Parameters when Autofit variogram is selected
#        VariogramCheckBox.Bind(wx.EVT_CHECKBOX, self.HideOptions)
        
        self.KrigingList = ["Ordinary kriging", "Universal Kriging", "Block kriging"] #@FIXME: i18n on the list?
        KrigingRadioBox = wx.RadioBox(self, id=wx.ID_ANY, label=_("Kriging techniques"), 
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            choices=self.KrigingList, majorDimension=1, style=wx.RA_SPECIFY_COLS)
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(VariogramSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        Sizer.Add(KrigingRadioBox,  proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        
        self.SetSizerAndFit(Sizer)
    
    def FitVariogram():
        pass
    
    def DoKriging():
        pass
    
    def HideOptions(self, event):
        for n in self.ParametersSizer.GetChildren(): n.Disable()
        #@TODO(anne): set it right.
    
class RBookAutomapPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific automap options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        
    def FitVariogram(self, Formula, InputData):
        return robjects.r.autofitVariogram(Formula, InputData)
        
    def DoKriging():
        #BUG: remove grid creation when automap command will be corrected.
        #PredictionGrid = grass.run_command("v.mkgrid")
        pass
        
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

    #@TODO(anne):add here all dependency checking
    if not haveRpy2:
        sys.exit(1)

    app = wx.App()
    k = KrigingModule(parent=None)
    k.Centre()
    k.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
