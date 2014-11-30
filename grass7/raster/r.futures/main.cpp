
/****************************************************************************
 *
 * MODULE:       r.futures
 * AUTHOR(S):    Ross K. Meentemeyer
 *               Wenwu Tang
 *               Monica A. Dorning
 *               John B. Vogler
 *               Nik J. Cunniffe
 *               Douglas A. Shoemaker
 *               Jennifer A. Koch
 *               Vaclav Petras <wenzeslaus gmail com>
 *               (See the manual page for details and references.)
 *
 * PURPOSE:      Simulation of urban-rural landscape structure (FUTURES model)
 *
 * COPYRIGHT:    (C) 2013-2014 by Meentemeyer et al.
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
#include <string.h>
#include <math.h>
#include <sys/time.h>
#include <iostream>
#include <fstream>
#include <vector>

extern "C"
{
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
}

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
#define maxNumAddVariables 6

/** maximal number of counties allowed */
#define MAXNUM_COUNTY 50
#define MAX_YEARS 100
/// maximum array size for undev cells (maximum: 1840198 for a county within 16 counties)
#define MAX_UNDEV_SIZE 2000000
using namespace std;


/* Wenwu Tang */
/// use absolute paths
char dirName[100];

/// string for temporarily storage
char tempStr[100];



typedef struct
{

    /** see #define's starting _CELL_ above */
    int nCellType;

    /** attraction to employment base; static */
    double employAttraction;

    /** distance to interchange; static */
    double interchangeDistance;

    /** road density; static */
    double roadDensity;

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

    /** multiplicative factor on the probabilities */
    double consWeight;

    /** additional variables */
    double additionVariable[maxNumAddVariables];
    int index_region;
    float devProba;
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
      std::vector < std::vector < t_Undev > >asUndevs;  //WT
    int num_undevSites[MAXNUM_COUNTY];  //WT
} t_Landscape;

typedef struct
{

    /** size of the grids */
    int xSize;

    /** size of the grids */
    int ySize;

    /** file containing information on how many cells to transition and when */
    char *controlFile;

    /** files containing the information to read in */
    char *employAttractionFile;
    char *interchangeDistanceFile;
    char *roadDensityFile;
    char *undevelopedFile;
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

    /** use this to downweight probabilities */
    double dProbWeight;

    /** and this to downweight old dev pressure */
    double dDevPersistence;

    /** file containing parcel size information */
    char *parcelSizeFile;
    double discountFactor;      ///< for calibrate patch size

    /** give up spiralling around when examined this number of times too many cells */
    double giveUpRatio;

    /** these parameters only relevant for new stochastic algorithm */
    int sortProbs;
    double patchFactor;
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
    double dV1[MAXNUM_COUNTY];
    double dV2[MAXNUM_COUNTY];
    double dV3[MAXNUM_COUNTY];
    double dV4[MAXNUM_COUNTY];
    int num_Regions;

    /** index file to run multiple regions */
    char *indexFile;

    /// control files for all regions
    /// development demand for multiple regions
    char *controlFileAll;
    int devDemand[MAX_YEARS];
    int devDemands[MAXNUM_COUNTY][MAX_YEARS];
    /// number of simulation steps
    int nSteps;
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
    char str[200];
    int id;
    double di, d1, d2, d3, d4, val;

    // TODO: d5 is in file but unused
    int i, j;
    ifstream f;

    f.open(fn);
    if (!f.is_open())
        G_fatal_error(_("Cannot open development potential parameters file <%s>"),
                      fn);

    f.getline(str, 200);
    for (i = 0; i < pParams->num_Regions; i++) {
        // TODO: read by lines to count the variables
        f >> id >> di >> d1 >> d2 >> d3 >> d4;
        cout << id << "\t" << di << "\t" << d1 << "\t" << d2 << "\t" << d3 <<
            "\t" << d4;

        pParams->dIntercepts[i] = di;
        pParams->dV1[i] = d1;
        pParams->dV2[i] = d2;
        pParams->dV3[i] = d3;
        pParams->dV4[i] = d4;
        for (j = 0; j < pParams->numAddVariables; j++) {
            f >> val;
            cout << "\t" << val;
            pParams->addParameters[j][i] = val;
        }
        cout << endl;
    }
    f.close();
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
    fprintf(stdout, "entered buildLandscape()\n");
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
        if (pParams->num_Regions > 1) {
            /* just allocate enough space for every cell to be undev */
            pLandscape->asUndev = (t_Undev *) malloc(sizeof(t_Undev) * pLandscape->totalCells);
            if (pLandscape->asUndev) {
                bRet = 1;
            }
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

    for (i = 0; i < pParams->numAddVariables; i++) {
        cout << "reading additional variables File: " <<
            pParams->addVariableFile[i] << "...";

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
                if (pLandscape->asCells[ii].nCellType == _CELL_VALID)
                    pLandscape->asCells[ii].additionVariable[i] = val;
                else
                    pLandscape->asCells[ii].additionVariable[i] = 0.0;
                ii++;
            }
        }
        Rast_close(fd);
        cout << "done" << endl;
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

    cout << "reading index File: " << pParams->indexFile << "...";
    for (int row = 0; row < pParams->xSize; row++) {
        Rast_get_row(fd, buffer, row, data_type);
        void *ptr = buffer;

        for (int col = 0; col < pParams->ySize; col++,
             ptr = G_incr_void_ptr(ptr, Rast_cell_size(data_type))) {
            if (Rast_is_null_value(ptr, data_type))
                val = _GIS_NO_DATA_INT; // assign FUTURES representation of NULL value
            else {
                val = *(CELL *) ptr;
                if (val > pParams->num_Regions)
                    G_fatal_error(_("Region ID (%d) inconsistent with number of regions (%d) in map <%s>"),
                                  val, pParams->num_Regions,
                                  pParams->indexFile);
                if (val < 1)
                    G_fatal_error(_("Region ID (%d) is smaller then 1 in map <%s>"),
                                  val, pParams->indexFile);
            }

            pLandscape->asCells[ii].index_region = val;
            ii++;
        }
    }
    cout << "done" << endl;
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

    fprintf(stdout, "entered readData()\n");
    bRet = 0;
    szBuff = (char *)malloc(_N_MAX_DYNAMIC_BUFF_LEN * sizeof(char));
    if (szBuff) {
        for (j = 0; j < 6; j++) {
            switch (j) {        /* get correct filename */
            case 0:
                strcpy(szFName, pParams->undevelopedFile);
                break;
            case 1:
                strcpy(szFName, pParams->employAttractionFile);
                break;
            case 2:
                strcpy(szFName, pParams->interchangeDistanceFile);
                break;
            case 3:
                strcpy(szFName, pParams->roadDensityFile);
                break;
            case 4:
                strcpy(szFName, pParams->devPressureFile);
                break;
            case 5:
                strcpy(szFName, pParams->consWeightFile);
                break;
            default:
                fprintf(stderr, "readData(): shouldn't get here...\n");
                break;
            }
            fprintf(stdout, "\t%s...", szFName);
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
                            pLandscape->asCells[i].bUndeveloped = iVal;
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
                            pLandscape->asCells[i].employAttraction = dVal;
                            break;
                        case 2:
                            pLandscape->asCells[i].interchangeDistance = dVal;
                            break;
                        case 3:
                            pLandscape->asCells[i].roadDensity = dVal;
                            break;
                        case 4:
                            pLandscape->asCells[i].devPressure = (int)dVal;
                            break;
                        case 5:
                            pLandscape->asCells[i].consWeight = dVal;
                            break;
                        default:
                            fprintf(stderr,
                                    "readData(): shouldn't get here...\n");
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
                    fprintf(stderr, "readData(): x too small\n");
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
                    fprintf(stderr, "readData(): y too small\n");
                    bRet = 0;
                }
            }
            else {
                if (bRet && i == pLandscape->totalCells) {
                    fprintf(stdout, "done\n");;
                }
                else {

                    if (bRet) {
                        G_message(_("x=%d y=%d"), x, y);
                        G_message(_(" xSize=%d ySize=%d"), pParams->xSize,
                                  pParams->ySize);
                        G_message(_(" maxX=%d minX=%d"), pLandscape->maxX,
                                  pLandscape->maxY);
                        fprintf(stderr,
                                "readData(): not read in enough points\n");
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
    id = id - 1;
    probAdd = pParams->dIntercepts[id];
    //cout<<"intercept\t"<<probAdd<<endl;
    probAdd += pParams->dV1[id] * pThis->employAttraction;
    //cout<<"employAttraction: "<<pParams->dV1[id]<<endl;
    //cout<<"employAttraction: "<<pThis->employAttraction<<endl;
    //cout<<"employAttraction: "<<pParams->dV1[id] * pThis->employAttraction<<endl;
    probAdd += pParams->dV2[id] * pThis->interchangeDistance;
    //cout<<"interchangeDistance: "<<pParams->dV2[id]<<endl;
    //cout<<"interchangeDistance: "<<pThis->interchangeDistance<<endl;
    //cout<<"interchangeDistance: "<<pParams->dV2[id] * pThis->interchangeDistance<<endl;
    probAdd += pParams->dV3[id] * pThis->roadDensity;
    //cout<<"roadDensity: "<<pParams->dV3[id]<<endl;
    //cout<<"roadDensity: "<<pThis->roadDensity<<endl;
    //cout<<"roadDensity: "<<pParams->dV3[id] * pThis->roadDensity<<endl;
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
    fprintf(stdout, "\t\trecalculating probabilities\n");
    pLandscape->undevSites = 0;
    for (i = 0; i < pLandscape->totalCells; i++) {
        pThis = &(pLandscape->asCells[i]);
        if (pThis->nCellType == _CELL_VALID) {
            if (pThis->bUndeveloped) {
                if (pThis->consWeight > 0.0) {
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
                    pLandscape->asUndev[pLandscape->undevSites].logitVal *=
                        pThis->consWeight;
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
    /* downweight the devPressure if necessary (do not do in first step) */
    /* doing it here means that last time step values have full weight */
    if (pParams->nAlgorithm == _N_ALGORITHM_STOCHASTIC_I) {
        if (pParams->dDevPersistence < 1.0) {
            fprintf(stdout, "\t\tdownweighting development pressure\n");

            for (i = 0; i < pLandscape->totalCells; i++) {
                pThis = &(pLandscape->asCells[i]);
                if (pThis->nCellType == _CELL_VALID) {
                    /* only need to bother downweighting on cells that can still convert */
                    if (pThis->bUndeveloped) {
                        pThis->devPressure =
                            (int)((double)pThis->devPressure *
                                  pParams->dDevPersistence);
                    }
                }
            }
        }
    }
    /* sort */
    /* can only be zero for algorithm=stochastic_ii */
    if (pParams->sortProbs) {
        fprintf(stdout, "\t\tsorting %d unconserved undeveloped sites\n",
                pLandscape->undevSites);
        qsort(pLandscape->asUndev, pLandscape->undevSites, sizeof(t_Undev),
              undevCmpReverse);
    }
    else {
        fprintf(stdout, "\t\tskipping sort as choosing cells randomly\n");
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
    Create patches based on spiraling around.

    \deprecated
*/
int fillValidNeighbourList(int nThisID, t_Landscape * pLandscape,
                           t_Params * pParams, int *anToConvert,
                           int nWantToConvert, int bAllowTouched,
                           int bDeterministic)
{
    int nTried, nFound, x, y, upDown, stopAt, countMove, stepMove, nPos,
        nSkipped;

    anToConvert[0] = nThisID;
    nSkipped = 0;
    nFound = 1;
    nTried = 1;
    x = pLandscape->asCells[nThisID].thisX;
    y = pLandscape->asCells[nThisID].thisY;
    stopAt = 0;
    upDown = 0;
    stepMove = -1;
    while (nFound < nWantToConvert &&
           ((double)nWantToConvert * pParams->giveUpRatio) > nTried) {
        countMove = 0;
        upDown = !upDown;
        if (upDown) {
            stopAt++;
            stepMove *= -1;
        }
        while (countMove < stopAt && nFound < nWantToConvert &&
               ((double)nWantToConvert * pParams->giveUpRatio) > nTried) {
            if (upDown) {
                x += stepMove;
            }
            else {
                y += stepMove;
            }
            // fprintf(stdout, "%d %d\n", x, y);
            nPos = posFromXY(x, y, pLandscape);
            if (nPos != _CELL_OUT_OF_RANGE) {
                if (pLandscape->asCells[nPos].nCellType == _CELL_VALID) {
                    if (pLandscape->asCells[nPos].bUndeveloped) {
                        if (bAllowTouched ||
                            pLandscape->asCells[nPos].bUntouched) {
                            if (bDeterministic ||
                                (uniformRandom() < pParams->dProbWeight)) {
                                if (pLandscape->asCells[nPos].consWeight >
                                    0.0) {
                                    anToConvert[nFound] = nPos;
                                    nFound++;
                                }
                            }
                            else {
                                pLandscape->asCells[nPos].bUntouched = 0;
                                nSkipped++;
                            }
                        }
                    }
                }
            }
            nTried++;
            countMove++;
        }
    }
    // fprintf(stdout, "\tskipped=%d\n", nSkipped);
    return nFound;
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
                if (pThis->consWeight > 0.0) {
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
                                fprintf(stderr,
                                        "memory error in addNeighbourIfPoss()\n...exiting\n");
                                exit(EXIT_FAILURE);
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
                        probAdd *= pThis->consWeight;
                        /* multiply by the patch factor to help control shapes of patches */
                        // pF now is set to 1, so it won't affect the result.or this can be deleted // WT
                        probAdd *= pParams->patchFactor;
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
        if (pParams->nAlgorithm == _N_ALGORITHM_STOCHASTIC_II) {
            nToConvert =
                newPatchFinder(nThisID, pLandscape, pParams, anToConvert,
                               nWantToConvert);
        }
        else {
            nToConvert =
                fillValidNeighbourList(nThisID, pLandscape, pParams,
                                       anToConvert, nWantToConvert,
                                       bAllowTouched, bDeterministic);
        }
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

/**
    main routine to actually run the model
*/
void updateMap(t_Landscape * pLandscape, t_Params * pParams)
{
    FILE *fIn;
    char *szBuff;
    char szStepLabel[_N_MAX_FILENAME_LEN];
    int i, nToConvert, nStep, nDone, bAllowTouched, nRandTries, nExtra;
    double dProb;
    t_Cell *pThis;

    nExtra = 0;
    fprintf(stdout, "entered updateMap()\n");
    fIn = fopen(pParams->controlFile, "rb");
    if (fIn) {
        szBuff = (char *)malloc(_N_MAX_DYNAMIC_BUFF_LEN * sizeof(char));
        if (szBuff) {
            /* start counter at 1 so can distinguish between cells
               which transition on first step and those which already developed */
            nStep = 1;
            while (fgets(szBuff, _N_MAX_DYNAMIC_BUFF_LEN, fIn)) {
                if (parseControlLine(szBuff, szStepLabel, &nToConvert)) {
                    fprintf(stdout,
                            "\tdoing step %s...controlFile requests conversion of %d cells\n",
                            szStepLabel, nToConvert);
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
                    fprintf(stdout,
                            "\t\tafter accounting for extra cells, attempt %d cells\n",
                            nToConvert);
                    /* if have cells to convert this step */
                    if (nToConvert > 0) {
                        findAndSortProbs(pLandscape, pParams, nToConvert);
                        /* if not enough cells to convert then alter number required */
                        if (nToConvert > pLandscape->undevSites) {
                            fprintf(stdout,
                                    "\t\tnot enough undeveloped sites...converting all\n");
                            nToConvert = pLandscape->undevSites;
                        }
                        /* update either in deterministic or stochastic fashion */
                        fprintf(stdout, "\t\tupdating map\n");
                        switch (pParams->nAlgorithm) {
                        case _N_ALGORITHM_DETERMINISTIC:       /* deterministic */
                            nDone = 0;
                            for (i = 0; i < nToConvert && nDone < nToConvert;
                                 i++) {
                                nDone +=
                                    convertCells(pLandscape, pParams,
                                                 pLandscape->asUndev[i].
                                                 cellID, nStep, 1, 1);
                            }
                            break;
                        case _N_ALGORITHM_STOCHASTIC_I:        /* stochastic */
                            nDone = 0;
                            i = 0;
                            bAllowTouched = 0;
                            /* loop until done enough cells...might need multiple passes */
                            while (nDone < nToConvert) {
                                if (i == pLandscape->undevSites) {
                                    /* if at the end of the grid, just loop around again until done */
                                    i = 0;
                                    /* allow previously considered cells if you have to */
                                    bAllowTouched = 1;
                                }
                                pThis =
                                    &(pLandscape->asCells
                                      [pLandscape->asUndev[i].cellID]);
                                if (pThis->bUndeveloped) {      /* need to check is still undeveloped */
                                    if (bAllowTouched || pThis->bUntouched) {
                                        /* Doug's "back to front" logit */
                                        // dProb = 1.0/(1.0 + exp(pLandscape->asUndev[i].logitVal));
                                        dProb =
                                            pLandscape->asUndev[i].logitVal;
                                        /* if starting a patch off here */
                                        if (uniformRandom() <
                                            pParams->dProbWeight * dProb) {
                                            nDone +=
                                                convertCells(pLandscape,
                                                             pParams,
                                                             pLandscape->
                                                             asUndev[i].
                                                             cellID, nStep,
                                                             bAllowTouched,
                                                             0);
                                        }
                                    }
                                    pThis->bUntouched = 0;
                                }
                                i++;
                            }
                            break;
                        case _N_ALGORITHM_STOCHASTIC_II:  /* stochastic */
                            nDone = 0;
                            i = 0;
                            nRandTries = 0;
                            bAllowTouched = 0;
                            /* loop until done enough cells...might need multiple passes */
                            while (nDone < nToConvert) {
                                if (i == pLandscape->undevSites) {
                                    /* if at the end of the grid, just loop around again until done */
                                    i = 0;
                                    /* allow previously considered cells if you have to */
                                    bAllowTouched = 1;
                                }
                                /* if tried too many randomly in this step, give up on idea of only letting untouched cells convert */
                                if (nRandTries >
                                    _MAX_RAND_FIND_SEED_FACTOR * nToConvert) {
                                    bAllowTouched = 1;
                                }
                                if (pParams->sortProbs) {
                                    /* if sorted then choose the top cell and do nothing */
                                }
                                else {
                                    /* otherwise give a random undeveloped cell a go */
                                    if (sParams.seedSearch == 1)
                                        i = (int)(uniformRandom() *
                                                  pLandscape->undevSites);
                                    // pick one according to their probability
                                    else
                                        i = getUnDevIndex(pLandscape);

                                }
                                pThis =
                                    &(pLandscape->asCells
                                      [pLandscape->asUndev[i].cellID]);

                                if (pThis->bUndeveloped) {      /* need to check is still undeveloped */
                                    if (bAllowTouched || pThis->bUntouched) {
                                        /* Doug's "back to front" logit */
                                        // dProb = 1.0/(1.0 + exp(pLandscape->asUndev[i].logitVal));
                                        dProb =
                                            pLandscape->asUndev[i].logitVal;
                                        if (uniformRandom() < dProb) {
                                            nDone +=
                                                convertCells(pLandscape,
                                                             pParams,
                                                             pLandscape->
                                                             asUndev[i].
                                                             cellID, nStep,
                                                             bAllowTouched,
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
                            fprintf(stderr, "Unknown algorithm...exiting\n");
                            break;
                        }
                        fprintf(stdout, "\t\tconverted %d sites\n", nDone);
                        nExtra += (nDone - nToConvert);
                        fprintf(stdout,
                                "\t\t%d extra sites knocked off next timestep\n",
                                nExtra);
                    }
                }
                nStep++;  /* next time step */
            }
            /* dump results to a file at the end of the run */
            outputDevRasterStep(pLandscape, pParams, pParams->dumpFile, false,
                                false);
            free(szBuff);
        }
        fclose(fIn);
    }
}

void readDevDemand(t_Params * pParams)
{
    ifstream f1;

    /*
       f1.open(pParams->controlFile);
       int counter=0;
       int val1,val2;
       while(!f1.eof()){
       f1>>val1>>val2;
       pParams->devDemand[counter]=val2;
       counter++;
       }
       pParams->nSteps=counter;
       f1.close();
     */
    //read land demand for each region
    int i;
    int val1;
    char str[200];

    f1.open(pParams->controlFileAll);
    f1 >> str >> val1;
    pParams->nSteps = val1;
    f1.getline(str, 200);
    f1.getline(str, 200);  //skip the header
    int ii;

    for (ii = 0; ii < pParams->nSteps; ii++) {
        f1 >> val1;
        for (i = 0; i < pParams->num_Regions; i++) {
            f1 >> val1;
            pParams->devDemands[i][ii] = val1;
        }

    }
    f1.close();

}

void initializeUnDev(t_Landscape * pLandscape, t_Params * pParams)
{
    int i;

    pLandscape->asUndevs.clear();
    pLandscape->asUndevs.resize(pParams->num_Regions,
                                std::vector < t_Undev > (MAX_UNDEV_SIZE));
    for (i = 0; i < pParams->num_Regions; i++) {
        pLandscape->num_undevSites[i] = 0;
    }
}

void finalizeUnDev(t_Landscape * pLandscape, t_Params * pParams)
{

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
        cout << i << "\t" << pParams->nSteps << endl;
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

    nExtra = 0;

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
    fprintf(stdout,
            "\t\tafter accounting for extra cells, attempt %d cells\n",
            nToConvert);
    /* if have cells to convert this step */
    if (nToConvert > 0) {
        //findAndSortProbs(pLandscape, pParams, nToConvert);
        /* if not enough cells to convert then alter number required */
        if (nToConvert > pLandscape->num_undevSites[regionID]) {
            fprintf(stdout,
                    "\t\tnot enough undeveloped sites...converting all\n");
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
        case _N_ALGORITHM_STOCHASTIC_I:        /* stochastic */
            nDone = 0;
            i = 0;
            bAllowTouched = 0;
            /* loop until done enough cells...might need multiple passes */
            while (nDone < nToConvert) {
                if (i == pLandscape->undevSites) {
                    /* if at the end of the grid, just loop around again until done */
                    i = 0;
                    /* allow previously considered cells if you have to */
                    bAllowTouched = 1;
                }
                pThis = &(pLandscape->asCells[pLandscape->asUndev[i].cellID]);
                /* need to check is still undeveloped */
                if (pThis->bUndeveloped) {
                    if (bAllowTouched || pThis->bUntouched) {
                        /* Doug's "back to front" logit */
                        // dProb = 1.0/(1.0 + exp(pLandscape->asUndev[i].logitVal));
                        dProb = pLandscape->asUndev[i].logitVal;
                        /* if starting a patch off here */
                        if (uniformRandom() < pParams->dProbWeight * dProb) {
                            nDone +=
                                convertCells(pLandscape, pParams,
                                             pLandscape->asUndev[i].cellID,
                                             nStep, bAllowTouched, 0);
                        }
                    }
                    pThis->bUntouched = 0;
                }
                i++;
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
                        G_verbose_message("nDone=%d, toConvert=%d", nDone,
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
            fprintf(stderr, "Unknown algorithm...exiting\n");
            break;
        }
        fprintf(stdout, "\t\tconverted %d sites\n", nDone);
        nExtra += (nDone - nToConvert);
        fprintf(stdout, "\t\t%d extra sites knocked off next timestep\n",
                nExtra);
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

    fprintf(stdout, "entered readParcelSizes()\n");
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
            *controlFile, *employAttractionFile, *interchangeDistanceFile,
            *roadDensityFile, *undevelopedFile, *devPressureFile,
            *consWeightFile, *addVariableFiles, *nDevNeighbourhood,
            *devpotParamsFile, *dumpFile, *outputSeries, *algorithm,
            *dProbWeight, *dDevPersistence, *parcelSizeFile, *discountFactor,
            *giveUpRatio, *probLookupFile, *sortProbs, *patchFactor,
            *patchMean, *patchRange, *numNeighbors, *seedSearch,
            *devPressureApproach, *alpha, *scalingFactor, *num_Regions,
            *indexFile, *controlFileAll, *seed;

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

    opt.controlFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.controlFile->key = "control_file";
    opt.controlFile->required = NO;
    opt.controlFile->label =
        _("File containing information on how many cells to transition and when");
    opt.controlFile->description =
        _("Needed only for single region/zone run");

    opt.undevelopedFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.undevelopedFile->key = "undeveloped";
    opt.undevelopedFile->required = YES;
    opt.undevelopedFile->description =
        _("Files containing the information to read in");

    opt.employAttractionFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.employAttractionFile->key = "employ_attraction";
    opt.employAttractionFile->required = YES;
    opt.employAttractionFile->description =
        _("Files containing the information to read in");

    opt.interchangeDistanceFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.interchangeDistanceFile->key = "interchange_distance";
    opt.interchangeDistanceFile->required = YES;
    opt.interchangeDistanceFile->description =
        _("Files containing the information to read in");

    opt.roadDensityFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.roadDensityFile->key = "road_density";
    opt.roadDensityFile->required = YES;
    opt.roadDensityFile->description =
        _("Files containing the information to read in");

    opt.devPressureFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.devPressureFile->key = "development_pressure";
    opt.devPressureFile->required = YES;
    opt.devPressureFile->description =
        _("Files containing the information to read in");

    opt.consWeightFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.consWeightFile->key = "cons_weight";
    opt.consWeightFile->required = YES;
    opt.consWeightFile->description =
        _("Files containing the information to read in");

    opt.addVariableFiles = G_define_standard_option(G_OPT_R_INPUT);
    opt.addVariableFiles->key = "additional_variable_files";
    opt.addVariableFiles->required = YES;
    opt.addVariableFiles->multiple = YES;
    opt.addVariableFiles->description = _("additional variables");

    opt.nDevNeighbourhood = G_define_option();
    opt.nDevNeighbourhood->key = "n_dev_neighbourhood";
    opt.nDevNeighbourhood->type = TYPE_INTEGER;
    opt.nDevNeighbourhood->required = YES;
    opt.nDevNeighbourhood->description =
        _("Size of square used to recalculate development pressure");

    opt.devpotParamsFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.devpotParamsFile->key = "devpot_params";
    opt.devpotParamsFile->required = YES;
    opt.devpotParamsFile->label =
        _("Development potential parameters for each region");
    opt.devpotParamsFile->description =
        _("Each line should contain region ID followed"
          " by parameters. Values are separated by whitespace (spaces or tabs)."
          " First line is ignored, so it can be used for header");

    opt.algorithm = G_define_option();
    opt.algorithm->key = "algorithm";
    opt.algorithm->type = TYPE_STRING;
    opt.algorithm->required = YES;
    opt.algorithm->options = "deterministic,stochastic1,stochastic2";
    opt.algorithm->description =
        _("Parameters controlling the algorithm to use");

    opt.dProbWeight = G_define_option();
    opt.dProbWeight->key = "prob_weight";
    opt.dProbWeight->type = TYPE_DOUBLE;
    opt.dProbWeight->required = NO;
    opt.dProbWeight->label = _("Parameters controlling the algorithm to use");
    opt.dProbWeight->description = _("(only relevant if nAlgorithm=2)"
                                     " the probabilities are multiplied"
                                     " by this factor before comparing with random numbers...increases randomness"
                                     " of the simulation as with probs like 0.95 is more or less deterministic");
    opt.dProbWeight->guisection = _("Stochastic 1");

    opt.dDevPersistence = G_define_option();
    opt.dDevPersistence->key = "dev_neighbourhood";
    opt.dDevPersistence->type = TYPE_DOUBLE;
    opt.dDevPersistence->required = NO;
    opt.dDevPersistence->label =
        _("Parameters controlling the algorithm to use");
    opt.dDevPersistence->description =
        _("(only relevant if nAlgorithm=2) the devPressures"
          " are multiplied by this factor on each timestep, meaning older development is"
          " downweighted and more recent development most important...should lead"
          " to clustering of new development");
    opt.dDevPersistence->guisection = _("Stochastic 1");

    opt.parcelSizeFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.parcelSizeFile->key = "parcel_size_file";
    opt.parcelSizeFile->required = YES;
    opt.parcelSizeFile->description =
        _("File containing information on the parcel size to use");

    opt.discountFactor = G_define_option();
    opt.discountFactor->key = "discount_factor";
    opt.discountFactor->type = TYPE_DOUBLE;
    opt.discountFactor->required = YES;
    opt.discountFactor->description = _("discount factor of patch size");

    opt.giveUpRatio = G_define_option();
    opt.giveUpRatio->key = "give_up_ratio";
    opt.giveUpRatio->type = TYPE_DOUBLE;
    opt.giveUpRatio->required = NO;
    opt.giveUpRatio->label = _("Give up ratio");
    opt.giveUpRatio->description = _("(only relevant if nAlgorithm=2) give up"
                                     " spiralling around when examined this factor of sites too many");
    opt.giveUpRatio->guisection = _("Stochastic 1");

    /* stochastic 2 algorithm */

    opt.probLookupFile = G_define_standard_option(G_OPT_F_INPUT);
    opt.probLookupFile->key = "probability_lookup_file";
    opt.probLookupFile->required = NO;
    opt.probLookupFile->label =
        _("File containing lookup table for probabilities");
    opt.probLookupFile->description =
        _("Format is tightly constrained. See documentation.");
    opt.probLookupFile->guisection = _("Stochastic 2");

    opt.sortProbs = G_define_option();
    opt.sortProbs->key = "sort_probs";
    opt.sortProbs->type = TYPE_INTEGER;
    opt.sortProbs->required = NO;
    opt.sortProbs->description =
        _("Whether or not to sort the list of undeveloped cells before choosing patch seeds");
    opt.sortProbs->guisection = _("Stochastic 2");

    opt.patchFactor = G_define_option();
    opt.patchFactor->key = "patch_factor";
    opt.patchFactor->type = TYPE_DOUBLE;
    opt.patchFactor->required = NO;
    opt.patchFactor->description =
        _("when building patches, multiply all probabilities by this"
          " factor (will controls shape of patches to some extent, with higher"
          " numbers more circular and lower numbers more linear)");
    opt.patchFactor->guisection = _("Stochastic 2");

    opt.patchMean = G_define_option();
    opt.patchMean->key = "patch_mean";
    opt.patchMean->type = TYPE_DOUBLE;
    opt.patchMean->required = NO;
    opt.patchMean->description =
        _("patch_mean and patch_range are now used to control patch shape");
    opt.patchMean->guisection = _("Stochastic 2");

    opt.patchRange = G_define_option();
    opt.patchRange->key = "patch_range";
    opt.patchRange->type = TYPE_DOUBLE;
    opt.patchRange->required = NO;
    opt.patchRange->description =
        _("patch_mean and patch_range are now used to control patch shape");
    opt.patchRange->guisection = _("Stochastic 2");

    opt.numNeighbors = G_define_option();
    opt.numNeighbors->key = "num_neighbors";
    opt.numNeighbors->type = TYPE_INTEGER;
    opt.numNeighbors->required = NO;
    opt.numNeighbors->options = "4,8";
    opt.numNeighbors->description =
        _("The number of neighbors to be used for patch generation (4 or 8)");
    opt.numNeighbors->guisection = _("Stochastic 2");

    opt.seedSearch = G_define_option();
    opt.seedSearch->key = "seed_search";
    opt.seedSearch->type = TYPE_INTEGER;
    opt.seedSearch->required = NO;
    opt.seedSearch->options = "1,2";
    opt.seedSearch->description =
        _("The way that the location of a seed is determined");
    opt.seedSearch->guisection = _("Stochastic 2");

    opt.devPressureApproach = G_define_option();
    opt.devPressureApproach->key = "development_pressure_approach";
    opt.devPressureApproach->type = TYPE_INTEGER;
    opt.devPressureApproach->required = NO;
    opt.devPressureApproach->options = "1,2,3";
    opt.devPressureApproach->description =
        _("approaches to derive development pressure");
    opt.devPressureApproach->guisection = _("Stochastic 2");

    opt.alpha = G_define_option();
    opt.alpha->key = "alpha";
    opt.alpha->type = TYPE_DOUBLE;
    opt.alpha->required = NO;
    opt.alpha->description =
        _("Required for development_pressure_approach 1 and 2");
    opt.alpha->guisection = _("Stochastic 2");

    opt.scalingFactor = G_define_option();
    opt.scalingFactor->key = "scaling_factor";
    opt.scalingFactor->type = TYPE_DOUBLE;
    opt.scalingFactor->required = NO;
    opt.scalingFactor->description =
        _("Required for development_pressure_approach 2 and 3");
    opt.scalingFactor->guisection = _("Stochastic 2");

    opt.num_Regions = G_define_option();
    opt.num_Regions->key = "num_regions";
    opt.num_Regions->type = TYPE_INTEGER;
    opt.num_Regions->required = NO;
    opt.num_Regions->description =
        _("Number of sub-regions (e.g., counties) to be simulated");
    opt.num_Regions->guisection = _("Stochastic 2");

    opt.indexFile = G_define_standard_option(G_OPT_R_INPUT);
    opt.indexFile->key = "index_file";
    opt.indexFile->required = NO;
    opt.indexFile->description = _("File for index of sub-regions");
    opt.indexFile->guisection = _("Stochastic 2");

    opt.controlFileAll = G_define_standard_option(G_OPT_F_INPUT);
    opt.controlFileAll->key = "control_file_all";
    opt.controlFileAll->required = NO;
    opt.controlFileAll->description =
        _("Control file with number of cells to convert");
    opt.controlFileAll->guisection = _("Stochastic 2");

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
        _("State of the development at after each step");
    opt.outputSeries->guisection = _("Output");
    // TODO: add mutually exclusive?
    // TODO: add flags or options to control values in series and final rasters

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

    /* parameters dependednt on region */
    sParams.xSize = Rast_window_rows();
    sParams.ySize = Rast_window_cols();
    G_message(_("Running on %d rows and %d columns (%d cells)"),
              sParams.xSize, sParams.ySize, sParams.xSize * sParams.ySize);

    /* set up parameters */
    sParams.controlFile = opt.controlFile->answer;
    sParams.undevelopedFile = opt.undevelopedFile->answer;
    sParams.employAttractionFile = opt.employAttractionFile->answer;
    sParams.interchangeDistanceFile = opt.interchangeDistanceFile->answer;
    sParams.roadDensityFile = opt.roadDensityFile->answer;
    sParams.devPressureFile = opt.devPressureFile->answer;
    sParams.consWeightFile = opt.consWeightFile->answer;
    sParams.numAddVariables = 0;
    char **answer = opt.addVariableFiles->answers;
    size_t num_answers = 0;

    while (opt.addVariableFiles->answers[num_answers]) {
        sParams.addVariableFile[num_answers] = *answer;
        num_answers++;
    }
    sParams.numAddVariables = num_answers;
    // TODO: dyn allocate file list
    sParams.nDevNeighbourhood = atoi(opt.nDevNeighbourhood->answer);

    sParams.dumpFile = opt.dumpFile->answer;
    sParams.outputSeries = opt.outputSeries->answer;

    sParams.parcelSizeFile = opt.parcelSizeFile->answer;

    sParams.discountFactor = atof(opt.discountFactor->answer);

    // always 1 if not stochastic 2
    sParams.sortProbs = 1;

    // TODO: implement real switching of algorithm
    if (!strcmp(opt.algorithm->answer, "deterministic"))
        sParams.nAlgorithm = _N_ALGORITHM_DETERMINISTIC;
    else if (!strcmp(opt.algorithm->answer, "stochastic1"))
        sParams.nAlgorithm = _N_ALGORITHM_STOCHASTIC_I;
    else if (!strcmp(opt.algorithm->answer, "stochastic2"))
        sParams.nAlgorithm = _N_ALGORITHM_STOCHASTIC_II;

    if (sParams.nAlgorithm == _N_ALGORITHM_STOCHASTIC_I) {
        // TODO: add check of filled answer
        sParams.dProbWeight = atof(opt.dProbWeight->answer);
        sParams.dDevPersistence = atof(opt.dDevPersistence->answer);

        sParams.giveUpRatio = atof(opt.giveUpRatio->answer);
    }
    else if (sParams.nAlgorithm == _N_ALGORITHM_STOCHASTIC_II) {

        int parsedOK, i;
        FILE *fp;
        char inBuff[N_MAXREADINLEN];
        char *pPtr;

        fprintf(stdout, "reading probability lookup\n");
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
                fprintf(stderr,
                        "error parsing probLookup file '%s'...exiting\n",
                        sParams.probLookupFile);
                return 0;
            }
            fclose(fp);
        }
        else {
            perror("The following error occurred");
            fprintf(stderr, "error opening probLookup file '%s'...exiting\n",
                    sParams.probLookupFile);
            return 0;
        }

        sParams.sortProbs = atoi(opt.sortProbs->answer);
        sParams.patchFactor = atof(opt.patchFactor->answer);
        sParams.patchMean = atof(opt.patchMean->answer);
        sParams.patchRange = atof(opt.patchRange->answer);
        sParams.numNeighbors = atoi(opt.numNeighbors->answer);
        // TODO: convert to options or flag: 1: uniform distribution 2: based on dev. proba.
        sParams.seedSearch = atoi(opt.seedSearch->answer);
        sParams.devPressureApproach = atoi(opt.devPressureApproach->answer);
        if (sParams.devPressureApproach != 1) {
            sParams.alpha = atof(opt.alpha->answer);
            sParams.scalingFactor = atof(opt.scalingFactor->answer);
        }

        sParams.num_Regions = atoi(opt.num_Regions->answer);
        sParams.indexFile = opt.indexFile->answer;
        sParams.controlFileAll = opt.controlFileAll->answer;
    }

    if (sParams.num_Regions > 1)
        readDevPotParams(&sParams, opt.devpotParamsFile->answer);

    readDevDemand(&sParams);
    /* allocate memory */
    if (buildLandscape(&sLandscape, &sParams)) {
        /* read data */
        if (readData(&sLandscape, &sParams)) {
            readData4AdditionalVariables(&sLandscape, &sParams);
            readIndexData(&sLandscape, &sParams);
            if (readParcelSizes(&sLandscape, &sParams)) {
                //testDevPressure(&sLandscape, &sParams);
                /* do calculation and dump result */
                //one region, enable the following
                //updateMap(&sLandscape, &sParams);

                //multiple regions
                updateMapAll(&sLandscape, &sParams);
            }
            else {
                fprintf(stderr, "error in readParcelSizes()\n");
            }
        }
        else {
            fprintf(stderr, "error in readData()\n");
        }
        /* could put in routines to free memory, but OS will garbage collect anyway */
    }
    else {
        fprintf(stderr, "error in buildLandscape()\n");
    }

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

    G_verbose_message(_("getUnDevIndex1: regionID=%d, num_undevSites=%d, p=%f"),
                      regionID, pLandscape->num_undevSites[regionID], p);
    int i;

    for (i = 0; i < pLandscape->num_undevSites[regionID]; i++) {
        if (p < pLandscape->asUndevs[regionID][i].cumulProb) {
            G_verbose_message(_("getUnDevIndex1: cumulProb=%f"),
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
    fprintf(stdout, "\t\trecalculating probabilities\n");
    for (i = 0; i < pParams->num_Regions; i++) {
        pLandscape->num_undevSites[i] = 0;
    }
    float val = 0.0;

    for (i = 0; i < pLandscape->totalCells; i++) {
        pThis = &(pLandscape->asCells[i]);
        if (pThis->nCellType == _CELL_VALID) {
            if (pThis->bUndeveloped) {
                if (pThis->consWeight > 0.0) {
                    id = pThis->index_region - 1;
                    if (pThis->index_region == -9999)
                        continue;
                    /* note that are no longer just storing the logit value,
                       but instead the probability
                       (allows consWeight to affect sort order) */

                    if (id < 0 || id >= pParams->num_Regions)
                        G_fatal_error(_("Index of region %d is out of range [0, %d] (region is %d)"),
                                      id, pParams->num_Regions - 1,
                                      pThis->index_region);

                    if (pLandscape->num_undevSites[id] >=
                        pLandscape->asUndevs[id].size())
                        pLandscape->asUndevs[id].resize(pLandscape->
                                                        asUndevs[id].size() *
                                                        2);

                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].
                        cellID = i;
                    val = getDevProbability(pThis, pParams);
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].
                        logitVal = val;
                    G_verbose_message("logit value %f", val);
                    pThis->devProba = val;
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
                    pThis->devProba =
                        pLandscape->asUndevs[id][pLandscape->
                                                 num_undevSites[id]].logitVal;
                    // discount by a conservation factor
                    pLandscape->asUndevs[id][pLandscape->num_undevSites[id]].logitVal *= pThis->consWeight;
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
    /* downweight the devPressure if necessary (do not do in first step) */
    /* doing it here means that last time step values have full weight */
    if (pParams->nAlgorithm == _N_ALGORITHM_STOCHASTIC_I) {
        if (pParams->dDevPersistence < 1.0) {
            fprintf(stdout, "\t\tdownweighting development pressure\n");

            for (i = 0; i < pLandscape->totalCells; i++) {
                pThis = &(pLandscape->asCells[i]);
                if (pThis->nCellType == _CELL_VALID) {
                    /* only need to bother downweighting on cells that can still convert */
                    if (pThis->bUndeveloped) {
                        pThis->devPressure =
                            (int)((double)pThis->devPressure *
                                  pParams->dDevPersistence);
                    }
                }
            }
        }
    }
    /* sort */
    /* can only be zero for algorithm=stochastic_ii */
    if (pParams->sortProbs) {
        fprintf(stdout, "\t\tsorting %d unconserved undeveloped sites\n",
                pLandscape->undevSites);
        qsort(pLandscape->asUndev, pLandscape->undevSites, sizeof(t_Undev),
              undevCmpReverse);
    }
    else {
        fprintf(stdout, "\t\tskipping sort as choosing cells randomly\n");
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
