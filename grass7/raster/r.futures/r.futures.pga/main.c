
/****************************************************************************
 *
 * MODULE:       r.futures.pga
 * AUTHOR(S):    Ross K. Meentemeyer
 *               Wenwu Tang
 *               Monica A. Dorning
 *               John B. Vogler
 *               Nik J. Cunniffe
 *               Douglas A. Shoemaker
 *               Jennifer A. Koch
 *               Vaclav Petras <wenzeslaus gmail com>
 *               Anna Petrasova
 *               (See the manual page for details and references.)
 *
 * PURPOSE:      Simulation of urban-rural landscape structure (FUTURES model)
 *
 * COPYRIGHT:    (C) 2013-2016 by Anna Petrasova and Meentemeyer et al.
 *
 *               This program is free software: you can redistribute it and/or
 *               modify it under the terms of the GNU General Public License
 *               as published by the Free Software Foundation, either version 3
 *               of the License, or (at your option) any later version.
 *
 *               This program is distributed in the hope that it will be useful,
 *               but WITHOUT ANY WARRANTY; without even the implied warranty of
 *               MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *               GNU General Public License for more details.
 *
 *               You should have received a copy of the GNU General Public
 *               License along with this program. If not, see
 *               <http://www.gnu.org/licenses/> or read the file COPYING that
 *               comes with GRASS GIS for details.
 *
 *****************************************************************************/

/**
    \file main.c

    The main file containing both the model code and the data handing part.

    A lot of parts of the code are dead code. May be useful as an alternative
    algorithms. Some of the dead code is commented out and might need to
    be revived if other parts will show as useful.

    The language of the code is subject to change. The goal is to use either
    C or C++, not both mixed as it is now.

    Major refactoring of the code is expected.
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#include "keyvalue.h"

//#include "distance.h"

/** used to flag cells that are off the lattice */
#define _CELL_OUT_OF_RANGE -2

/** used to flag cells that are not in this county */
#define _CELL_OUT_OF_COUNTY -1

/** used to flag cells that are valid */
#define _CELL_VALID 1

/** need to dynamically allocate this as putting all on stack will crash most compilers */
#define _N_MAX_DYNAMIC_BUFF_LEN (1024*1024)
#define _N_MAX_FILENAME_LEN 1024

/** Max length of input line */
#define N_MAXREADINLEN 8192

/** for working out where to start reading data */
#define _GIS_HEADER_LENGTH 6

/** strictly-speaking, should probably parse these from GIS files */
#define _GIS_NO_DATA_STRING "-9999"

/** Value used to represent NULL (NoData) in some parts of the model */
#define _GIS_NO_DATA_INT -9999

/** use this for tDeveloped if cell still undeveloped */
#define _N_NOT_YET_DEVELOPED -1

/* algorithm to use */

/** deterministic model */
#define _N_ALGORITHM_DETERMINISTIC 1

/** stochastic model with downweighting of logit probabilities and of devPressure over time */
#define _N_ALGORITHM_STOCHASTIC_I 2
#define _N_ALGORITHM_STOCHASTIC_II 3

#define _MAX_RAND_FIND_SEED_FACTOR 25
#define maxNumAddVariables 20

/** maximal number of counties allowed */
#define MAXNUM_COUNTY 200
#define MAX_YEARS 100
/// maximum array size for undev cells (maximum: 1840198 for a county within 16 counties)
#define MAX_UNDEV_SIZE 2000000


/* Wenwu Tang */
/// use absolute paths
char dirName[100];

/// string for temporarily storage
char tempStr[100];



typedef struct
{

    /** see #define's starting _CELL_ above */
    int nCellType;

    /** x position on the lattice; static */
    int thisX;

    /** y position on the lattice; static */
    int thisY;

    /** whether this site is still undeveloped; varies.  Note if bUndeveloped = 0 the values of employAttraction etc. are not to be trusted */
    int bUndeveloped;
    // TODO: is the following int or double (defined as double but usually casting to int in assignment, was as int in some print)

    /** development pressure; varies */
    double devPressure;

    /** stores whether this site has been considered for development, to handle "protection" */
    int bUntouched;

    /** timestep on which developed (0 for developed at start, _N_NOT_YET_DEVELOPED for not developed yet ) */
    int tDeveloped;

    /** additional variables, see t_Landscape.predictors */
    double *additionVariable;
    int index_region;
} t_Cell;

typedef struct
{

    /** id of this cell */
    int cellID;

    /** value of the logit */
    double logitVal;

    /** whether or not cell previously considered...need to use this in the sort */
    int bUntouched;

    /** to support random pick based on their logitVal */
    double cumulProb;
} t_Undev;

typedef struct
{

    /** array of cells (see posFromXY for how they are indexed) */
    t_Cell *asCells;

    /** number of columns in the grid */
    int maxX;

    /** number of rows in the grid */
    int maxY;

    /** total number of cells */
    int totalCells;

    /** array of information on undeveloped cells */
    t_Undev *asUndev;

    /** number of cells which have not yet converted */
    int undevSites;

    /** posterior sample from parcel size distribution */
    int *aParcelSizes;

    /** number in that sample */
    int parcelSizes;
    //  std::vector < std::vector < t_Undev > >asUndevs;  //WT
    t_Undev **asUndevs;
    size_t asUndevs_m;
    size_t *asUndevs_ns;
    int num_undevSites[MAXNUM_COUNTY];  //WT

    /** array of predictor variables ordered as p1,p2,p3,p1,p2,p3 */
    double *predictors;
    /** multiplicative factor on the probabilities */
    double *consWeight;
} t_Landscape;


typedef struct
{

    /** size of the grids */
    int xSize;

    /** size of the grids */
    int ySize;

    /** files containing the information to read in */
    char *developedFile;
    char *devPressureFile;
    char *consWeightFile;
    char *probLookupFile;
    int nProbLookup;
    double *adProbLookup;
    // parameters provided in other ways
    //      /* parameters that go into regression formula */
    //      double          dIntercept;                                                                             /* 0.038884 */
    //      double          dEmployAttraction;                                                              /* -0.0000091946 */
    //      double          dInterchangeDistance;                                                   /* 0.000042021 */
    //      double          dRoadDensity;                                                                   /* 0.00065813 */
    //      double          dDevPressure;                                                                   /* -0.026190 */
    /* size of square used to recalculate development pressure */

    int nDevNeighbourhood;  /** 8 (i.e. 8 in each direction, leading to 17 x 17 = 289 in total) */

    /** used in writing rasters */
    char *dumpFile;
    char *outputSeries;

    /** 1 deterministic, 2 old stochastic, 3 new stochastic */
    int nAlgorithm;

    /** file containing parcel size information */
    char *parcelSizeFile;
    double discountFactor;      ///< for calibrate patch size

    /** these parameters only relevant for new stochastic algorithm */
    int sortProbs;
    double patchMean;
    double patchRange;
    /// 4 or 8 neighbors only
    int numNeighbors;
    /// 1: uniform distribution 2: based on dev. proba.
    int seedSearch;
    int numAddVariables;

    /** parameters for additional variables */
    double addParameters[maxNumAddVariables][MAXNUM_COUNTY];
    char *addVariableFile[maxNumAddVariables];
    /// 1: #occurrence; 2: gravity (need to define alpha and scaling factor); 3: kernel, need to define alpha and scaling factor
    ///
    /// for 2: formula-> scalingFactor/power(dist,alpha)
    /// for 3: formula-> scalingFactor*exp(-2*dist/alpha)
    int devPressureApproach;
    /// scale distance-based force
    double scalingFactor;
    ///< constraint on distance
    double alpha;

    /** parameters that go into regression formula */
    double dIntercepts[MAXNUM_COUNTY];
    double dV4[MAXNUM_COUNTY];
    int num_Regions;

    /** index file to run multiple regions */
    char *indexFile;

    /// control files for all regions
    /// development demand for multiple regions
    char *controlFileAll;
    int devDemand[MAX_YEARS];
    int devDemands[MAXNUM_COUNTY][MAX_YEARS];
    /// This keeps the number of cells in demand which we satisfied
    /// in one step but it was more than we should have satisfied.
    /// To corrent for this, we keep it to the next step and we use
    /// it to lower the current demand.
    int overflowDevDemands[MAXNUM_COUNTY];
    /// number of simulation steps
    int nSteps;
    struct KeyValueIntInt *region_map;
} t_Params;


//From WT: move here to be global variables
t_Params sParams;
t_Landscape sLandscape;

int getUnDevIndex(t_Landscape * pLandscape);
void Shuffle4(int *mat);
double getDistance1(double x1, double y1, double x2, double y2);
void readDevPotParams(t_Params * pParams, char *fn);
void readIndexData(t_Landscape * pLandscape, t_Params * pParams);
void findAndSortProbsAll(t_Landscape * pLandscape, t_Params * pParams,
                         int step);
void updateMap1(t_Landscape * pLandscape, t_Params * pParams, int step,
                int regionID);
int getUnDevIndex1(t_Landscape * pLandscape, int regionID);


void readDevPotParams(t_Params * pParams, char *fn)
{
    FILE *fp;
    if ((fp = fopen(fn, "r")) == NULL)
        G_fatal_error(_("Cannot open development potential parameters file <%s>"),
                      fn);

    const char *fs = "\t";
    const char *td = "\"";

    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Development potential parameters file <%s>"
                        " contains less than one line"), fn);

    char **tokens;
    int ntokens;

    while (G_getl2(buf, buflen, fp)) {
        tokens = G_tokenize2(buf, fs, td);
        ntokens = G_number_of_tokens(tokens);

        int idx;
        int id;
        double di, d4;
        double val;
        int j;

        G_chop(tokens[0]);
        id = atoi(tokens[0]);

        if (KeyValueIntInt_find(pParams->region_map, id, &idx)) {
            G_chop(tokens[1]);
            di = atof(tokens[1]);
            G_chop(tokens[2]);
            d4 = atof(tokens[2]);
            pParams->dIntercepts[idx] = di;
            pParams->dV4[idx] = d4;
            for (j = 0; j < pParams->numAddVariables; j++) {
                G_chop(tokens[j + 3]);
                val = atof(tokens[j + 3]);
                pParams->addParameters[j][idx] = val;
            }
        }
        // else ignoring the line with region which is not used

        G_free_tokens(tokens);
    }

    fclose(fp);
}

/**
    Generate uniform number on [0,1).

    Encapsulated to allow easy replacement if necessary.
*/
double uniformRandom()
{
    int nRet;

    nRet = RAND_MAX;
    while (nRet == RAND_MAX) {  /* make sure never get 1.0 */
        nRet = rand();
    }
    return ((double)nRet / (double)(RAND_MAX));
}

/**
    Seed random number generator.

    Encapsulated to allow easy replacement if necessary.
*/
void seedRandom(struct timeval ttime)
{
    srand((ttime.tv_sec * 100) + (ttime.tv_usec / 100));
    //srand((unsigned int)time(NULL));
}


/**
    Work out x and y position on the grid from index into siteMapping/landscape array.
*/
void xyFromPos(int nPos, int *pnX, int *pnY, t_Landscape * pLandscape)
{
    /* integer division just gives whole number part */
    *pnX = nPos % pLandscape->maxX;
    *pnY = nPos / pLandscape->maxX;
}

/**
    Work out index into asCells array from location.
*/
int posFromXY(int nX, int nY, t_Landscape * pLandscape)
{
    int nPos;

    /*
       0   1         2              .... nX-1
       nX  nX+1 nX+2   .... 2*nX-1
       .                                            .
       .                                            .
       .                                            .
       (nY-1)*nX            ...  nX*nY-1
     */
    nPos = _CELL_OUT_OF_RANGE;
    if (nX >= 0 && nX < pLandscape->maxX && nY >= 0 && nY < pLandscape->maxY) {
        nPos = nX * pLandscape->maxY + nY;
    }
    return nPos;
}

/**
    Allocate memory to store information on cells.
*/
int buildLandscape(t_Landscape * pLandscape, t_Params * pParams)
{
    int bRet;

    /* blank everything out */
    G_verbose_message("Initialization and memory allocation...");
    bRet = 0;

    pLandscape->asCells = NULL;
    pLandscape->asUndev = NULL;
    pLandscape->undevSites = 0;
    pLandscape->aParcelSizes = NULL;
    pLandscape->parcelSizes = 0;

    /* set initial values across the landscape */

    pLandscape->maxX = pParams->xSize;
    pLandscape->maxY = pParams->ySize;
    pLandscape->totalCells = pLandscape->maxX * pLandscape->maxY;

    pLandscape->asCells =
        (t_Cell *) malloc(sizeof(t_Cell) * pLandscape->totalCells);
    if (pLandscape->asCells) {
        /* just allocate enough space for every cell to be undev */
        pLandscape->asUndev = (t_Undev *) malloc(sizeof(t_Undev) * pLandscape->totalCells);
        if (pLandscape->asUndev) {
            bRet = 1;
        }
        else
            bRet = 1;
    }
    return bRet;
}

void readData4AdditionalVariables(t_Landscape * pLandscape,
                                  t_Params * pParams)
{
    int i;
    int ii;
    double val;

    pLandscape->predictors = (double *)G_malloc(pParams->numAddVariables * pLandscape->totalCells * sizeof(double));
    for (i = 0; i < pParams->numAddVariables; i++) {
        G_verbose_message("Reading predictor variables %s...", pParams->addVariableFile[i]);

        /* open raster map */
        int fd = Rast_open_old(pParams->addVariableFile[i], "");
        RASTER_MAP_TYPE data_type = Rast_get_map_type(fd);
        void *buffer = Rast_allocate_buf(data_type);

        ii = 0;
        for (int row = 0; row < pParams->xSize; row++) {
            Rast_get_row(fd, buffer, row, data_type);
            void *ptr = buffer;

            for (int col = 0; col < pParams->ySize; col++,
                 ptr = G_incr_void_ptr(ptr, Rast_cell_size(data_type))) {
                if (data_type == DCELL_TYPE)
                    val = *(DCELL *) ptr;
                else if (data_type == FCELL_TYPE)
                    val = *(FCELL *) ptr;
                else {
                    val = *(CELL *) ptr;
                }
                if (Rast_is_null_value(ptr, data_type)) {
                    pLandscape->asCells[ii].nCellType =
                        _CELL_OUT_OF_COUNTY;
                }
                if (i == 0)
                    pLandscape->asCells[ii].additionVariable = &pLandscape->predictors[pParams->numAddVariables * ii];
                if (pLandscape->asCells[ii].nCellType == _CELL_VALID)
                    pLandscape->asCells[ii].additionVariable[i] = val;
                else
                    pLandscape->asCells[ii].additionVariable[i] = 0.0;
                ii++;
            }
        }
        Rast_close(fd);
        G_verbose_message("Done");
    }
}

void readIndexData(t_Landscape * pLandscape, t_Params * pParams)
{
    int ii;
    int val;

    ii = 0;
    int fd = Rast_open_old(pParams->indexFile, "");

    /* TODO: data type should always be CELL */
    RASTER_MAP_TYPE data_type = Rast_get_map_type(fd);
    void *buffer = Rast_allocate_buf(data_type);

    G_verbose_message("Reading subregions %s", pParams->indexFile);
    int count_regions = 0;
    int index = 0;
    for (int row = 0; row < pParams->xSize; row++) {
        Rast_get_row(fd, buffer, row, data_type);
        void *ptr = buffer;

        for (int col = 0; col < pParams->ySize; col++,
             ptr = G_incr_void_ptr(ptr, Rast_cell_size(data_type))) {
            if (Rast_is_null_value(ptr, data_type))
                index = _GIS_NO_DATA_INT; // assign FUTURES representation of NULL value
            else {
                val = *(CELL *) ptr;
                if (KeyValueIntInt_find(pParams->region_map, val, &index))
                    ; // pass
                else {
                    KeyValueIntInt_set(pParams->region_map, val, count_regions);
                    index = count_regions;
                    count_regions++;
                }
            }

            pLandscape->asCells[ii].index_region = index;
            ii++;
        }
    }
    pParams->num_Regions = count_regions;
    G_verbose_message("Done");
}

/**
    Read data from GIS rasters and put in correct places in memory.
*/
int readData(t_Landscape * pLandscape, t_Params * pParams)
{
    // TODO: this function should be rewritten to be nicer (unless storing in memorey will change completely)
    // TODO: fix null handling somewhere
    char *szBuff;
    char szFName[_N_MAX_FILENAME_LEN];
    int bRet, x, y, i, j;
    double dVal;

    G_verbose_message("Reading input rasters...");
    bRet = 0;
    szBuff = (char *)malloc(_N_MAX_DYNAMIC_BUFF_LEN * sizeof(char));
    if (szBuff) {
        for (j = 0; j < 3; j++) {
            /* workaround to skip loading constraint map so that it can be omitted in input */
            if (j == 2) {
                pLandscape->consWeight = NULL;
                if (pParams->consWeightFile)
                    pLandscape->consWeight = (double *)G_malloc(pLandscape->totalCells * sizeof(double));
                else
                    continue;
            }
            switch (j) {        /* get correct filename */
            case 0:
                strcpy(szFName, pParams->developedFile);
                break;
            case 1:
                strcpy(szFName, pParams->devPressureFile);
                break;
            case 2:
                strcpy(szFName, pParams->consWeightFile);
                break;
            default:
                G_fatal_error("readData(): shouldn't get here");
                break;
            }
            G_verbose_message("%s...", szFName);
            /* open raster map */
            int fd = Rast_open_old(szFName, "");

            i = 0;

            x = 0;
            bRet = 1;  /* can only get worse from here on in */
            RASTER_MAP_TYPE data_type = Rast_get_map_type(fd);
            void *buffer = Rast_allocate_buf(data_type);

            for (int row = 0; row < pParams->xSize; row++) {
                y = 0;
                Rast_get_row(fd, buffer, row, data_type);
                void *ptr = buffer;

                for (int col = 0; col < pParams->ySize; col++,
                     ptr = G_incr_void_ptr(ptr, Rast_cell_size(data_type))) {
                    CELL iVal;

                    if (data_type == DCELL_TYPE)
                        dVal = *(DCELL *) ptr;
                    else if (data_type == FCELL_TYPE)
                        dVal = *(FCELL *) ptr;
                    else {
                        iVal = *(CELL *) ptr;  // integer value for some rasters
                        dVal = iVal;
                    }
                    if (j == 0) {
                        /* check for NO_DATA */
                        if (Rast_is_null_value(ptr, data_type)) {
                            pLandscape->asCells[i].nCellType =
                                _CELL_OUT_OF_COUNTY;
                        }
                        else {
                            pLandscape->asCells[i].nCellType = _CELL_VALID;
                        }
                        /* and put in the correct place */
                        pLandscape->asCells[i].thisX = x;
                        pLandscape->asCells[i].thisY = y;
                        /* and set the time of development */
                        pLandscape->asCells[i].tDeveloped = _GIS_NO_DATA_INT;
                    }
                    else {
                        /* clean up missing data */
                        if (Rast_is_null_value(ptr, data_type)) {
                            dVal = 0.0;
                        }
                    }
                    // TODO: how do we know that this is set?
                    if (pLandscape->asCells[i].nCellType == _CELL_VALID) {
                        /* put data into a correct place */
                        switch (j) {
                        case 0:
                            pLandscape->asCells[i].bUndeveloped = (iVal == 0) ? 1 : 0;
                            pLandscape->asCells[i].bUntouched = 1;
                            if (pLandscape->asCells[i].bUndeveloped == 1) {
                                pLandscape->asCells[i].tDeveloped =
                                    _N_NOT_YET_DEVELOPED;
                            }
                            else {
                                /* already developed at the start */
                                pLandscape->asCells[i].tDeveloped = 0;
                            }
                            break;
                        case 1:
                            pLandscape->asCells[i].devPressure = (int)dVal;
                            break;
                        case 2:
                            if (pLandscape->consWeight) {
                                pLandscape->consWeight[i] = dVal;
                            }
                            break;
                        default:
                            G_fatal_error("readData(): shouldn't get here");
                            break;
                        }
                    }
                    y++;
                    i++;
                }

                x++;
            }
            if (x == pLandscape->maxX) {

            }
            else {
                if (bRet) {
                    G_warning("readData(): x too small");
                    bRet = 0;
                }
            }

            if (y != pLandscape->maxY) {
                if (bRet) {
                    G_message(_("x=%d y=%d"), x, y);
                    G_message(_(" xSize=%d ySize=%d"), pParams->xSize,
                              pParams->ySize);
                    G_message(_(" maxX=%d minX=%d"), pLandscape->maxX,
                              pLandscape->maxY);
                    G_warning("readData(): y too small");
                    bRet = 0;
                }
            }
            else {
                if (bRet && i == pLandscape->totalCells) {
                    G_verbose_message("Done");
                }
                else {

                    if (bRet) {
                        G_message(_("x=%d y=%d"), x, y);
                        G_message(_(" xSize=%d ySize=%d"), pParams->xSize,
                                  pParams->ySize);
                        G_message(_(" maxX=%d minX=%d"), pLandscape->maxX,
                                  pLandscape->maxY);
                        G_warning("readData(): not read in enough points");
                        bRet = 0;
                    }

                }
            }
            Rast_close(fd);

        }
        free(szBuff);
    }

    return bRet;
}


/**
    Compare two t_Undev structures.

    To be used in qsort().

    \note This sort function is in ascending order
    (i.e. opposite to what we normally want).

    \see undevCmpReverse()
*/
static int undevCmp(const void *a, const void *b)
{
    double da = ((t_Undev *) a)->logitVal;
    double db = ((t_Undev *) b)->logitVal;

    /* make sure untouched cells preferentially go to top of sort when there is asymmetry between a and b */
    if (((t_Undev *) a)->bUntouched && !((t_Undev *) b)->bUntouched)
        return -1;
    if (((t_Undev *) b)->bUntouched && !((t_Undev *) a)->bUntouched)
        return 1;
    /* then sort by value */
    if (da > db)
        return 1;
    if (da < db)
        return -1;
    return 0;
}

/**
    Compare two t_Undev structures.

    This is the correct way around sorting with undevCmp() and qsort().
 */
static int undevCmpReverse(const void *a, const void *b)
{
    return -1 * undevCmp(a, b);
}


/**
    Write current state of developed areas.

    Called at end and dumps tDeveloped for all valid cells (NULL for all others)

    \param undevelopedAsNull Represent undeveloped areas as NULLs instead of -1
    \param developmentAsOne Represent all developed areas as 1 instead of number
        representing the step when are was developed
 */
// TODO: add timestamp to maps
void outputDevRasterStep(t_Landscape * pLandscape, t_Params * pParams,
                         const char *rasterNameBase, bool undevelopedAsNull,
                         bool developmentAsOne)
{
    int out_fd = Rast_open_new(rasterNameBase, CELL_TYPE);
    CELL *out_row = Rast_allocate_c_buf();

    for (int x = 0; x < pLandscape->maxX; x++) {
        Rast_set_c_null_value(out_row, pLandscape->maxY);
        for (int y = 0; y < pLandscape->maxY; y++) {
            // we don't check return values since we use landscape directly
            int cellId = posFromXY(x, y, pLandscape);

            // this handles NULLs on input
            if (pLandscape->asCells[cellId].nCellType == _CELL_VALID) {
                CELL value = pLandscape->asCells[cellId].tDeveloped;

                // this handles undeveloped cells
                if (undevelopedAsNull && value == -1)
                    continue;
                // this handles developed cells
                if (developmentAsOne)
                    value = 1;
                out_row[y] = value;
            }
        }
        Rast_put_c_row(out_fd, out_row);
    }
    Rast_close(out_fd);

    struct Colors colors;

    Rast_init_colors(&colors);
    CELL val1 = 0;
    // TODO: the map max is 36 for 36 steps, it is correct?
    CELL val2 = pParams->nSteps;

    if (developmentAsOne) {
        val1 = 1;
        val2 = 1;
        Rast_add_c_color_rule(&val1, 255, 100, 50, &val2, 255, 100, 50,
                              &colors);
    }
    else {
        Rast_add_c_color_rule(&val1, 255, 100, 50, &val2, 255, 255, 0,
                              &colors);
    }
    if (!undevelopedAsNull) {
        val1 = -1;
        val2 = -1;
        Rast_add_c_color_rule(&val1, 100, 255, 100, &val2, 100, 255, 100,
                              &colors);
    }

    const char *mapset = G_find_file2("cell", rasterNameBase, "");

    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), rasterNameBase);

    Rast_write_colors(rasterNameBase, mapset, &colors);
    Rast_free_colors(&colors);

    struct History hist;

    Rast_short_history(rasterNameBase, "raster", &hist);
    Rast_command_history(&hist);
    // TODO: store also random seed value (need to get it here, global? in Params?)
    Rast_write_history(rasterNameBase, &hist);

    G_message(_("Raster map <%s> created"), rasterNameBase);
}

char *mapNameForStep(const char *basename, const int step, const int maxSteps)
{
    int digits = log10(maxSteps) + 1;

    return G_generate_basename(basename, step, digits, 0);
}

/**
    Work out how many cells to transition based on the control file.
*/
int parseControlLine(char *szBuff, char *szStepLabel, int *pnToConvert)
{
    char *pPtr;
    int i;
    int bRet;

    bRet = 0;
    /* strip newline */
    pPtr = strpbrk(szBuff, "\r\n");
    if (pPtr) {
        pPtr[0] = '\0';
    }
    *pnToConvert = 0;
    i = 0;
    pPtr = strtok(szBuff, " \t");
    while (pPtr && i < 2) {
        switch (i) {
        case 0:
            strcpy(szStepLabel, pPtr);
            break;
        case 1:
            *pnToConvert = atoi(pPtr);
            break;
        }
        pPtr = strtok(NULL, " \t");
        i++;
    }
    /* only process this line of the control file if it is well formed */
    if (i == 2) {
        bRet = 1;
    }
    return bRet;
}

/**
    Calculate probability of development.
*/

double getDevProbability(t_Cell * pThis, t_Params * pParams)
{
    double probAdd;
    int i;
    int id = pThis->index_region;

    if (id == -9999)
        return 0;
    probAdd = pParams->dIntercepts[id];
    //cout<<"intercept\t"<<probAdd<<endl;
    probAdd += pParams->dV4[id] * pThis->devPressure;
    //cout<<"devPressure: "<<pParams->dV4[id]<<endl;
    //cout<<"devPressure: "<<pThis->devPressure<<endl;
    //cout<<"devPressure: "<<pParams->dV4[id] * pThis->devPressure<<endl;
    for (i = 0; i < pParams->numAddVariables; i++) {
        probAdd += pParams->addParameters[i][id] * pThis->additionVariable[i];
        //cout<<"additionVariable: "<<i<<"\t"<<pParams->addParameters[i][id]<<endl;
        //cout<<"additionVariable: "<<i<<"\t"<<pThis->additionVariable[i]<<endl;
        //cout<<"additionVariable: "<<i<<"\t"<<pParams->addParameters[i][id] * pThis->additionVariable[i]<<endl;
    }
    probAdd = 1.0 / (1.0 + exp(-probAdd));
    //cout<<"The probability:";
    //cout<<probAdd<<endl;
    return probAdd;
}

/*
   double getDevProbability(t_Cell      *pThis, t_Params *pParams){
   float probAdd; int i;
   int id=pThis->index_region;
   if(id==-9999)
   return 0;
   id=id-1;
   probAdd = pParams->dIntercepts[id];
   probAdd += pParams->dV1[id] * pThis->employAttraction;
   probAdd += pParams->dV2[id] * pThis->interchangeDistance;
   probAdd += pParams->dV3[id] * pThis->roadDensity;
   probAdd += pParams->dV4[id] * pThis->devPressure;
   for(i=0;i<2;i++){
   probAdd+=pParams->addParameters[i][id]*pThis->additionVariable[i];
   }
   if (0<pThis->additionVariable[2]<=400)
   {
   probAdd = probAdd * 0.0005 ;
   }
   else { 
   if(400<pThis->additionVariable[2]<=600)
   {probAdd = probAdd * 0.024;}
   else {
   if(600<pThis->additionVariable[2]<=800)
   {probAdd = probAdd * 0.912 ;}
   else{
   if(800<pThis->additionVariable[2]<=1000)
   {probAdd = probAdd * 0.055 ;}
   else{
   if(1000<pThis->additionVariable[2]<=1200)
   {probAdd = probAdd * 0.006 ;}
   else{
   if(1200<pThis->additionVariable[2]<=1400)
   {probAdd = probAdd * 0.002 ;}
   else{

   {probAdd = probAdd * 0.0005;}

   }
   }
   }

   }

   }


   }


   probAdd = 1.0/(1.0 + exp(-probAdd));
   return probAdd;
   }

 */


/**
    Recalculate probabilities for each unconverted cell.

    Called each timestep.
*/
void findAndSortProbs(t_Landscape * pLandscape, t_Params * pParams,
                      int nToConvert)
{
    int i, lookupPos;
    t_Cell *pThis;

    /* update calcs */
    G_verbose_message("Recalculating probabilities...");
    pLandscape->undevSites = 0;
    for (i = 0; i < pLandscape->totalCells; i++) {
        pThis = &(pLandscape->asCells[i]);
        if (pThis->nCellType == _CELL_VALID) {
            if (pThis->bUndeveloped) {
                double consWeight = pLandscape->consWeight ? pLandscape->consWeight[i] : 1;
                if (consWeight > 0.0) {
                    /* note that are no longer just storing the logit value, but instead the probability (allows consWeight to affect sort order) */
                    pLandscape->asUndev[pLandscape->undevSites].cellID = i;
                    pLandscape->asUndev[pLandscape->undevSites].logitVal =
                        getDevProbability(pThis, pParams);
                    /* lookup table of probabilities is applied before consWeight */
                    if (pParams->nAlgorithm == _N_ALGORITHM_STOCHASTIC_II) {
                        /* replace with value from lookup table */
                        lookupPos =
                            (int)(pLandscape->asUndev[pLandscape->undevSites].
                                  logitVal * (pParams->nProbLookup - 1));
                        pLandscape->asUndev[pLandscape->undevSites].logitVal =
                            pParams->adProbLookup[lookupPos];
                        // fprintf(stdout, "%f %d %f\n", pLandscape->asUndev[pLandscape->undevSites].logitVal, lookupPos, pParams->adProbLookup[lookupPos]);
                    }
                    // multiply consweight
                    pLandscape->asUndev[pLandscape->undevSites].logitVal *= consWeight;
                    pLandscape->asUndev[pLandscape->undevSites].bUntouched = pThis->bUntouched; /* need to store this to put correct elements near top of list */
                    if (pLandscape->asUndev[pLandscape->undevSites].logitVal >
                        0.0) {
                        /* only add one more to the list if have a positive probability */
                        pLandscape->undevSites++;
                    }
                }
            }
        }
    }
    /* sort */
    /* can only be zero for algorithm=stochastic_ii */
    if (pParams->sortProbs) {
        G_verbose_message("Sorting %d unconserved undeveloped sites",
                pLandscape->undevSites);
        qsort(pLandscape->asUndev, pLandscape->undevSites, sizeof(t_Undev),
              undevCmpReverse);
    }
    else {
        G_verbose_message("Skipping sort as choosing cells randomly");
    }
    //calculate cumulative probability
    // From Wenwu Tang
    double sum = pLandscape->asUndev[0].logitVal;

    for (i = 1; i < pLandscape->undevSites; i++) {
        pLandscape->asUndev[i].cumulProb =
            pLandscape->asUndev[i - 1].cumulProb +
            pLandscape->asUndev[i].logitVal;
        sum = sum + pLandscape->asUndev[i].logitVal;
    }
    for (i = 0; i < pLandscape->undevSites; i++) {
        pLandscape->asUndev[i].cumulProb =
            pLandscape->asUndev[i].cumulProb / sum;
    }
}


/**
   Helper structur for neighbour grabbing algorithm
 */
typedef struct
{
    double probAdd;
    int cellID;
    int newInList;
    // Wenwu Tang
    /// distance to the center
    double distance;
} t_candidateNeighbour;

/**
    Helper structur for neighbour grabbing algorithm
*/
typedef struct
{
    double maxProb;
    int nCandidates;
    int nSpace;
    t_candidateNeighbour *aCandidates;
} t_neighbourList;

#define _N_NEIGHBOUR_LIST_BLOCK_SIZE 20

int addNeighbourIfPoss(int x, int y, t_Landscape * pLandscape,
                       t_neighbourList * pNeighbours, t_Params * pParams)
{
    int i, thisPos, mustAdd, listChanged, lookupPos;
    double probAdd;
    t_Cell *pThis;

    listChanged = 0;
    thisPos = posFromXY(x, y, pLandscape);
    if (thisPos != _CELL_OUT_OF_RANGE) {
        pThis = &(pLandscape->asCells[thisPos]);
        if (pThis->nCellType == _CELL_VALID) {
            pThis->bUntouched = 0;
            if (pThis->bUndeveloped) {
                double consWeight = pLandscape->consWeight ? pLandscape->consWeight[thisPos] : 1;
                if (consWeight > 0.0) {
                    /* need to add this cell... */

                    /* ...either refresh its element in list if already there */
                    mustAdd = 1;
                    for (i = 0; mustAdd && i < pNeighbours->nCandidates; i++) {
                        if (pNeighbours->aCandidates[i].cellID == thisPos) {
                            pNeighbours->aCandidates[i].newInList = 1;
                            mustAdd = 0;
                            listChanged = 1;
                        }
                    }
                    /* or add it on the end, allocating space if necessary */
                    if (mustAdd) {
                        if (pNeighbours->nCandidates == pNeighbours->nSpace) {
                            pNeighbours->nSpace +=
                                _N_NEIGHBOUR_LIST_BLOCK_SIZE;
                            pNeighbours->aCandidates =
                                (t_candidateNeighbour *)
                                realloc(pNeighbours->aCandidates,
                                        pNeighbours->nSpace *
                                        sizeof(t_candidateNeighbour));
                            if (!pNeighbours->aCandidates) {
                                G_fatal_error("Memory error in addNeighbourIfPoss()");
                            }
                        }
                        pNeighbours->aCandidates[pNeighbours->nCandidates].
                            cellID = thisPos;
                        pNeighbours->aCandidates[pNeighbours->nCandidates].
                            newInList = 1;

                        /* note duplication of effort in here recalculating the probabilities, but didn't store them in an accessible way */
                        /*
                           probAdd = pParams->dIntercept;
                           probAdd += pParams->dDevPressure * pThis->devPressure;
                           probAdd += pParams->dEmployAttraction * pThis->employAttraction;
                           probAdd += pParams->dInterchangeDistance * pThis->interchangeDistance;
                           probAdd += pParams->dRoadDensity * pThis->roadDensity;
                           probAdd = 1.0/(1.0 + exp(probAdd));
                         */
                        probAdd = getDevProbability(pThis, pParams);
                        /* replace with value from lookup table */
                        lookupPos =
                            (int)(probAdd * (pParams->nProbLookup - 1));
                        probAdd = pParams->adProbLookup[lookupPos];
                        probAdd *= consWeight;
                        pNeighbours->aCandidates[pNeighbours->nCandidates].
                            probAdd = probAdd;
                        /* only actually add it if will ever transition */
                        if (probAdd > 0.0) {
                            pNeighbours->nCandidates++;
                            if (probAdd > pNeighbours->maxProb) {
                                pNeighbours->maxProb = probAdd;
                            }
                            listChanged = 1;
                        }
                    }
                }
            }
        }
    }
    return listChanged;
}

// From Wenwu

/**
    Sort according to the new flag and conversion probability.
*/
static int sortNeighbours(const void *pOne, const void *pTwo)
{
    t_candidateNeighbour *pNOne = (t_candidateNeighbour *) pOne;
    t_candidateNeighbour *pNTwo = (t_candidateNeighbour *) pTwo;

    /*
       if(pNOne->newInList > pNTwo->newInList)
       {
       return -1;
       }
       if(pNTwo->newInList > pNOne->newInList)
       {
       return 1;
       }
     */
    float p = rand() / (float)RAND_MAX;

    /*
       if(p<0.0){
       if(pNOne->distance> pNTwo->distance)
       {
       return 1;
       }
       if(pNTwo->distance > pNOne->distance)
       {
       return -1;
       }
       }
     */
    float alpha = 0.5;          // assign this from parameter file

    alpha = (sParams.patchMean) - (sParams.patchRange) * 0.5;
    alpha += p * sParams.patchRange;
    //alpha=0;
    float p1, p2;

    p1 = pNOne->probAdd / pow(pNOne->distance, alpha);
    p2 = pNTwo->probAdd / pow(pNTwo->distance, alpha);

    //p1=alpha*pNOne->probAdd+(1-alpha)*pow(pNOne->distance,-2);
    //p2=alpha*pNTwo->probAdd+(1-alpha)*pow(pNTwo->distance,-2);

    if (p1 > p2) {
        return -1;
    }
    if (p2 > p1) {
        return 1;
    }
    return 0;
}

/**
    randomly shuffle the 4 neighbors
*/
void Shuffle4(int *mat)
{
    int proba[4], flag[4];
    int size = 4, i;

    for (i = 0; i < size; i++) {
        proba[i] = rand() % 1000;
        flag[i] = 1;
    }

    int numChecked = 0;
    int max;
    int index = 0;

    while (numChecked != 4) {
        max = -9999;
        for (i = 0; i < size; i++) {
            if (flag[i] != 0) {
                if (proba[i] > max) {
                    max = proba[i];
                    index = i;
                }
            }
        }
        flag[index] = 0;
        mat[numChecked] = index;
        numChecked++;
    }
}

void findNeighbours(int nThisID, t_Landscape * pLandscape,
                    t_neighbourList * pNeighbours, t_Params * pParams)
{
    t_Cell *pThis;
    int listChanged = 0;

    // int     idmat[4]; idmat[0]=0;idmat[1]=1;idmat[2]=2;idmat[3]=3;
    /* try to add the neighbours of this one */
    pThis = &(pLandscape->asCells[nThisID]);
    //note: if sorted, then shuffle is no need
    /*
       Shuffle4(&idmat[0]);
       for(i=0;i<4;i++){
       if(idmat[i]==0)
       listChanged+=addNeighbourIfPoss(pThis->thisX-1,pThis->thisY,pLandscape,pNeighbours,pParams);
       else if(idmat[i]==1)
       listChanged+=addNeighbourIfPoss(pThis->thisX+1,pThis->thisY,pLandscape,pNeighbours,pParams);
       else if(idmat[i]==2)
       listChanged+=addNeighbourIfPoss(pThis->thisX,pThis->thisY-1,pLandscape,pNeighbours,pParams);
       else if (idmat[i]==3)
       listChanged+=addNeighbourIfPoss(pThis->thisX,pThis->thisY+1,pLandscape,pNeighbours,pParams);
       }
     */

    listChanged += addNeighbourIfPoss(pThis->thisX - 1, pThis->thisY, pLandscape, pNeighbours, pParams);  // left
    listChanged += addNeighbourIfPoss(pThis->thisX + 1, pThis->thisY, pLandscape, pNeighbours, pParams);  // right
    listChanged += addNeighbourIfPoss(pThis->thisX, pThis->thisY - 1, pLandscape, pNeighbours, pParams);  // down
    listChanged += addNeighbourIfPoss(pThis->thisX, pThis->thisY + 1, pLandscape, pNeighbours, pParams);  // up 
    if (sParams.numNeighbors == 8) {
        listChanged +=
            addNeighbourIfPoss(pThis->thisX - 1, pThis->thisY - 1, pLandscape,
                               pNeighbours, pParams);
        listChanged +=
            addNeighbourIfPoss(pThis->thisX - 1, pThis->thisY + 1, pLandscape,
                               pNeighbours, pParams);
        listChanged +=
            addNeighbourIfPoss(pThis->thisX + 1, pThis->thisY - 1, pLandscape,
                               pNeighbours, pParams);
        listChanged +=
            addNeighbourIfPoss(pThis->thisX + 1, pThis->thisY + 1, pLandscape,
                               pNeighbours, pParams);
    }
    /* if anything has been altered then resort */

    if (listChanged) {
        //qsort(pNeighbours->aCandidates,pNeighbours->nCandidates,sizeof(t_candidateNeighbour),sortNeighbours);
    }
}

double getDistance(int id1, int id2, t_Landscape * pLandscape)
{
    double x1, x2, y1, y2, result = 0;

    x1 = pLandscape->asCells[id1].thisX;
    x2 = pLandscape->asCells[id2].thisX;
    y1 = pLandscape->asCells[id1].thisY;
    y2 = pLandscape->asCells[id2].thisY;
    result = sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2));
    return result;
}

double getDistance1(double x1, double y1, double x2, double y2)
{
    double result = 0;

    result = sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2));
    return result;
}

int newPatchFinder(int nThisID, t_Landscape * pLandscape, t_Params * pParams,
                   int *anToConvert, int nWantToConvert)
{
    int bTrying, i, nFound, j;
    t_neighbourList sNeighbours;

    memset(&sNeighbours, 0, sizeof(t_neighbourList));
    anToConvert[0] = nThisID;
    pLandscape->asCells[nThisID].bUntouched = 0;
    pLandscape->asCells[nThisID].bUndeveloped = 0;
    nFound = 1;
    findNeighbours(nThisID, pLandscape, &sNeighbours, pParams);
    for (i = 0; i < sNeighbours.nCandidates; i++) {
        sNeighbours.aCandidates[i].distance =
            getDistance(nThisID, sNeighbours.aCandidates[i].cellID,
                        pLandscape);
    }

    while (nFound < nWantToConvert && sNeighbours.nCandidates > 0) {
        i = 0;
        bTrying = 1;
        while (bTrying) {
            if (uniformRandom() < sNeighbours.aCandidates[i].probAdd) {
                anToConvert[nFound] = sNeighbours.aCandidates[i].cellID;
                /* flag that it is about to develop */
                pLandscape->asCells[anToConvert[nFound]].bUndeveloped = 0;
                /* remove this one from the list by copying down everything above it */
                for (j = i + 1; j < sNeighbours.nCandidates; j++) {
                    sNeighbours.aCandidates[j - 1].cellID =
                        sNeighbours.aCandidates[j].cellID;
                    sNeighbours.aCandidates[j - 1].newInList =
                        sNeighbours.aCandidates[j].newInList;
                    sNeighbours.aCandidates[j - 1].probAdd =
                        sNeighbours.aCandidates[j].probAdd;
                }
                /* reduce the size of the list */
                sNeighbours.nCandidates--;
                sNeighbours.maxProb = 0.0;
                for (j = 0; j < sNeighbours.nCandidates; j++) {
                    if (sNeighbours.aCandidates[j].probAdd >
                        sNeighbours.maxProb) {
                        sNeighbours.maxProb =
                            sNeighbours.aCandidates[j].probAdd;
                    }
                }
                /* add its neighbours */
                findNeighbours(anToConvert[nFound], pLandscape, &sNeighbours,
                               pParams);
                nFound++;
                bTrying = 0;
            }
            else {
                sNeighbours.aCandidates[i].newInList = 0;
            }
            if (bTrying) {
                i++;
                if (i == sNeighbours.nCandidates) {
                    i = 0;
                }
            }
            else {
                /* always resort the list if have just added, to let new elements bubble to the top */
                if (sNeighbours.nCandidates > 0) {
                    //                                      int z;
                    for (i = 0; i < sNeighbours.nCandidates; i++) {
                        sNeighbours.aCandidates[i].distance =
                            getDistance(nThisID,
                                        sNeighbours.aCandidates[i].cellID,
                                        pLandscape);
                    }

                    qsort(sNeighbours.aCandidates, sNeighbours.nCandidates,
                          sizeof(t_candidateNeighbour), sortNeighbours);
#if 0
                    for (z = 0; z < sNeighbours.nCandidates; z++) {
                        fprintf(stdout, "%d %d %f\n", z,
                                sNeighbours.aCandidates[z].newInList,
                                sNeighbours.aCandidates[z].probAdd);
                    }
                    fprintf(stdout, "***\n");
#endif
                }
            }
        }
    }
    if (sNeighbours.nSpace) {   /* free any allocated memory */
        free(sNeighbours.aCandidates);
    }
    //      fprintf(stdout, "looking for %d found %d\n", nWantToConvert,nFound);
    return nFound;
}

int convertCells(t_Landscape * pLandscape, t_Params * pParams, int nThisID,
                 int nStep, int bAllowTouched, int bDeterministic)
{
    int i, x, y, nCell, nDone, nToConvert, nWantToConvert;
    int *anToConvert;
    t_Cell *pThis, *pThat;

    nDone = 0;
    /* in here need to build list of near neigbours to loop over */
    nWantToConvert = pLandscape->aParcelSizes[(int)
                                              (uniformRandom() *
                                               pLandscape->parcelSizes)];
    anToConvert = (int *)malloc(sizeof(int) * nWantToConvert);
    if (anToConvert) {
        /* in here goes code to fill up list of neighbours */
        nToConvert =
            newPatchFinder(nThisID, pLandscape, pParams, anToConvert,
                           nWantToConvert);
        /* will actually always be the case */
        if (nToConvert > 0) {
            //                      fprintf(stdout, "wanted %d, found %d\n", nWantToConvert, nToConvert);
            for (i = 0; i < nToConvert; i++) {
                /* convert, updating dev press on neighbours */
                pThis = &(pLandscape->asCells[anToConvert[i]]);
                pThis->bUndeveloped = 0;
                pThis->bUntouched = 0;
                pThis->tDeveloped = nStep + 1;
                nDone++;
                // fprintf(stdout, "%d total=%f dev=%f employment=%f interchange=%f roads=%f\n", pLandscape->asUndev[i].cellID, pLandscape->asUndev[i].logitVal, pParams->dDevPressure * pThis->devPressure, pParams->dEmployAttraction * pThis->employAttraction, pParams->dInterchangeDistance * pThis->interchangeDistance, pParams->dRoadDensity * pThis->roadDensity);
                float dist = 0;
                float force = 0;

                for (x = pThis->thisX - pParams->nDevNeighbourhood;
                     x <= pThis->thisX + pParams->nDevNeighbourhood; x++) {
                    for (y = pThis->thisY - pParams->nDevNeighbourhood;
                         y <= pThis->thisY + pParams->nDevNeighbourhood;
                         y++) {
                        nCell = posFromXY(x, y, pLandscape);
                        if (nCell != _CELL_OUT_OF_RANGE) {
                            pThat = &(pLandscape->asCells[nCell]);
                            dist =
                                getDistance1(pThis->thisX, pThis->thisY, x,
                                             y);
                            if (dist > pParams->nDevNeighbourhood)
                                continue;
                            force = 0;
                            if (pParams->devPressureApproach == 1)
                                force = 1;      // development pressure increases by 1
                            else if (pParams->devPressureApproach == 2) {
                                if (dist > 0)
                                    force =
                                        pParams->scalingFactor / pow(dist,
                                                                     pParams->
                                                                     alpha);
                            }
                            else {
                                force =
                                    pParams->scalingFactor * exp(-2 * dist /
                                                                 pParams->
                                                                 alpha);
                            }
                            pThat->devPressure = pThat->devPressure + force;
                        }
                    }
                }
            }
        }
        free(anToConvert);
    }
    return nDone;
}


void readDevDemand(t_Params * pParams)
{
    FILE *fp;
    if ((fp = fopen(pParams->controlFileAll, "r")) == NULL)
        G_fatal_error(_("Cannot open population demand file <%s>"),
                      pParams->controlFileAll);

    size_t buflen = 4000;
    char buf[buflen];
    if (G_getl2(buf, buflen, fp) == 0)
        G_fatal_error(_("Population demand file <%s>"
                        " contains less than one line"), pParams->controlFileAll);

    char **tokens;
    int ntokens;

    const char *fs = "\t";
    const char *td = "\"";

    tokens = G_tokenize2(buf, fs, td);
    ntokens = G_number_of_tokens(tokens);
    if (ntokens == 0)
        G_fatal_error("No columns in the header row");

    struct ilist *ids = G_new_ilist();
    int count;
    // skip first column which does not contain id of the region
    for (int i = 1; i < ntokens; i++) {
            G_chop(tokens[i]);
            G_ilist_add(ids, atoi(tokens[i]));
    }

    int years = 0;
    while(G_getl2(buf, buflen, fp)) {
        tokens = G_tokenize2(buf, fs, td);
        ntokens = G_number_of_tokens(tokens);
        // skip empty lines
        if (ntokens == 0)
            continue;
        count = 0;
        for (int i = 1; i < ntokens; i++) {
            // skip first column which is the year which we ignore
            int idx;
            if (KeyValueIntInt_find(pParams->region_map, ids->value[count], &idx)) {
                G_chop(tokens[i]);
                pParams->devDemands[idx][years] = atoi(tokens[i]);
            }
            count++;
        }
        // each line is a year
        years++;
    }
    G_verbose_message("Number of steps in demand file: %d", years);
    if (!sParams.nSteps)
        sParams.nSteps = years;
    G_free_ilist(ids);
    G_free_tokens(tokens);
}

void initializeUnDev(t_Landscape * pLandscape, t_Params * pParams)
{
    int i;

    pLandscape->asUndevs = (t_Undev **) G_malloc(pParams->num_Regions * sizeof(t_Undev *));
    pLandscape->asUndevs_m = pParams->num_Regions;
    pLandscape->asUndevs_ns = (size_t *) G_malloc(pParams->num_Regions * sizeof(t_Undev *));

    for (i = 0; i < pParams->num_Regions; i++) {
        pLandscape->asUndevs[i] = (t_Undev *) G_malloc(MAX_UNDEV_SIZE * sizeof(t_Undev));
        pLandscape->asUndevs_ns[i] = MAX_UNDEV_SIZE;
        pLandscape->num_undevSites[i] = 0;
    }
}

void finalizeUnDev(t_Landscape * pLandscape, t_Params * pParams)
{
    int i;

    for (i = 0; i < pParams->num_Regions; i++) {
        G_free(pLandscape->asUndevs[i]);
    }
    G_free(pLandscape->asUndevs);
    G_free(pLandscape->asUndevs_ns);
}

/*
   main routine to run models on multiple regions // WTang
 */
void updateMapAll(t_Landscape * pLandscape, t_Params * pParams)
{
    //readDevDemand(pParams);
    int i, j;

    //initialize undev arrays
    initializeUnDev(pLandscape, pParams);

    //iterate each step (year)
    for (i = 0; i < pParams->nSteps; i++) {
        G_verbose_message("Processing step %d from %d", i + 1, pParams->nSteps);
        // for each sub-region, find and update conversion probability (conservation weight applied)
        findAndSortProbsAll(pLandscape, pParams, i);
        for (j = 0; j < pParams->num_Regions; j++)
            //j=1;
            updateMap1(pLandscape, pParams, i, j);
        if (pParams->outputSeries)
            outputDevRasterStep(pLandscape, pParams,
                                mapNameForStep(pParams->outputSeries, i,
                                               pParams->nSteps), true, true);
    }
    outputDevRasterStep(pLandscape, pParams, pParams->dumpFile, false, false);
    finalizeUnDev(pLandscape, pParams);
}

void updateMap1(t_Landscape * pLandscape, t_Params * pParams, int step,
                int regionID)
{
    int i, nToConvert, nStep, nDone, bAllowTouched, nRandTries, nExtra;
    double dProb;
    t_Cell *pThis;

    // get number of demanded cells already satisfied in the previous step
    nExtra = pParams->overflowDevDemands[regionID];

    nStep = step;

    //fprintf(stdout, "entered updateMap()\n");
    nToConvert = pParams->devDemands[regionID][step];
    //fprintf(stdout, "\tdoing step %s...controlFile requests conversion of %d cells\n", szStepLabel, nToConvert);
    if (nExtra > 0) {
        if (nToConvert - nExtra > 0) {
            nToConvert -= nExtra;
            nExtra = 0;
        }
        else {
            nExtra -= nToConvert;
            nToConvert = 0;
        }
    }
    G_debug(1, "After accounting for extra cells, attempt %d cells", nToConvert);
    /* if have cells to convert this step */
    if (nToConvert > 0) {
        //findAndSortProbs(pLandscape, pParams, nToConvert);
        /* if not enough cells to convert then alter number required */
        if (nToConvert > pLandscape->num_undevSites[regionID]) {
            G_warning("Not enough undeveloped sites... converting all");
            nToConvert = pLandscape->num_undevSites[regionID];
        }
        /* update either in deterministic or stochastic fashion */
        //fprintf(stdout, "\t\tupdating map\n");
        switch (pParams->nAlgorithm) {
        case _N_ALGORITHM_DETERMINISTIC:       /* deterministic */
            nDone = 0;
            for (i = 0; i < nToConvert && nDone < nToConvert; i++) {
                nDone +=
                    convertCells(pLandscape, pParams,
                                 pLandscape->asUndev[i].cellID, nStep, 1, 1);
            }
            break;
        case _N_ALGORITHM_STOCHASTIC_II:       /* stochastic */
            nDone = 0;
            i = 0;
            nRandTries = 0;
            bAllowTouched = 0;
            /* loop until done enough cells...might need multiple passes */
            while (nDone < nToConvert) {
                if (i == pLandscape->num_undevSites[regionID]) {
                    /* if at the end of the grid, just loop around again until done */
                    i = 0;
                    /* allow previously considered cells if you have to */
                    bAllowTouched = 1;
                }
                /* if tried too many randomly in this step, give up on idea of only letting untouched cells convert */
                if (nRandTries > _MAX_RAND_FIND_SEED_FACTOR * nToConvert) {
                    bAllowTouched = 1;
                }
                if (pParams->sortProbs) {
                    /* if sorted then choose the top cell and do nothing */
                }
                else {
                    /* otherwise give a random undeveloped cell a go */
                    if (sParams.seedSearch == 1)
                        i = (int)(uniformRandom() *
                                  pLandscape->num_undevSites[regionID]);
                    //pick one according to their probability
                    else
                        G_debug(3, "nDone=%d, toConvert=%d", nDone,
                                          nToConvert);
                    i = getUnDevIndex1(pLandscape, regionID);
                }
                pThis =
                    &(pLandscape->asCells
                      [pLandscape->asUndevs[regionID][i].cellID]);

                /* need to check is still undeveloped */
                if (pThis->bUndeveloped) {
                    if (bAllowTouched || pThis->bUntouched) {
                        /* Doug's "back to front" logit */
                        //  dProb = 1.0/(1.0 + exp(pLandscape->asUndev[i].logitVal));
                        dProb = pLandscape->asUndevs[regionID][i].logitVal;
                        if (uniformRandom() < dProb) {
                            nDone +=
                                convertCells(pLandscape, pParams,
                                             pLandscape->asUndevs[regionID]
                                             [i].cellID, nStep, bAllowTouched,
                                             0);
                        }
                    }
                    pThis->bUntouched = 0;
                }
                if (pParams->sortProbs) {
                    i++;
                }
                else {
                    nRandTries++;
                }
            }
            break;
        default:
            G_fatal_error("Unknown algorithm...exiting");
            break;
        }
        G_debug(1, "Converted %d sites", nDone);
        nExtra += (nDone - nToConvert);
        // save overflow for the next time
        pParams->overflowDevDemands[regionID] = nExtra;
        G_debug(1, "%d extra sites knocked off next timestep", nExtra);
    }
}


/**
    Check Doug's calculation of devPressure.

    No longer called.
 */
void testDevPressure(t_Landscape * pLandscape, t_Params * pParams)
{
    int x, y, xN, yN, cellID, nCell, testPressure;

    for (y = 0; y < pLandscape->maxY; y++) {
        for (x = 0; x < pLandscape->maxX; x++) {
            cellID = posFromXY(x, y, pLandscape);
            if (cellID != _CELL_OUT_OF_RANGE) { /* should never happen */
                if (pLandscape->asCells[cellID].nCellType == _CELL_VALID) {
                    if (pLandscape->asCells[cellID].bUndeveloped) {
                        if (pLandscape->asCells[cellID].devPressure) {
                            fprintf(stdout,
                                    "(x,y)=(%d,%d) cellType=%d bUndev=%d devPress=%f\n",
                                    x, y,
                                    pLandscape->asCells[cellID].nCellType,
                                    pLandscape->asCells[cellID].bUndeveloped,
                                    pLandscape->asCells[cellID].devPressure);
                            testPressure = 0;
                            for (xN = x - pParams->nDevNeighbourhood;
                                 xN <= x + pParams->nDevNeighbourhood; xN++) {
                                for (yN = y - pParams->nDevNeighbourhood;
                                     yN <= y + pParams->nDevNeighbourhood;
                                     yN++) {
                                    nCell = posFromXY(xN, yN, pLandscape);
                                    if (nCell != _CELL_OUT_OF_RANGE) {
                                        if (pLandscape->asCells[nCell].
                                            nCellType == _CELL_VALID) {
                                            if (pLandscape->asCells[nCell].
                                                bUndeveloped == 0) {
                                                testPressure++;
                                            }
                                        }
                                    }
                                }
                            }
                            fprintf(stdout, "\t%d\n", testPressure);
                        }
                    }
                }
            }
        }
    }
}

int readParcelSizes(t_Landscape * pLandscape, t_Params * pParams)
{
    FILE *fIn;
    char *szBuff;
    int nMaxParcels;


    pLandscape->parcelSizes = 0;

    G_verbose_message("Reading patch sizes...");
    fIn = fopen(pParams->parcelSizeFile, "rb");
    if (fIn) {
        szBuff = (char *)malloc(_N_MAX_DYNAMIC_BUFF_LEN * sizeof(char));
        if (szBuff) {
            /* just scan the file twice */
            nMaxParcels = 0;
            while (fgets(szBuff, _N_MAX_DYNAMIC_BUFF_LEN, fIn)) {
                nMaxParcels++;
            }
            rewind(fIn);
            if (nMaxParcels) {
                pLandscape->aParcelSizes =
                    (int *)malloc(sizeof(int) * nMaxParcels);
                if (pLandscape->aParcelSizes) {
                    while (fgets(szBuff, _N_MAX_DYNAMIC_BUFF_LEN, fIn)) {
                        pLandscape->aParcelSizes[pLandscape->parcelSizes] =
                            atoi(szBuff) * pParams->discountFactor;
                        if (pLandscape->aParcelSizes[pLandscape->parcelSizes]) {
                            pLandscape->parcelSizes++;
                        }
                    }
                }
            }
            free(szBuff);
        }
        fclose(fIn);
    }
    return pLandscape->parcelSizes;
}

int main(int argc, char **argv)
{

    struct
    {
        struct Option
            *developedFile, *devPressureFile,
            *consWeightFile, *addVariableFiles, *nDevNeighbourhood,
            *devpotParamsFile, *dumpFile, *outputSeries,
            *parcelSizeFile, *discountFactor,
            *probLookupFile,
            *patchMean, *patchRange, *numNeighbors, *seedSearch,
            *devPressureApproach, *alpha, *scalingFactor, *num_Regions,
            *numSteps, *indexFile, *controlFileAll, *seed;

    } opt;

    struct
    {
        struct Flag *generateSeed;
    } flg;


    G_gisinit(argv[0]);

    struct GModule *module = G_define_module();

    G_add_keyword(_("raster"));
    G_add_keyword(_("patch growing"));
    G_add_keyword(_("urban"));
    G_add_keyword(_("landscape"));
    G_add_keyword(_("modeling"));
    module->label =
        _("Simulates landuse change using FUTure Urban-Regional Environment Simulation (FUTURES).");
    module->description =
        _("Module uses Patch-Growing Algorithm (PGA) to"
          " simulate urban-rural landscape structure development.");

    opt.developedFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.developedFile->key = "developed";
    opt.developedFile->required = YES;
    opt.developedFile->description =
        _("Raster map of developed areas (=1), undeveloped (=0) and excluded (no data)");
    opt.developedFile->guisection = _("Basic input");

    opt.addVariableFiles = G_define_standard_option(G_OPT_R_INPUTS);
    opt.addVariableFiles->key = "predictors";
    opt.addVariableFiles->required = YES;
    opt.addVariableFiles->multiple = YES;
    opt.addVariableFiles->label = _("Names of predictor variable raster maps");
    opt.addVariableFiles->description = _("Listed in the same order as in the development potential table");
    opt.addVariableFiles->guisection = _("Potential");

    opt.controlFileAll = G_define_standard_option(G_OPT_F_INPUT);
    opt.controlFileAll->key = "demand";
    opt.controlFileAll->required = YES;
    opt.controlFileAll->description =
        _("Control file with number of cells to convert");
    opt.controlFileAll->guisection = _("Demand");


    opt.devpotParamsFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.devpotParamsFile->key = "devpot_params";
    opt.devpotParamsFile->required = YES;
    opt.devpotParamsFile->label =
        _("Development potential parameters for each region");
    opt.devpotParamsFile->description =
        _("Each line should contain region ID followed"
          " by parameters (intercepts, development pressure, other predictors)."
          " Values are separated by whitespace (spaces or tabs)."
          " First line is ignored, so it can be used for header");
    opt.devpotParamsFile->guisection = _("Potential");

    opt.discountFactor = G_define_option();
    opt.discountFactor->key = "discount_factor";
    opt.discountFactor->type = TYPE_DOUBLE;
    opt.discountFactor->required = YES;
    opt.discountFactor->description = _("Discount factor of patch size");
    opt.discountFactor->guisection = _("PGA");

    opt.patchMean = G_define_option();
    opt.patchMean->key = "compactness_mean";
    opt.patchMean->type = TYPE_DOUBLE;
    opt.patchMean->required = YES;
    opt.patchMean->description =
        _("Mean value of patch compactness to control patch shapes");
    opt.patchMean->guisection = _("PGA");

    opt.patchRange = G_define_option();
    opt.patchRange->key = "compactness_range";
    opt.patchRange->type = TYPE_DOUBLE;
    opt.patchRange->required = YES;
    opt.patchRange->description =
        _("Range of patch compactness to control patch shapes");
    opt.patchRange->guisection = _("PGA");

    opt.numNeighbors = G_define_option();
    opt.numNeighbors->key = "num_neighbors";
    opt.numNeighbors->type = TYPE_INTEGER;
    opt.numNeighbors->required = YES;
    opt.numNeighbors->options = "4,8";
    opt.numNeighbors->answer = "4";
    opt.numNeighbors->description =
        _("The number of neighbors to be used for patch generation (4 or 8)");
    opt.numNeighbors->guisection = _("PGA");

    opt.seedSearch = G_define_option();
    opt.seedSearch->key = "seed_search";
    opt.seedSearch->type = TYPE_INTEGER;
    opt.seedSearch->required = YES;
    opt.seedSearch->options = "1,2";
    opt.seedSearch->answer="2";
    opt.seedSearch->description =
        _("The way location of a seed is determined (1: uniform distribution 2: development probability)");
    opt.seedSearch->guisection = _("PGA");

    opt.parcelSizeFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.parcelSizeFile->key = "patch_sizes";
    opt.parcelSizeFile->required = YES;
    opt.parcelSizeFile->description =
        _("File containing list of patch sizes to use");
    opt.parcelSizeFile->guisection = _("PGA");

    opt.devPressureFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.devPressureFile->key = "development_pressure";
    opt.devPressureFile->required = YES;
    opt.devPressureFile->description =
        _("Raster map of development pressure");
    opt.devPressureFile->guisection = _("Development pressure");

    opt.nDevNeighbourhood = G_define_option();
    opt.nDevNeighbourhood->key = "n_dev_neighbourhood";
    opt.nDevNeighbourhood->type = TYPE_INTEGER;
    opt.nDevNeighbourhood->required = YES;
    opt.nDevNeighbourhood->description =
        _("Size of square used to recalculate development pressure");
    opt.nDevNeighbourhood->guisection = _("Development pressure");

    opt.devPressureApproach = G_define_option();
    opt.devPressureApproach->key = "development_pressure_approach";
    opt.devPressureApproach->type = TYPE_STRING;
    opt.devPressureApproach->required = YES;
    opt.devPressureApproach->options = "occurrence,gravity,kernel";
    opt.devPressureApproach->description =
        _("Approaches to derive development pressure");
    opt.devPressureApproach->answer = "gravity";
    opt.devPressureApproach->guisection = _("Development pressure");

    opt.alpha = G_define_option();
    opt.alpha->key = "gamma";
    opt.alpha->type = TYPE_DOUBLE;
    opt.alpha->required = YES;
    opt.alpha->description =
        _("Influence of distance between neighboring cells");
    opt.alpha->guisection = _("Development pressure");

    opt.scalingFactor = G_define_option();
    opt.scalingFactor->key = "scaling_factor";
    opt.scalingFactor->type = TYPE_DOUBLE;
    opt.scalingFactor->required = YES;
    opt.scalingFactor->description =
        _("Scaling factor");
    opt.scalingFactor->guisection = _("Development pressure");

    opt.indexFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.indexFile->key = "subregions";
    opt.indexFile->required = YES;
    opt.indexFile->description = _("Raster map of subregions with categories starting with 1");
    opt.indexFile->guisection = _("Basic input");

    opt.numSteps = G_define_option();
    opt.numSteps->key = "num_steps";
    opt.numSteps->type = TYPE_INTEGER;
    opt.numSteps->required = NO;
    opt.numSteps->description =
        _("Number of steps to be simulated");
    opt.numSteps->guisection = _("Basic input");

    opt.probLookupFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.probLookupFile->key = "incentive_table";
    opt.probLookupFile->required = YES;
    opt.probLookupFile->label =
        _("File containing incentive lookup table (infill vs. sprawl)");
    opt.probLookupFile->description =
        _("Format is tightly constrained. See documentation.");
    opt.probLookupFile->guisection = _("Scenarios");

    opt.consWeightFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.consWeightFile->key = "constrain_weight";
    opt.consWeightFile->required = NO;
    opt.consWeightFile->label =
        _("Raster map representing development potential constraint weight for scenarios.");
    opt.consWeightFile->description =
        _("Values must be between 0 and 1, 1 means no constraint.");
    opt.consWeightFile->guisection = _("Scenarios");

    opt.seed = G_define_option();
    opt.seed->key = "random_seed";
    opt.seed->type = TYPE_INTEGER;
    opt.seed->required = NO;
    opt.seed->label = _("Seed for random number generator");
    opt.seed->description =
        _("The same seed can be used to obtain same results"
          " or random seed can be generated by other means.");
    opt.seed->guisection = _("Random numbers");

    flg.generateSeed = G_define_flag();
    flg.generateSeed->key = 's';
    flg.generateSeed->label =
        _("Generate random seed (result is non-deterministic)");
    flg.generateSeed->description =
        _("Automatically generates random seed for random number"
          " generator (use when you don't want to provide the seed option)");
    flg.generateSeed->guisection = _("Random numbers");

    opt.dumpFile = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.dumpFile->key = "output";
    opt.dumpFile->required = YES;
    opt.dumpFile->description =
        _("State of the development at the end of simulation");
    opt.dumpFile->guisection = _("Output");

    opt.outputSeries = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.outputSeries->key = "output_series";
    opt.outputSeries->required = NO;
    opt.outputSeries->label =
        _("Basename for raster maps of development generated after each step");
    opt.outputSeries->guisection = _("Output");
    // TODO: add mutually exclusive?
    // TODO: add flags or options to control values in series and final rasters


    // provided XOR generated
    G_option_exclusive(opt.seed, flg.generateSeed, NULL);
    G_option_required(opt.seed, flg.generateSeed, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    long seed_value;

    if (flg.generateSeed->answer) {
        seed_value = G_srand48_auto();
        G_message("Generated random seed (-s): %ld", seed_value);
    }
    if (opt.seed->answer) {
        seed_value = atol(opt.seed->answer);
        // this does nothing since we are not using GRASS random function
        G_srand48(seed_value);
        G_message("Read random seed from %s option: %ld",
                  opt.seed->key, seed_value);
    }
    // although GRASS random function is initialized
    // the general one must be done separately
    // TODO: replace all by GRASS random number generator?
    srand(seed_value);

    // TODO: move this back to local variables
    //t_Params      sParams;
    //t_Landscape   sLandscape;

    /* blank everything out */
    memset(&sParams, 0, sizeof(t_Params));
    sParams.region_map = KeyValueIntInt_create();

    /* parameters dependednt on region */
    sParams.xSize = Rast_window_rows();
    sParams.ySize = Rast_window_cols();
    G_message(_("Running on %d rows and %d columns (%d cells)"),
              sParams.xSize, sParams.ySize, sParams.xSize * sParams.ySize);

    /* set up parameters */
    sParams.developedFile = opt.developedFile->answer;
    sParams.devPressureFile = opt.devPressureFile->answer;
    sParams.consWeightFile = opt.consWeightFile->answer;
    sParams.numAddVariables = 0;
    if (opt.numSteps->answer)
        sParams.nSteps = atoi(opt.numSteps->answer);

    size_t num_answers = 0;
    while (opt.addVariableFiles->answers[num_answers]) {
        sParams.addVariableFile[num_answers] = opt.addVariableFiles->answers[num_answers];
        num_answers++;
    }
    sParams.numAddVariables = num_answers;
    // TODO: dyn allocate file list
    sParams.nDevNeighbourhood = atoi(opt.nDevNeighbourhood->answer);

    sParams.dumpFile = opt.dumpFile->answer;
    sParams.outputSeries = opt.outputSeries->answer;

    sParams.parcelSizeFile = opt.parcelSizeFile->answer;

    sParams.discountFactor = atof(opt.discountFactor->answer);

    // TODO: remove all sortProbs != 0 code if it does not make sense for Stochastic 2
    // always 0 for Stochastic 2
    sParams.sortProbs = 0;

    // TODO: remove remaining stochastic 1 and deterministic code
    // stochastic 1 and deterministic not maintained, reimplementing considered as easier
    // then fixing it (old code will be still available in the old version)
    // always use Stochastic II
    sParams.nAlgorithm = _N_ALGORITHM_STOCHASTIC_II;

    if (sParams.nAlgorithm == _N_ALGORITHM_STOCHASTIC_II) {

        int parsedOK, i;
        FILE *fp;
        char inBuff[N_MAXREADINLEN];
        char *pPtr;

        G_verbose_message("Reading probability lookup ...");
        sParams.probLookupFile = opt.probLookupFile->answer;

        fp = fopen(sParams.probLookupFile, "r");
        if (fp) {
            parsedOK = 0;
            if (fgets(inBuff, N_MAXREADINLEN, fp)) {
                if (inBuff[0] == ',') {
                    sParams.nProbLookup = atoi(inBuff + 1);
                    if (sParams.nProbLookup > 0) {
                        sParams.adProbLookup =
                            (double *)malloc(sizeof(double) *
                                             sParams.nProbLookup);
                        if (sParams.adProbLookup) {
                            parsedOK = 1;
                            i = 0;
                            while (parsedOK && i < sParams.nProbLookup) {
                                parsedOK = 0;
                                if (fgets(inBuff, N_MAXREADINLEN, fp)) {
                                    if (pPtr = strchr(inBuff, ',')) {
                                        parsedOK = 1;
                                        sParams.adProbLookup[i] =
                                            atof(pPtr + 1);
                                        G_debug(3,
                                                "probability lookup table: i=%d, i/(n-1)=%f, result=%f",
                                                i,
                                                i * 1.0 /
                                                (sParams.nProbLookup - 1),
                                                sParams.adProbLookup[i]);
                                    }
                                }
                                i++;
                            }
                        }
                    }
                }
            }
            if (!parsedOK) {
                G_fatal_error("Error parsing probability lookup file '%s'",
                        sParams.probLookupFile);
            }
            fclose(fp);
        }
        else {
            G_fatal_error("Error opening probability lookup file '%s'",
                    sParams.probLookupFile);
        }

        sParams.patchMean = atof(opt.patchMean->answer);
        sParams.patchRange = atof(opt.patchRange->answer);
        sParams.numNeighbors = atoi(opt.numNeighbors->answer);
        // TODO: convert to options or flag: 1: uniform distribution 2: based on dev. proba.
        sParams.seedSearch = atoi(opt.seedSearch->answer);
        sParams.devPressureApproach = atoi(opt.devPressureApproach->answer);
        if (strcmp(opt.devPressureApproach->answer, "occurrence") == 0)
            sParams.devPressureApproach = 1;
        else if (strcmp(opt.devPressureApproach->answer, "gravity") == 0)
            sParams.devPressureApproach = 2;
        else if (strcmp(opt.devPressureApproach->answer, "kernel") == 0)
            sParams.devPressureApproach = 3;
        else
            G_fatal_error(_("Approach doesn't exist"));
        if (sParams.devPressureApproach != 1) {
            sParams.alpha = atof(opt.alpha->answer);
            sParams.scalingFactor = atof(opt.scalingFactor->answer);
        }

        sParams.indexFile = opt.indexFile->answer;
        sParams.controlFileAll = opt.controlFileAll->answer;
    }

    /* allocate memory */
    if (buildLandscape(&sLandscape, &sParams)) {
        /* read data */
        if (readData(&sLandscape, &sParams)) {
            readData4AdditionalVariables(&sLandscape, &sParams);
            readIndexData(&sLandscape, &sParams);
            // initialize the overflow demands to zero
            for (int i = 0; i < sParams.num_Regions; i++) {
                sParams.overflowDevDemands[i] = 0;
            }
            readDevDemand(&sParams);
            if (sParams.num_Regions > 1)
                readDevPotParams(&sParams, opt.devpotParamsFile->answer);
            if (readParcelSizes(&sLandscape, &sParams)) {
                //testDevPressure(&sLandscape, &sParams);
                /* do calculation and dump result */
                //one region, enable the following
                //updateMap(&sLandscape, &sParams);

                //multiple regions
                updateMapAll(&sLandscape, &sParams);
            }
            else {
                G_fatal_error("Reading patch sizes failed");
            }
        }
        else {
            G_fatal_error("Reading input maps failed");
        }
        /* could put in routines to free memory, but OS will garbage collect anyway */
    }
    else {
        G_fatal_error("Initialization failed");
    }
    KeyValueIntInt_free(sParams.region_map);
    G_free(sLandscape.predictors);
    if (sLandscape.consWeight)
        G_free(sLandscape.consWeight);

    return EXIT_SUCCESS;
}

int getUnDevIndex(t_Landscape * pLandscape)
{
    float p = rand() / (double)RAND_MAX;
    int i;

    for (i = 0; i < pLandscape->undevSites; i++) {
        if (p < pLandscape->asUndev[i].cumulProb) {
            return i;
        }
    }
    // TODO: returning at least something but should be something more meaningful
    return 0;
}

int getUnDevIndex1(t_Landscape * pLandscape, int regionID)
{
    float p = rand() / (double)RAND_MAX;

    G_debug(3, _("getUnDevIndex1: regionID=%d, num_undevSites=%d, p=%f"),
                      regionID, pLandscape->num_undevSites[regionID], p);
    int i;

    for (i = 0; i < pLandscape->num_undevSites[regionID]; i++) {
        if (p < pLandscape->asUndevs[regionID][i].cumulProb) {
            G_debug(3, _("getUnDevIndex1: cumulProb=%f"),
                              pLandscape->asUndevs[regionID][i].cumulProb);
            return i;
        }
    }
    // TODO: returning at least something but should be something more meaningful
    return 0;
}

void findAndSortProbsAll(t_Landscape * pLandscape, t_Params * pParams,
                         int step)
{
    int i, lookupPos;
    t_Cell *pThis;
    int id;

    /* update calcs */
    G_verbose_message("Recalculating probabilities");
    for (i = 0; i < pParams->num_Regions; i++) {
        pLandscape->num_undevSites[i] = 0;
    }
    float val = 0.0;

    for (i = 0; i < pLandscape->totalCells; i++) {
        pThis = &(pLandscape->asCells[i]);
        if (pThis->nCellType == _CELL_VALID) {
            if (pThis->bUndeveloped) {
                double consWeight = pLandscape->consWeight ? pLandscape->consWeight[i] : 1;
                if (consWeight > 0.0) {
                    id = pThis->index_region;
                    if (pThis->index_region == -9999)
                        continue;
                    /* note that are no longer just storing the logit value,
                       but instead the probability
                       (allows consWeight to affect sort order) */

                    if (id < 0 || id >= pParams->num_Regions)
                        G_fatal_error(_("Index of region %d is out of range [0, %d] (region is %d)"),
                                      id, pParams->num_Regions - 1,
                                      pThis->index_region);

                    if (pLandscape->num_undevSites[id] >= pLandscape->asUndevs_ns[id]) {
                        pLandscape->asUndevs[id] = (t_Undev *) G_realloc(pLandscape->asUndevs[id], pLandscape->asUndevs_ns[id] * 2 * sizeof(t_Undev));
                    }
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].
                        cellID = i;
                    val = getDevProbability(pThis, pParams);
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].
                        logitVal = val;
                    G_debug(2, "logit value %f", val);
                    /* lookup table of probabilities is applied before consWeight */
                    if (pParams->nAlgorithm == _N_ALGORITHM_STOCHASTIC_II) {
                        /* replace with value from lookup table */
                        lookupPos = (int)(pLandscape->asUndevs[id]
                                          [pLandscape->num_undevSites[id]].
                                          logitVal * (pParams->nProbLookup -
                                                      1));
                        if (lookupPos >= pParams->nProbLookup ||
                            lookupPos < 0)
                            G_fatal_error
                                ("lookup position (%d) out of range [0, %d]",
                                 lookupPos, pParams->nProbLookup - 1);
                        pLandscape->asUndevs[id][pLandscape->
                                                 num_undevSites[id]].
                            logitVal = pParams->adProbLookup[lookupPos];
                    }
                    // discount by a conservation factor
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].logitVal *= consWeight;
                    /* need to store this to put correct elements near top of list */
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].bUntouched = pThis->bUntouched;
                    if (pLandscape->asUndevs[id]
                        [pLandscape->num_undevSites[id]].logitVal > 0.0) {
                        /* only add one more to the list if have a positive probability */
                        pLandscape->num_undevSites[id]++;
                    }
                }
            }
        }
    }
    /* sort */
    /* can only be zero for algorithm=stochastic_ii */
    if (pParams->sortProbs) {
        G_debug(1, "Sorting %d unconserved undeveloped sites",
                pLandscape->undevSites);
        qsort(pLandscape->asUndev, pLandscape->undevSites, sizeof(t_Undev),
              undevCmpReverse);
    }
    else {
        G_debug(1, "Skipping sort as choosing cells randomly");
    }
    //calculate cumulative probability // From Wenwu Tang
    int j;

    for (j = 0; j < pParams->num_Regions; j++) {
        double sum = pLandscape->asUndevs[j][0].logitVal;

        for (i = 1; i < pLandscape->num_undevSites[j]; i++) {
            pLandscape->asUndevs[j][i].cumulProb =
                pLandscape->asUndevs[j][i - 1].cumulProb +
                pLandscape->asUndevs[j][i].logitVal;
            sum = sum + pLandscape->asUndevs[j][i].logitVal;
        }
        for (i = 0; i < pLandscape->num_undevSites[j]; i++) {
            pLandscape->asUndevs[j][i].cumulProb =
                pLandscape->asUndevs[j][i].cumulProb / sum;
        }
    }
}
