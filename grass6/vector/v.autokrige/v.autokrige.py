#!/usr/bin/python
#-*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       v.autokrige.py
# AUTHOR(S):	Mathieu Grelier (greliermathieu@gmail.com)
# PURPOSE:	automatic kriging interpolation from vector point data
# REQUIREMENTS:
#   - statistical software : R (http://www.r-project.org/)
#   - R packages :
#       - spgrass6 (http://cran.r-project.org/web/packages/spgrass6/index.html)
#       - automap (http://intamap.geo.uu.nl/~paul/Downloads.html) packages 
#   - optional :
#       - imagemagick : convert program
# COPYRIGHT:	(C) 2009 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#%  description: automatic ordinary kriging interpolation from vector point data with R automap package.
#%  keywords: kriging, automap, R
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of the vector containing values to interpolate (must not contain any null values)
#% required : yes
#%end
#%option
#% key: column
#% type: string
#% description: Attribute column to interpolate (must be numeric)
#% required : yes
#%end
#%option
#% key: nbcell
#% type: integer
#% answer: 100
#% description: number of cell of the created grid. If set, GRASS region is affected
#% required : no
#%end
#%option
#% key: models
#% type: string
#% options: Exp,Sph,Gau,Mat
#% multiple : yes
#% answer: 
#% description: List of variogram models to be automatically tested. Select only one to fix the model
#% required : no
#%end
#%option
#% key: range
#% type: integer
#% description: Range value. Automatically fixed if not set
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
#% key: nmax
#% type: double
#% description: Local kriging. Number of nearest observations that should be used for a kriging prediction (default : all observations are used)
#% required : no
#%end
#%option
#% key: maxdist
#% type: double
#% description: Local kriging. Maximum distance for observations from the prediction location to be included for prediction (default : no limitation)
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
#% description: Don't set region from sites extent. Region would have been previously set in grass
#%end
#%flag
#% key: l
#% description: Log R output to v.autokrige.py.log
#%end

import sys
import os
import re
from subprocess import Popen, call, PIPE
import traceback

##see http://trac.osgeo.org/grass/browser/grass/trunk/lib/python
from grass import core as grass
##only needed to use debugger with Komodo IDE. See http://aspn.activestate.com/ASPN/Downloads/Komodo/RemoteDebugging
#from dbgp.client import brk

class AutoKrige():

    def __init__(self, options, flags):
        ##options
        self.input = options['input']
        self.column = options['column']
        self.nbcell = options['nbcell'] if options['nbcell'].strip() != '' else None
        self.models = options['models'] if options['models'].strip() != '' else None
        self.range = options['range'] if options['range'].strip() != '' else 'NA'
        self.nugget = options['nugget'] if options['nugget'].strip() != '' else 'NA'
        self.sill = options['sill'] if options['sill'].strip() != '' else 'NA'
        self.nmax = options['nmax'] if options['nmax'].strip() != '' else 'Inf'
        self.maxdist = options['maxdist'] if options['maxdist'].strip() != '' else 'Inf'
        self.output = options['output']
        self.colormap = options['colormap'] if options['colormap'].strip() != '' else 'bcyor'
        ##flags
        self.varianceFlag = True if flags['v'] is True else False
        self.regionFlag = False if flags['r'] is True else True
        self.logROutput = True if flags['l'] is True else False
        ##others
        self.RscriptFile = None
        logfilename = 'v.autokrige.py.log'
        self.logfile = os.path.join(os.getenv('LOGDIR'),logfilename) if os.getenv('LOGDIR') else logfilename
        grass.try_remove(self.logfile)

    def __prepareRModelsString(self, models=None):
        """Create the R argument as expected in the R script.
        Used to avoid string manipulations with R."""
        modelsString = ''
        if models is None:
            ##it is important not to have any space between commas and following slashes
            modelsString = 'c(\\"Sph\\",\\"Exp\\",\\"Gau\\",\\"Mat\\")'
        else:
            ##conversion to R arguments in the expected format, starting from model1,model2...
            ##add c(" at the beginning and add ") at the end
            modelsString = 'c(\\"' + models + '\\")'
            ##replace commas by \",\"
            p = re.compile(',')
            modelsString = p.sub('\\",\\"',modelsString)
        return modelsString

    def __writeRScript(self):
        """Create the R script for automap."""
        RscriptFile = grass.tempfile()
        fileHandle = open(RscriptFile, 'a')
        script = """
        options(echo = FALSE)
        args <- commandArgs()
        ##start at index 5 because first arguments are R options
        cat("arguments:","\n")
        sitesG <- args[5]
        column <- args[6]
        rastername <- args[7]
        cellsize <- as.numeric(args[8])
        models <- args[9]
        modelslist <- eval(parse(text = models))
        range <- as.numeric(args[10])
        if(args[11] == "NA") {nugget = NA} else {nugget <- as.numeric(args[11])}
        if(args[12] == "NA") {sill = NA} else {sill <- as.numeric(args[12])}
        if(args[13] == "Inf") {nobsmax = Inf} else {nobsmax <- as.numeric(args[13])}
        if(args[14] == "Inf") {maxdistance = Inf} else {maxdistance <- as.numeric(args[14])}
        writevarrast <- as.logical(args[15])
        ##preparing UK implementation
        predictors <- as.character(args[16])
        
        ##print arguments
        #################
        cat("sitesG:",sitesG,"\n")
        cat("column:",column,"\n")
        cat("rastername:",rastername,"\n")
        cat("cellsize:",cellsize,"\n")
        cat("modelslist:",modelslist,"\n")
        cat("range:",range,"\n")
        cat("nugget:",nugget,"\n")
        cat("sill:",sill,"\n")
        cat("nobsmax:",nobsmax,"\n")
        cat("maxdistance:",maxdistance,"\n")
        cat("writevarrast:",writevarrast,"\n")
        cat("predictors:",predictors,"\n")
        
        ##variogram plot function
        #########################
        plot.autoKrigeVariogramAndFittedModel = function(x, sp.layout = NULL, ...)
        ##Function adapted from plot.autoKrige in automap package.
        ##Prints only the variogram and model as we already have the map output in GRASS.
        {
            library(lattice)
            shift = 0.03
            labels = as.character(x$exp_var$np)
            vario = xyplot(gamma ~ dist, data = x$exp_var, panel = automap:::autokrige.vgm.panel,
                        labels = labels, shift = shift, model = x$var_model,# subscripts = TRUE,
                        direction = c(x$exp_var$dir.hor[1], x$exp_var$dir.ver[1]),
                        ylim = c(min(0, 1.04 * min(x$exp_var$gamma)), 1.04 * max(x$exp_var$gamma)),
                        xlim = c(0, 1.04 * max(x$exp_var$dist)), xlab = "Distance", ylab = "Semi-variance",
                        main = "Experimental variogram and fitted variogram model", mode = "direct",...)
        
            print(vario, position = c(0,0,1,1))
        
        }
        
        ##autokrige script
        ##################
        tryCatch({
            ##libraries
            library(spgrass6)
            library(automap)
        
            ##retrieve sites in a SpatialPointsDataFrame object
            cat("retrieve sites from GRASS","\n")
            sitesR <- readVECT6(sitesG, ignore.stderr = F)
        
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
            kriging_result = autoKrige(as.formula(paste(column,"~",predictors)), sitesR[column], mask_SG, model = modelslist, fix.values = c(nugget,range,sill), debug.level=-1, verbose=TRUE, nmax=nobsmax, maxdist=maxdistance)
            
            cat("send raster to GRASS","\n")
            writeRAST6(kriging_result$krige_output,rastername,zcol=1,NODATA=0)
            cat("Generated",rastername," "); cat("", sep="\n")
            if(writevarrast == T) {
                varrastername = paste(rastername, "_var", sep = "")
                writeRAST6(kriging_result$krige_output,varrastername,zcol=2,NODATA=0)
                cat("Generated",varrastername," "); cat("", sep="\n")
            }
        
            ##plot experimental and model variogram
            cat("plot kriging results","\n")
            ##see R FAQ 7.19. Plotting to png can produce errors if R version < 2.7
            ##we use the pdf driver then we will convert to png
            options(device="pdf")
            try(plot.autoKrigeVariogramAndFittedModel(kriging_result))
            cat("R script done","\n")
            quit(status = 0)
        }, interrupt = function(ex) {
            cat("An interrupt was detected while executing R script.\n")
            cat(conditionMessage(ex), "\n")
            quit(status = 4)
            }, 
            error = function(ex) {
            cat("\n");
            cat("Error while executing R script\n")
            cat(conditionMessage(ex), "\n")
            quit(status = 5)
            }
        ) ## tryCatch()
        
        """
        fileHandle.write(script)
        fileHandle.close()
        return RscriptFile

    def __execRCommand(self, command, logFile = False):
        """R command execution method using Popen in shell mode."""
        if logFile is not False:
            command = command + ' >> ' +  logFile
        ##use redirection on stdout only
        command = command + " 2>&1"
        p = Popen(command, shell = True, stdout = PIPE)
        retcode = p.wait()
        com = p.communicate()
        if retcode == 0:
            return retcode
        else:
            lines = None
            if logFile is not False:
                logHandle = open(logFile,"r")
                lines = logHandle.readlines()
            else:
                r = re.compile('\n')
                lines = r.split(com[0])
            out = lines[-2].strip() + ":" + lines[-1].strip()
            raise AutoKrigeError(out)

    def printMessage(self, message, type = 'info'):
        """Call grass message function corresponding to type."""
        if type == 'error':
            grass.error(message)
        elif type == 'warning':
            grass.warning(message)
        elif type == 'info' and os.getenv('GRASS_VERBOSE') > 0:
            grass.info(message)

    def checkLayers(self, input, output, testVarianceRast = False):
        """Preliminary checks before starting kriging.
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
            if not grass.overwrite() is True:
                raise AutoKrigeError("raster map " + output + " already exists in mapset search path. \n \
Use the --o flag to overwrite.")
            else:
                self.printMessage("raster map " + output + " will be overwritten.", type = 'warning')
        ##Test also variance raster.
        if testVarianceRast is True:
            testVarOutput = grass.find_file(output + '_var', element = 'cell')
            if testVarOutput['fullname'] != '':
                if not grass.overwrite() is True:
                    raise AutoKrigeError("raster map " + output + " already exists in mapset search path. \n \
Use the --o flag to overwrite.")
                else:
                    self.printMessage("raster map " + output + '_var' + " will be overwritten.", type = 'warning')

    def getGridCellSize(self, input, nbcell, adjustRegionToSites = True):
        """Define kriged grid cell size.
        Raster resolution but also computation time depends on it.
        We take region resolution as cell size but we can fix this resolution with the nbcell parameter.
        Only one value is needed because the R script use square cells."""
        if adjustRegionToSites is True:
            grass.run_command("g.region", vect = input)
        if nbcell is not None:
            self.fixRegionResFromNumberOfCells(nbcell)
        regionParams = grass.region()
        cellsize = float(regionParams['nsres']) if float(regionParams['nsres']) > float(regionParams['ewres']) \
        else float(regionParams['ewres'])
        return cellsize

    def fixRegionResFromNumberOfCells(self, nbcell=100):
        """Adjust one of the two region dimensions so that we have a maximum of 'nbcell' cells in both."""
        regionParams = grass.region()
        nsResForGivenNbCell = (float(regionParams['n'])- float(regionParams['s'])) / float(nbcell)
        ewResForGivenNbCell = (float(regionParams['e'])- float(regionParams['w'])) / float(nbcell)
        tmpRegionRes = nsResForGivenNbCell if nsResForGivenNbCell > ewResForGivenNbCell else ewResForGivenNbCell
        grass.use_temp_region
        grass.run_command("g.region", res = tmpRegionRes)

    def finalizeOutput(self):
        """Final operations after successful kriging.
        We don't want to stop execution if an error occurs here.
        """
        try:
            ##convert plot to png
            call('convert -alpha off Rplots.pdf autokrige_result.png', shell = True)
            grass.try_remove('Rplots.pdf')
            ##apply colormap
            grass.run_command("r.colors", map = self.output, rules = self.colormap, quiet = True)
            if self.varianceFlag is True:
                grass.run_command("r.colors", map = self.output + '_var', rules = self.colormap, quiet = True) 
        except:
            pass

    def runAutoKrige(self):
        """Performs kriging process."""
        ##1)Necessary checks
        self.checkLayers(self.input, self.output, self.varianceFlag)
        ##2)Adjust interpolation resolution
        cellsize = self.getGridCellSize(self.input, self.nbcell, self.regionFlag)
        ##3)Execute R from GRASS
        self.RscriptFile = self.__writeRScript()
        ##spgrass6 cause : column name in R has only the 10 first characters of the original column name
        ##may change with future versions of spgrass6
        Rcolumnname = self.column[0:10]
        writeVarRast = 'T' if self.varianceFlag is True else 'F'
        self.printMessage("RGrass is working...", type = 'info')
        #print "RGrass is working..."
        ##ordinary kriging for now
        predictors = '1'
        autoKrigeCommand = 'R --vanilla --slave --args ' + self.input + ' ' + Rcolumnname + ' ' + \
                        self.output + ' ' + str(cellsize) + ' "' + self.__prepareRModelsString(self.models) + '" ' + \
                        self.range + ' ' +  self.nugget + ' ' + self.sill \
                        + ' ' + self.nmax + ' ' + self.maxdist + ' ' \
                        + writeVarRast + ' ' + predictors + ' < "' + self.RscriptFile + '"'
        logFileArg = self.logfile if self.logROutput is True else False
        self.__execRCommand(autoKrigeCommand, logFile=logFileArg)
        ##4)Final steps
        self.finalizeOutput()

class AutoKrigeError(Exception):
    """Errors specific to Autokrige class."""

    def __init__(self, message=''):
        self.details = '\nDetails:\n'
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        self.details += repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        self.message = message + "\n" + self.details

def main():
    exitStatus = 0
    try:
        autoKrige = AutoKrige(options, flags)
        autoKrige.runAutoKrige()
    except AutoKrigeError, e1:
        autoKrige.printMessage(e1.message, type = 'error')
        exitStatus = 1
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        errorMessage = "Unexpected error \n:" + \
                       repr(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback))
        autoKrige.printMessage(errorMessage, type = 'error')
        exitStatus = 1
    else:
        autoKrige.printMessage("Done", type = 'info')
    finally:
        grass.try_remove(autoKrige.RscriptFile)
        sys.exit(exitStatus)

if __name__ == "__main__":
    ### DEBUG : uncomment to start local debugging session
    #brk(host="localhost", port=9000)
    if grass.find_program('R'):
        options, flags = grass.parser()
        main()
    else:
        print "R required, please install R first"


