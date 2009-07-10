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

## g.parser informations

#%module
#% description: Performs ordinary kriging.
#% keywords: kriging
#%end

#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of point vector map containing sample data
#% required: yes
#%end
#%option
#% key: column
#% type: string
#% description: Column with numerical value to be interpolated
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% label: Name for output raster map
#% description: If omitted, will be <input name>_kriging
#% required : no
#%end
#%option
#% key: package
#% type: string
#% options: gstat, geor
#% answer: gstat
#% description: R package to use
#% required: no
#%end
#%option
#% key: model
#% type: string
#% options: Exp,Sph,Gau,Mat,Lin
#% multiple: yes
#% label: Variogram model(s)
#% description: Leave empty to test all models (requires automap)
#% required: no
#%end
#%option
#% key: range
#% type: integer
#% label: Range value
#% description: Automatically fixed if not set
#% required : no
#%end
#%option
#% key: nugget
#% type: double
#% label: Nugget value
#% description: Automatically fixed if not set
#% required : no
#%end
#%option
#% key: sill
#% type: double
#% label: Sill value
#% description: Automatically fixed if not set
#% required : no
#%end

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

### i18N
import gettext
gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode=True)

#global variables
gisenv = grass.gisenv()
Region = grass.region()
# model list should come from gstat::vgm(), hardwired here.
ModelList = ['Exp','Sph','Gau','Mat','Lin']

#classes in alphabetical order. methods in logical order :)

class Controller():
    """ Executes analysis. For the moment, only with gstat functions."""
       
    def ImportMap(self, map):
        return robjects.r.readVECT6(map, type= 'point')
    
    def CreateGrid(self, inputdata):
        Grid = robjects.r.gmeta2grd()
        GridPredicted = robjects.r.SpatialGridDataFrame(Grid,
                                                        data=robjects.r['data.frame']
                                                        (k=robjects.r.rep(1,Region['cols']*Region['rows'])),
                                                        proj4string=robjects.r.CRS(robjects.r.proj4string(inputdata)))
        return GridPredicted
    
    def ComposeFormula(self, column):
        # will change when the formula will need to be more complex. Not yet.
        Formula = robjects.r['as.formula'](robjects.r.paste(column, "~ 1"))
        return Formula
    
    def FitVariogram(self, formula, inputdata, model, autofit, sill='NA', nugget='NA', range='NA'):
        if autofit:
            robjects.r.require("automap")
            VariogramModel = robjects.r.autofitVariogram(formula, inputdata)
            return VariogramModel.r['var_model'][0]
        else:
            DataVariogram = robjects.r.variogram(formula, inputdata) 
            VariogramModel = robjects.r['fit.variogram'](DataVariogram,
                                                         model = robjects.r.vgm(psill = sill,
                                                                                model = model,
                                                                                nugget = nugget,
                                                                                range = range))
            return VariogramModel
        
        #@TODO: print variogram?
        ##robjects.r.plot(Variogram.r['exp_var'], Variogram.r['var_model']) #does not work.
        ##see if it caused by automap/gstat dedicated plot function.
        #self.parent.log.write(_("Variogram fitted."))
    
    def DoKriging(self, formula, inputdata, grid, model):
        KrigingResult = robjects.r.krige(formula, inputdata, grid, model)
        return KrigingResult
 
    def ExportMap(self, map, column, name, overwrite):
        robjects.r.writeRAST6(map, vname = name, zcol = column, overwrite = overwrite)
        
    def Run(self, input, column, output, package, sill, nugget, range, logger, overwrite, model = None):
        """ Wrapper for all functions above. """
        # Load packages
        robjects.r.require(package)
        robjects.r.require("spgrass6")
        
        # Get data and create grid
        logger.message(_("Importing data..."))
        InputData = self.ImportMap(input)
        logger.message("Imported.")
        GridPredicted = self.CreateGrid(InputData)
        
        # Fit Variogram
        logger.message(_("Fitting variogram..."))
        Formula = self.ComposeFormula(column)
        Variogram = self.FitVariogram(Formula,
                                      InputData,
                                      model = model,
                                      autofit = model is None,
                                      sill = sill,
                                      nugget = nugget,
                                      range = range)
        logger.message(_("Variogram fitted."))
        
        # Krige
        logger.message(_("Kriging..."))
        KrigingResult = self.DoKriging(Formula, InputData, GridPredicted, Variogram)
        logger.message(_("Kriging performed."))
        
        # Export map
        self.ExportMap(map = KrigingResult,
                       column='var1.pred',
                       name = output,
                       overwrite = overwrite)
        
class KrigingPanel(wx.Panel):
    """ Main panel. Contains all widgets except Menus and Statusbar. """
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent 
        self.border = 5
        
        #controller istance
        self.Controller = Controller()
        
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
        self.InputDataColumn.SetSelection(0)
        flexSizer.Add(item = self.InputDataColumn)
        
        self.InputDataMap.GetChildren()[0].Bind(wx.EVT_TEXT, self.OnInputDataChanged)
        
        InputBoxSizer.Add(item = flexSizer)
        
#    2. Kriging. In book pages one for each R package. Includes variogram fit.
        KrigingSizer = wx.StaticBoxSizer(wx.StaticBox(self, id=wx.ID_ANY, label=_("Kriging")), wx.HORIZONTAL)

        self.RPackagesBook = FN.FlatNotebook(parent=self, id=wx.ID_ANY,
                                        style=FN.FNB_BOTTOM |
                                        FN.FNB_NO_NAV_BUTTONS |
                                        FN.FNB_FANCY_TABS | FN.FNB_NO_X_BUTTON)
        
        for Rpackage in ["gstat", "geoR"]:
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
        
        OutputParameters = wx.GridBagSizer(hgap=5, vgap=5)
        OutputParameters.AddGrowableCol(1)
        OutputParameters.Add(item = wx.StaticText(self, id=wx.ID_ANY, label=_("Name for the output raster map:")),
                             flag = wx.ALIGN_CENTER_VERTICAL,
                             pos = (0, 0))
        self.OutputMapName = gselect.Select(parent = self, id = wx.ID_ANY,
                                            type = 'raster',
                                            mapsets = [grass.gisenv()['MAPSET']])
        OutputParameters.Add(item=self.OutputMapName, flag=wx.EXPAND | wx.ALL,
                             pos = (0, 1))
        self.OverwriteCheckBox = wx.CheckBox(self, id=wx.ID_ANY,
                                             label=_("Allow output files to overwrite existing files"))
        self.OverwriteCheckBox.SetValue(state = False)
        OutputParameters.Add(item = self.OverwriteCheckBox,
                             pos = (1, 0), span = (1, 2))
        
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

    def OnInputDataChanged(self, event):
        """ Refreshes list of columns and fills output map name TextCtrl """
        MapName = event.GetString()
        self.InputDataColumn.InsertColumns(vector = MapName,
                                           layer = 1, excludeKey = True,
                                           type = ['integer', 'double precision'])
        self.InputDataColumn.SetSelection(0)
        self.OutputMapName.SetValue(MapName.split("@")[0]+"_kriging")
        
    def OnRunButton(self,event):
        """ Execute R analysis. """
        #@FIXME: send data to main method instead of running it here.
        
        #-1: get the selected notebook page. The user shall know that he/she can modify settings in all
        # pages, but only the selected one will be executed when Run is pressed.
        SelectedPanel = self.RPackagesBook.GetCurrentPage()
        
        self.Controller.Run(input = self.InputDataMap.GetValue(),
                            column = self.InputDataColumn.GetValue(),
                            output = self.OutputMapName.GetValue(),
                            overwrite = self.OverwriteCheckBox.IsChecked(),
                            package = self.RPackagesBook.GetPageText(self.RPackagesBook.GetSelection()),
                            sill = SelectedPanel.SillCtrl.GetValue(),
                            nugget = SelectedPanel.NuggetCtrl.GetValue(),
                            range = SelectedPanel.RangeCtrl.GetValue(),
                            logger = self.parent.log)
        
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
        self.log = Log(self) 
        self.CreateStatusBar()
        self.log.message(_("Ready."))
        
        self.Panel = KrigingPanel(self)
        self.SetMinSize(self.GetBestSize())
        self.SetSize(self.GetBestSize())
        
    
class Log:
    """ The log output is redirected to the status bar of the containing frame. """
    def __init__(self, parent):
        self.parent = parent

    def message(self, text_string):
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
            
        #@TODO: deploy this asap!!
        #self.ParametersSizer.Add(wx.Button(self, id=wx.ID_ANY, label=_("Interactive variogram fit")))

        self.VariogramSizer.Add(self.ParametersSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        
        KrigingList = ["Ordinary kriging"]#, "Universal kriging", "Block kriging"] #@FIXME: i18n on the list?
        KrigingRadioBox = wx.RadioBox(self, id=wx.ID_ANY, label=_("Kriging techniques"), 
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            choices=KrigingList, majorDimension=1, style=wx.RA_SPECIFY_COLS)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.VariogramSizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        self.Sizer.Add(KrigingRadioBox,  proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
    
    def ExportMap(self, map, col, name, overwrite):
        robjects.r.writeRAST6(map, vname = name, zcol = col, overwrite = overwrite)

class RBookgstatPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific gstat options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        
        self.VariogramCheckBox = wx.CheckBox(self, id=wx.ID_ANY, label=_("Auto-fit variogram"))
        self.VariogramCheckBox.SetValue(state = True) # check it by default
        for n in ["Sill", "Nugget", "Range"]:
            getattr(self, n+"Ctrl").Enable(False)
        self.VariogramSizer.Insert(2, self.VariogramCheckBox , proportion=0, flag=wx.EXPAND | wx.ALL, border=3)
        self.VariogramCheckBox.Bind(wx.EVT_CHECKBOX, self.HideOptions)
        
        try:
            ModelFactor = robjects.r.vgm().r['long']
            ModelList = robjects.r.levels(ModelFactor[0]) # no other way to let the Python pick it up..
        except AttributeError, e:
            print >> sys.stderr, 'Error: ' + str(e)
            ModelList = []
        
        self.ParametersSizer.Insert(before=0, item=wx.StaticText(self, id= wx.ID_ANY, label = _("Variogram model")))
        self.ModelChoicebox = wx.Choice(self, id=wx.ID_ANY, choices=ModelList)
        self.ModelChoicebox.Enable(False) # by default 
        self.ParametersSizer.Insert(before=1, item= self.ModelChoicebox)
        
        self.SetSizerAndFit(self.Sizer)
    
    def HideOptions(self, event):
        self.ModelChoicebox.Enable(not event.IsChecked())
        for n in ["Sill", "Nugget", "Range"]:
            getattr(self, n+"Ctrl").Enable(not event.IsChecked())
        #@FIXME: was for n in self.ParametersSizer.GetChildren(): n.Enable(False) but doesn't work    
    
    
class RBookgeoRPanel(RBookPanel):
    """ Subclass of RBookPanel, with specific geoR options and kriging functions. """
    def __init__(self, parent, *args, **kwargs):
        RBookPanel.__init__(self, parent, *args, **kwargs)
        #@TODO: change these two lines as soon as geoR f(x)s are integrated.
        for n in self.GetChildren():
            n.Hide()
        self.Sizer.Add(wx.StaticText(self, id= wx.ID_ANY, label = _("Work in progress! No functionality provided.")))
        self.SetSizerAndFit(self.Sizer)
    
    
def main(argv=None):
    #@TODO(anne): check all dependencies and data here.
    # grass - rpy2 - R - one of automap/gstat/geoR
    # a nice splash screen like QGIS does can fit the purpose, with a log message on the bottom and
    # popup windows for missing stuff messages.
    # For the moment, deps are checked when creating the notebook pages for each package, and the
    # data availability when clicking Run button. Quite late.
    if not haveRpy2:
        sys.exit(1)

    #@FIXME: solve this double ifelse. the control should not be done twice.
    if argv is None:
        argv = sys.argv[1:] #stripping first item, the full name of this script
        # wxGUI call.
        app = wx.App()
        k = KrigingModule(parent=None)
        k.Centre()
        k.Show()
        app.MainLoop()
    else:
        print argv
        options, flags = argv
        #CLI
        #@TODO: Work on verbosity. Sometimes it's too verbose (R), sometimes not enough.

        # create output map name, if not specified
        if options['output'] is '':
            try: # to strip mapset name from fullname. Ugh.
                options['input'] = options['input'].split("@")[0]
            except:
                pass
            options['output'] =  options['input'] + '_kriging'
        # check for output map with same name. g.parser can't handle this, afaik.
        if grass.find_file(options['output'], element = 'cell')['fullname']:
            grass.error(_("option: <output>: Raster map already exists."))
            sys.exit()        
        
        #print options
        print flags
        if options['model'] is '':
            try:
                robjects.r.require("automap")
            except ImportError, e:
                grass.fatal(_("R package automap is missing, no variogram autofit available."))
        
        controller = Controller()
        
        controller.Run(input = options['input'],
                       column = options['column'],
                       output = options['output'],
                       overwrite = flags['overwrite'],
                       package = options['package'],
                       model = options['model'],
                       sill = options['sill'],
                       nugget = options['nugget'],
                       range = options['range'],
                       logger = grass)
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.exit(main(argv=grass.parser()))
    else:
        main()
