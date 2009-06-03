#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v.autokrige.py
# AUTHOR(S):	Mathieu Grelier (greliermathieu@gmail.com)
# PURPOSE:	automatic kriging interpolation from vector point data
# REQUIREMENTS:
# - unix utility : bc
# - statistical software : R (http://www.r-project.org/) with spgrass6 (http://cran.r-project.org/web/packages/spgrass6/index.html)
#	and automap (http://intamap.geo.uu.nl/~paul/Downloads.html) packages 
# - imagemagick : convert program
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#%  description: automatic kriging interpolation from vector point data
#%  keywords: kriging, autokrige, RGrass
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of the vector containing sites data (values to interpolate) and geometry. Must not contain any null values.
#% required : yes
#%end
#%option
#% key: column
#% type: string
#% description: Attribute column to interpolate (must be numeric).
#% required : yes
#%end
#%option
#% key: nbcell
#% type: integer
#% answer: 100
#% description: number of cell of the created grid. If set, GRASS region is affected.
#% required : no
#%end
#%option
#% key: models
#% type: string
#% options: Exp,Sph,Gau,Mat
#% multiple : yes
#% answer: 
#% description: List of variogram models to be automatically tested. Select only one to fix the model.
#% required : no
#%end
#%option
#% key: range
#% type: integer
#% description: Range value. Automatically fixed if not set.
#% required : no
#%end
#%option
#% key: nugget
#% type: double
#% description: Nugget value. Automatically fixed if not set
#% required : no
#%end
#%option
#% key: sill
#% type: double
#% description: Sill value. Automatically fixed if not set
#% required : no
#%end
#%option
#% key: output
#% type: string
#% answer: autokrige
#% description: Name of the raster to produce
#% required : yes
#%end
#%option
#% key: colormap
#% type: string
#% answer: bcyor
#% description: Colormap file to use to colorize the raster
#% required : no
#%end
#%flag
#% key: v
#% description: Create variance raster also 
#%end
#%flag
#% key: r
#% description: Don't set region from sites extent. Region would have been previously set in grass. 
#%end

import sys
import os
import re
from subprocess import Popen, PIPE
import traceback

from grass import core as grass
from dbgp.client import brk

class AutoKrige():
    
    def __init__(self, options, flags):
        ##options
        self.input = options['input']
        self.column = options['column']
        self.nbcell = options['nbcell'] if options['nbcell'].strip() != '' else None
        self.models = options['models'] if options['models'].strip() != '' else None
        self.range = options['range'] if options['range'].strip() != '' else None
        self.nugget = options['nugget'] if options['nugget'].strip() != '' else None
        self.sill = options['sill'] if options['sill'].strip() != '' else None
        self.output = options['output']
        self.colormap = options['colormap'] if options['colormap'].strip() != '' else 'bcyor'
        ##flags
        self.varianceFlag = True if flags['v'] is True else False
        self.regionFlag = True if flags['r'] is True else False
        #others
        self.RscriptFile = None
        self.logfile='v.autokrige.log'
    
    def __checkLayers(self, input, output):
        """
        Preliminary chacks before starting kriging.
        Note : for this to work with grass6.3, in find_file function from core.py,
        command should be (n flag removed because 6.4 specific):
        s = read_command("g.findfile", element = element, file = name, mapset = mapset)
        """
        ##Test for input vector map.
        testInput = grass.find_file(input, element = 'vector')
        if testInput['fullname'] == '':
            raise AutoKrigeError("vector map " + input + " not found in mapset search path.")
        ##Test if output raster map already exists.
        testOutput = grass.find_file(output, element = 'cell')
        if testOutput['fullname'] != '':
            if not grass.overwrite is True:
                raise AutoKrigeError("raster map " + output + " already exists in mapset search path. \n \
Use the --o flag to overwrite.")
            else:
                print "Warning: raster map " + output + " will be overwritten."
        ##Test also variance raster.
        if self.varianceFlag is True:
            testVarOutput = grass.find_file(output + '_var', element = 'cell')
            if testVarOutput['fullname'] != '':
                if not grass.overwrite is True:
                    raise AutoKrigeError("raster map " + output + " already exists in mapset search path. \n \
Use the --o flag to overwrite.")
                else:
                    print "Warning: raster map " + output + '_var' + " will be overwritten."
        
    
    def __getGridCellSize(self, input, nbcell):
        """Define kriged grid cell size : we take region resolution as cell size.
        Only one value is needed because the R script use square cells."""
        if self.regionFlag is not True:
            grass.run_command("g.region", vect = input)
        if nbcell is not None:
            self.__fixRegionResFromNumberOfCells(nbcell)
        regionParams = grass.region()
        cellsize = float(regionParams['nsres']) if float(regionParams['nsres']) > float(regionParams['ewres']) \
        else float(regionParams['ewres'])
        return cellsize
    
    def __fixRegionResFromNumberOfCells(self, nbcell=100):
        """to explain"""
        regionParams = grass.region()
        nsResForGivenNbCell = (float(regionParams['n'])- float(regionParams['s'])) / float(nbcell)
        ewResForGivenNbCell = (float(regionParams['e'])- float(regionParams['w'])) / float(nbcell)
        tmpRegionRes = nsResForGivenNbCell if nsResForGivenNbCell > ewResForGivenNbCell else ewResForGivenNbCell
        grass.use_temp_region
        grass.run_command("g.region", res = tmpRegionRes)
    
    def __prepareRScriptArguments(self, cellsize, models=None, range=None, nugget=None, sill=None):
        ##1)Models
        ##The script will try to create the R argument as expected in the R script,
        ##to avoid string manipulations with R.
        RargumentsDict = {}
        if models is None:
            #it is important not to have any space between commas and following slashes
            RargumentsDict['models']='c(\"Sph\",\"Exp\",\"Gau\",\"Mat\")'
        else:
            #conversion to R arguments in the expected format, starting from model1,model2...
            #add c(" at the beginning and add ") at the end
            RargumentsDict['models'] = 'c(\\"' + models + '\\")'
            #replace commas by \",\"
            p = re.compile(',')
            RargumentsDict['models'] = p.sub('\\",\\"',RargumentsDict['models'])
        ##2)Range, nugget, sill
        RargumentsDict['range'] = range if range is not None else 'NA'
        RargumentsDict['nugget'] = nugget if nugget is not None else 'NA'
        RargumentsDict['sill'] = sill if sill is not None else 'NA'
        return RargumentsDict

    
    def __writeRScript(self):
        RscriptFile = grass.tempfile()
        fileHandle = open(RscriptFile, 'a')
        script = """
        options(echo = FALSE)
        args <- commandArgs()
        ##start at index 5 because first arguments are R options
        sitesG <- args[5]
        column <- args[6]
        rastername <- args[7]
        cellsize <- as.numeric(args[8])
        models <- args[9]
        modelslist <- eval(parse(text = models))
        range <- as.numeric(args[10])
        if(args[10] == "NA") {nugget = NA} else {nugget <- as.numeric(args[11])}
        if(args[12] == "NA") {sill = NA} else {sill <- as.numeric(args[12])}
        writevarrast <- as.logical(args[13])
        
        tryCatch({
            ##libraries
            library(spgrass6)
            library(automap)
        
            ##retrieve sites in a SpatialPointsDataFrame object
            cat("retrieve sites from GRASS","\n")
            sitesR <- readVECT6(sitesG, ignore.stderr = F)
            ##uncomment to check sites
            #sitesR
        
            cat("retrieve metadata","\n")
            G <- gmeta6()
            cat("GridTopology creation","\n")
            grd <- gmeta2grd()
            ##this is necessary to ensure that we have square cells
            ##the more this number is small, the more the kriged map resolution is high 
            slot(grd, "cellsize") <- c(cellsize, cellsize)
        
            ##creation of another grid object: SpatialGridDataFrame
            ##this is a matrix whose values receive spatial coordinates associated to interpolated values
            ##matrix size must be equal to the number of GridTopology cells 
            ##we create first a classical data.frame
            data <- data.frame(list(k=rep(1,(floor(G$cols)*floor(G$rows)))))
            cat("SpatialGridDataFrame creation","\n")
            mask_SG <- SpatialGridDataFrame(grd, data=data, CRS(G$proj4))
        
            ##add coordinates system
            attr(sitesR, "proj4string") <-CRS(G$proj4)
        
            cat("ordinary kriging","\n")
            #[note : rajouter une option pour gérer le krigeage universel]
            kriging_result = autoKrige(as.formula(paste(column,"~",1)), sitesR[column], mask_SG, model = modelslist, fix.values = c(nugget,range,sill), debug.level=-1, verbose=TRUE)
        
            cat("send raster to GRASS","\n")
            writeRAST6(kriging_result$krige_output,rastername,zcol=1,NODATA=0)
            cat("Generated",rastername," "); cat("", sep="\n")
            if(writevarrast == T) {
                varrastername = paste(rastername, "_var", sep = "")
                writeRASTt6(kriging_result$krige_output,varrastername,zcol=2,NODATA=0)
                cat("Generated",varrastername," "); cat("", sep="\n")
            }
        
            ##plot experimental and model variogram
            cat("plot kriging results","\n")
            options(device="pdf")
            try(automap:::plot.autoKrige(kriging_result))
            cat("R script done","\n")
            quit(status = 0)
        }, interrupt = function(ex) {
            cat("An interrupt was detected.\n");
            quit(status = 4)
            }, 
            error = function(ex) {
            cat("Error while executing R script.\n");
            quit(status = 5)
            }
        )
        """
        fileHandle.write(script)
        fileHandle.close()
        return RscriptFile
    
    def __finalize(self, output, colormap):
        try:
            ##convert plot to png
            self.__execShellCommand('convert -alpha off Rplots.pdf Rplots.png')
            ##apply colormap
            grass.run_command("r.colors", map = output, rules = colormap, quiet = True) 
        except:
            ##we don't want to stop execution if an error occurs here
            pass
    
    def __execShellCommand(self, command, stderrRedirection=False, writeToLog=False):
        """general purpose function, maybe should be added in some way to core.py """
        if stderrRedirection is True:
            command = command + " 2>&1"
        p = Popen(command, shell=True, stdout=PIPE)
        retcode = p.wait()
        com = p.communicate()
        if writeToLog is True:
            fileHandle = open(self.logfile, 'w')
            fileHandle.write(com[0])
            fileHandle.close()
        if retcode == 0:
            return com[0]
        else:
            errorMessage = ''
            for elem in com:
                errorMessage += str(elem) + "\n"
            raise AutoKrigeError(errorMessage)
            
                                       
    def runAutoKrige(self):
        """Autokrige class public method"""
        ##1)Necessary checks
        self.__checkLayers(self.input, self.output)
        ##2)Adjust interpolation resolution
        cellsize = self.__getGridCellSize(self.input, self.nbcell)
        ##3)Put all R arguments in a dict
        RargsDict = self.__prepareRScriptArguments(cellsize, self.models, self.range, \
                                                                 self.nugget, self.sill)
        ##4)Execute R from GRASS
        self.RscriptFile = self.__writeRScript()
        ##spgrass6 cause : column name in R has only the 10 first characters of the original column name
        Rcolumnname = self.column[0:9]
        writeVarRast = 'T' if self.varianceFlag is True else 'F'
        print "RGrass is working..."
        autoKrigeCommand = 'R --vanilla --slave --args ' + self.input + ' ' + Rcolumnname + ' ' + \
                        self.output + ' ' + str(cellsize) + ' "' + RargsDict['models'] + '" ' + \
                        RargsDict['range'] + ' ' +  RargsDict['nugget'] + ' ' + RargsDict['sill'] \
                        + ' ' + writeVarRast + ' < "' + self.RscriptFile + '"'
        self.__execShellCommand(autoKrigeCommand, stderrRedirection=True, writeToLog=True)
        ##5)Finalize output
        self.__finalize(self.output, self.colormap)
                                                                                  
class AutoKrigeError(Exception):
    """Errors specific to Autokrige class"""
    def __init__(self, message):
        self.details = '\nDetails:\n'
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        self.details += repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        self.message = message + "\n" + self.details

def main():
    try:
        autoKrige = AutoKrige(options, flags)
        autoKrige.runAutoKrige()
    except AutoKrigeError, e1:
        print >> sys.stderr, "Error:", e1.message
    except:
        print >> sys.stderr, "Unexpected error:"
        traceback.print_exc()
    else:
        print "Done"
        sys.exit(0)
    finally:
        grass.try_remove(autoKrige.RscriptFile)

if __name__ == "__main__":
    ### DEBUG : uncomment to start local debugging session
    #brk(host="localhost", port=9000)
    if grass.find_program('R'):
        options, flags = grass.parser()
        main()
    else:
        print "R required, please install R first"

