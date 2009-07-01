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
        #@FIXME: still does slow down interface creation. Thread? Put it elsewhere?
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
        
        for Rpackage in ["automap", "gstat", "geoR"]:
            self.CreatePage(package = Rpackage)
        
        #@TODO(anne): check this dependency at the beginning.
        if self.RPackagesBook.GetPageCount() == 0:
            wx.MessageBox(parent=self,
                          message=_("No R package with kriging functions available. Install either automap, gstat or geoR."),
                          caption=_("Missing Dependency"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
        
        self.RPackagesBook.SetSelection(0)
        KrigingSizer.Add(self.RPackagesBook, proportion=1, flag=wx.EXPAND)
        
#    3. Output Parameters.
        OutputSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label=_("Output")), wx.HORIZONTAL)
        
        OutputParameters = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        OutputParameters.AddGrowableCol(1)
        OutputParameters.Add(item = wx.StaticText(self, id=wx.ID_ANY, label=_("Name of the output map:")),
                      flag = wx.ALIGN_CENTER_VERTICAL)
        self.OutputMapName = wx.TextCtrl(self, id=wx.ID_ANY, size=(250,-1))
        OutputParameters.Add(item=self.OutputMapName, flag=wx.EXPAND | wx.ALL)
        self.OverwriteCheckBox = wx.CheckBox(self, id=wx.ID_ANY, label=_("Allow output files to overwrite existing files"))
        self.OverwriteCheckBox.SetValue(state = False)
        OutputParameters.Add(self.OverwriteCheckBox)
        
        OutputSizer.Add(OutputParameters, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        
#    4. Run Button and Quit Button
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
        Sizer.Add(OutputSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=self.border)
        Sizer.Add(ButtonSizer, proportion=0, flag=wx.ALIGN_RIGHT | wx.ALL, border=self.border)
        self.SetSizerAndFit(Sizer)
        
    def CreatePage(self, package):
        """ Creates the three notebook pages, one for each R package """
        if robjects.r.require(package) and robjects.r.require('spgrass6'):
            classobj = eval("RBook"+package+"Panel")
            setattr(self, "RBook"+package+"Panel", (classobj(self, id=wx.ID_ANY)))
            getattr(self, "RBook"+package+"Panel")
            self.RPackagesBook.AddPage(page=getattr(self, "RBook"+package+"Panel"), text=package)
        else:
            pass

    def OnInputDataChanged(self, event):
        """ Refreshes list of columns and fills output map name TextCtrl """
        MapName = event.GetString()
        self.InputDataColumn.InsertColumns(vector = MapName,
                                           layer = 1, excludeKey = True,
                                           type = ['integer', 'double precision'])
        self.OutputMapName.SetValue(MapName.split("@")[0]+"_kriging")
        
    def OnRunButton(self,event):
        """ Execute R analysis. """
        
        #-1: get the selected notebook page. The user shall know that he/she can modify settings in all
        # pages, but only the selected one will be executed when Run is pressed.
        SelectedPanel = self.RPackagesBook.GetCurrentPage()
        
        #0. require packages. See creation of the notebook pages and note after import directives.
        
        #1. get the data in R format, i.e. SpatialPointsDataFrame
        InputData = robjects.r.readVECT6(self.InputDataMap.GetValue(), type= 'point')
        #1.5 create the grid where to estimate values. Not used by block-kriging
        Grid = robjects.r.gmeta2grd()
        Region = grass.region()
        ##create the spatialgriddataframe with these settings
        GridPredicted = robjects.r.SpatialGridDataFrame(Grid,
                                                        data=robjects.r['data.frame']
                                                        (k=robjects.r.rep(1,Region['cols']*Region['rows'])),
                                                        proj4string=robjects.r.CRS(robjects.r.proj4string(InputData)))
        
        #2. collect options
        Column = self.InputDataColumn.GetValue() 
        #@TODO(anne): pick up parameters if user chooses to set variogram parameters.
        #3. Fit variogram. For the moment in batch mode, no interactive window. Stay tuned!
        self.parent.log.write(_("Variogram fitting"))
        Formula = robjects.r['as.formula'](robjects.r.paste(Column, "~ 1"))        
        Variogram = SelectedPanel.FitVariogram(Formula, InputData)
        # print variogram?
        #robjects.r.plot(Variogram.r['exp_var'], Variogram.r['var_model']) #does not work.
        #see if it caused by automap/gstat dedicated plot function.
        self.parent.log.write(_("Variogram fitted."))

        #4. Kriging
        self.parent.log.write('Kriging...')
        KrigingResult = SelectedPanel.DoKriging(formula = Formula, data = InputData, grid = GridPredicted, model = Variogram)
        self.parent.log.write('Kriging performed.')
        
        #5. Format output
        #@IDEA: set a generic f(x) for this too? seems like, because zcol= is only the first peculiar arg for gstat.
        robjects.r.writeRAST6(KrigingResult, vname = self.OutputMapName.GetValue(), zcol='var1.pred',
                              overwrite = self.OverwriteCheckBox.GetValue())
        self.parent.log.write('Yippee! Succeeded! Ready for another run.')
        
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
    """ Generic notebook page with shared widgets and empty kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        # unlock options as soon as they are available. Stone soup!
        self.VariogramSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, 
            label=_("Variogram fitting")), wx.VERTICAL)
        self.ParametersSizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5)        
        
        for n in ["Sill", "Nugget", "Range"]:
            setattr(self, n+"Text", (wx.StaticText(self, id= wx.ID_ANY, label = _(n))))
            setattr(self, n+"Ctrl", (wx.SpinCtrl(self, id = wx.ID_ANY, max=sys.maxint)))
            self.ParametersSizer.Add(getattr(self, n+"Text"))
            self.ParametersSizer.Add(getattr(self, n+"Ctrl"))
        
        #@TODO: deploy this
        #self.ParametersSizer.Add(wx.Button(self, id=wx.ID_ANY, label=_("Interactive variogram fit")))

        self.VariogramSizer.Add(self.ParametersSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        
        #@TODO: unlock options as soon as they are available.
        KrigingList = ["Ordinary kriging"]#, "Universal kriging", "Block kriging"] #@FIXME: i18n on the list?
        KrigingRadioBox = wx.RadioBox(self, id=wx.ID_ANY, label=_("Kriging techniques"), 
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            choices=KrigingList, majorDimension=1, style=wx.RA_SPECIFY_COLS)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.VariogramSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        self.Sizer.Add(KrigingRadioBox,  proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
    
    def FitVariogram(self, *args, **kwargs):
        pass
    
    def DoKriging(self, *args, **kwargs):
        pass
    
    def HideOptions(self, event):
        pass
    
class RBookautomapPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific automap options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        
        self.VariogramCheckBox = wx.CheckBox(self, id=wx.ID_ANY, label=_("Auto-fit variogram"))
        self.VariogramCheckBox.SetValue(state = True) # check it by default
        self.VariogramSizer.Insert(2, self.VariogramCheckBox , proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        self.VariogramCheckBox.Bind(wx.EVT_CHECKBOX, self.HideOptions)
        
        for n in ["Sill", "Nugget", "Range"]:
            getattr(self, n+"Ctrl").Enable(False)
        
        self.SetSizerAndFit(self.Sizer)
        
    def FitVariogram(self, formula, data):
        return robjects.r.autofitVariogram(formula, data)
        
    def DoKriging(self, formula, data, grid, **kwargs):
        KrigingResult = robjects.r.autoKrige(formula, data, grid)
        return KrigingResult.r['krige_output']
    
    def HideOptions(self, event):
        for n in ["Sill", "Nugget", "Range"]:
            if self.VariogramCheckBox.IsChecked():
                getattr(self, n+"Ctrl").Enable(False)
            else:
                getattr(self, n+"Ctrl").Enable(True)
        #@FIXME: was for n in self.ParametersSizer.GetChildren(): n.Enable(False) but doesn't work

class RBookgstatPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific gstat options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        self.SetSizerAndFit(self.Sizer)
        
    def FitVariogram(self, formula, data):
        DataVariogram = robjects.r.variogram(formula, data)
        VariogramModel = robjects.r['fit.variogram'](DataVariogram, model = robjects.r.vgm(1, "Lin"))
        #@TODO: hardcoded on rs dataset. There is a trend indeed.
        return VariogramModel
        
    def DoKriging(self, formula, data, grid,  model):
        KrigingResult = robjects.r.krige(formula, data, grid, model)
        return KrigingResult
    
class RBookgeoRPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific geoR options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        self.SetSizerAndFit(self.Sizer)
        
    def FitVariogram(self, Formula, InputData):
        pass
        
    def DoKriging():
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
