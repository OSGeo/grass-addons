/****************************************************************************
 *
 * MODULE:       r.soils.texture
 * AUTHOR(S):    Gianluca Massei (g_massa@libero.it)
 * PURPOSE:      Intended to define soil texture from sand and clay grid.
 *                 Require texture scheme supplied in scheme directory
 *
 * COPYRIGHT:    (C) 2008 by Gianluca MAssei and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "local_include.h"

/* global function declaration */
extern CELL f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

CELL c_calc(CELL c_sand, CELL c_clay, struct TextureTriangleCoord *punt_lista,
            int *numPoly)
{
    /*                           */
    CELL out;
    int polygons;

    polygons = *numPoly;
    out = ReadList(punt_lista, &polygons, c_sand, c_clay);
    return out;
}

FCELL f_calc(FCELL f_sand, FCELL f_clay,
             struct TextureTriangleCoord *punt_lista, int *numPoly)
{
    /*                           */
    FCELL out;
    int polygons;

    polygons = *numPoly;
    out = ReadList(punt_lista, &polygons, f_sand, f_clay);
    return out;
}

DCELL d_calc(DCELL d_sand, DCELL d_clay,
             struct TextureTriangleCoord *punt_lista, int *numPoly)
{
    /*                          */
    DCELL out;
    int polygons;

    polygons = *numPoly;
    out = ReadList(punt_lista, &polygons, d_sand, d_clay);
    return out;
}

/*
 * main function
 * it copies raster inputSand raster file, calling the appropriate function for
 * each data type (CELL, DCELL, FCELL)
 */
int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /* it stores region information, and header
                                information of rasters */
    char *SandName, *ClayName, *SchemeName; /* inputSand raster name */
    char *result;                           /* output raster name */
    char *mapsetSand, *mapsetClay;          /* mapset name */
    void *inrastSand, *inrastClay;          /* input buffer */
    unsigned char *outrast;                 /* output buffer */
    int nrows, ncols;
    int row, col;
    int infdSand, infdClay, outfd; /* file descriptor */
    int verbose;
    int polygons;
    RASTER_MAP_TYPE data_type_Sand, data_type_Clay,
        data_type;          /* type of the map (CELL/DCELL/...) */
    struct History history; /* holds meta-data (title, comments,..)*/
    struct GModule *module; /* GRASS module for parsing arguments */

    struct Option *inputSand, *inputClay, *inputTextureScheme,
        *output; /* options */

    struct TextureTriangleCoord *punt_lista;

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("soil"));
    G_add_keyword(_("texture"));
    module->description = _("Define soil texture from sand and clay grid.");

    /* Define the different options for SAND file */
    inputSand = G_define_standard_option(G_OPT_R_INPUT);
    inputSand->key = "sand";
    inputSand->description = _("Name of input sand map [0-100]");

    /* Define the different options for CLAY file */
    inputClay = G_define_standard_option(G_OPT_R_INPUT);
    inputClay->key = "clay";
    inputClay->description = _("Name of input clay map [0-100]");

    /*Define the texture file scheme: USDA, FAO, International or other scheme
     */
    inputTextureScheme = G_define_standard_option(G_OPT_F_INPUT);
    inputTextureScheme->key = "scheme";
    inputTextureScheme->description = _("Text file with texture scheme");

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    /* options and flags pareser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* stores options and flags to variables */
    SandName = inputSand->answer;
    ClayName = inputClay->answer;
    SchemeName = inputTextureScheme->answer;
    result = output->answer;

    /*************************************control sand
     * file*****************************/
    /* returns NULL if the map was not found in any mapset,
     * mapset name otherwise */
    mapsetSand = (char *)G_find_raster2(SandName, "");
    if (mapsetSand == NULL)
        G_fatal_error(_("cell file [%s] not found"), SandName);

    /* if (G_legal_filename(result) < 0)
         G_fatal_error(_("[%s] is an illegal name"), result);*/

    /* determine the input map type (CELL/FCELL/DCELL) */
    data_type_Sand = Rast_map_type(SandName, mapsetSand);

    /* G_open_cell_old - returns file destriptor (>0) */
    infdSand = Rast_open_old(SandName, mapsetSand);

    /* controlling, if we can open inputSand raster */
    Rast_get_cellhd(SandName, mapsetSand, &cellhd);
    G_debug(3, "number of rows %d", cellhd.rows);
    /*********************************control clay file
     * **********************************/

    /* returns NULL if the map was not found in any mapset,
     * mapset name otherwise */
    mapsetClay = (char *)G_find_raster2(ClayName, "");

    if (mapsetClay == NULL)
        G_fatal_error(_("cell file [%s] not found"), ClayName);

    /*if (G_legal_filename(result) < 0)
        G_fatal_error(_("[%s] is an illegal name"), result);*/

    /* determine the input map type (CELL/FCELL/DCELL) */
    data_type_Clay = Rast_map_type(ClayName, mapsetClay);

    /* G_open_cell_old - returns file destriptor (>0) */
    infdClay = Rast_open_old(ClayName, mapsetClay);

    /* controlling, if we can open inputClay raster */
    Rast_get_cellhd(ClayName, mapsetClay, &cellhd);

    G_debug(3, "number of rows %d", cellhd.rows);
    /**************************************************************************************/
    /* Allocate input buffer */
    inrastSand = Rast_allocate_buf(data_type_Sand);
    inrastClay = Rast_allocate_buf(data_type_Clay);

    /* Allocate output buffer, use input Sand map data_type */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_buf(data_type_Sand);
    data_type = data_type_Sand;

    /* controlling, if we can write the raster */
    outfd = Rast_open_new(result, data_type);

    punt_lista = ReadTriangle(
        &polygons,
        SchemeName); // read texture criteria file (es USDA.DAT) and buil a list
    CELL c_sand, c_clay, c;
    FCELL f_sand, f_clay, f;
    DCELL d_sand, d_clay, d;

    /* for each row */
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        /* read input Sand map */
        Rast_get_row(infdSand, inrastSand, row, data_type_Sand);
        /* read input Sand map */
        Rast_get_row(infdClay, inrastClay, row, data_type_Sand);

        /* process the data */
        for (col = 0; col < ncols; col++) {
            /* use different function for each data type */
            switch (data_type) {
            case CELL_TYPE:
                c_sand = ((CELL *)inrastSand)[col];
                c_clay = ((CELL *)inrastClay)[col];
                c = c_calc(c_sand, c_clay, punt_lista,
                           &polygons); /* calculate */
                ((CELL *)outrast)[col] = c;
                break;
            case FCELL_TYPE:
                f_sand = ((FCELL *)inrastSand)[col];
                f_clay = ((FCELL *)inrastClay)[col];
                f = f_calc(f_sand, f_clay, punt_lista,
                           &polygons); /* calculate */
                ((FCELL *)outrast)[col] = f;
                break;
            case DCELL_TYPE:
                d_sand = ((DCELL *)inrastSand)[col];
                d_clay = ((DCELL *)inrastClay)[col];
                d = d_calc(d_sand, d_clay, punt_lista,
                           &polygons); /* calculate */
                ((DCELL *)outrast)[col] = d;
                break;
            }
        }

        /* write raster row to output raster file */
        Rast_put_row(outfd, outrast, data_type);
    }

    /* memory cleanup */
    G_free(inrastSand);
    G_free(inrastClay);
    G_free(outrast);

    /* closing raster files */
    Rast_close(infdSand);
    Rast_close(infdClay);
    Rast_close(outfd);

    /* add command line incantation to history file */
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);

    reclassTexture(SchemeName, result);

    G_done_msg(_("Soil texture file generated with name: <%s>"), result);
    exit(EXIT_SUCCESS);
}

struct TextureTriangleCoord *ReadTriangle(int *numPoly, char *SchemeName)
{
    /*//////////// Declare Read Poly texture structure
     * //////////////////////////// */
    struct TextureTriangleCoord Triangle, *pTxt, *paus;

    pTxt = &Triangle; // pointer to struct
    /*//////////////////////////////////////////////////////////////////////////////
     */
    int i, j, polygons;
    FILE *fp_dat;

    fp_dat = fopen(SchemeName, "r");
    if (fp_dat == NULL) {
        printf("Could not read from <%s>", SchemeName);
    }

    fscanf(fp_dat, "%d", numPoly);
    polygons = *numPoly;

    if (polygons == 0) {
        pTxt = NULL; /*break if no polygons */
    }
    else {
        pTxt = (struct TextureTriangleCoord *)malloc(
            sizeof(struct TextureTriangleCoord)); /*first struct PolygonCoord */
        fscanf(fp_dat, "%d", &pTxt->codeTexture);
        fscanf(fp_dat, "%d", &pTxt->numVertex);

        for (j = 0; j < (pTxt->numVertex);
             j++) { // fill sand array with coord. polygons array
            fscanf(fp_dat, "%f", &pTxt->xSand[j]);
        }
        for (j = 0; j < (pTxt->numVertex);
             j++) { // fill clay array with coord. polygons array
            fscanf(fp_dat, "%f", &pTxt->yClay[j]);
        }
        paus = pTxt;

        for (i = 2; i <= polygons; i++) {
            paus->PointToNext = (struct TextureTriangleCoord *)malloc(
                sizeof(struct TextureTriangleCoord));
            paus = paus->PointToNext;
            fscanf(fp_dat, "%d", &paus->codeTexture);
            fscanf(fp_dat, "%d", &paus->numVertex);
            for (j = 0; j < (paus->numVertex);
                 j++) { // fill sand array with coord. polygons array
                fscanf(fp_dat, "%f", &paus->xSand[j]);
            }
            for (j = 0; j < (paus->numVertex);
                 j++) { // fill clay array with coord. polygons array
                fscanf(fp_dat, "%f", &paus->yClay[j]);
            }
        }

        paus->PointToNext = NULL;
    }
    fclose(fp_dat);
    return (pTxt);
}

int ReadList(struct TextureTriangleCoord *pTxt, int *numPoly, float SandVal,
             float ClayVal)
{
    int polygons, textureOUT;

    textureOUT = 0;
    polygons = *numPoly;
    while (pTxt != NULL && textureOUT == 0) {
        textureOUT = DefineTexture(pTxt->numVertex, pTxt->xSand, pTxt->yClay,
                                   SandVal, ClayVal, pTxt->codeTexture);
        pTxt = pTxt->PointToNext;
    }

    return textureOUT;
}

int DefineTexture(int numVert, float *xSand, float *yClay, float SandVal,
                  float ClayVal, int codeTxt)
{
    int i, j, textureVER = 0;

    for (i = 0, j = numVert - 1; i < numVert; j = i++) {
        if ((((yClay[i] <= ClayVal) && (ClayVal < yClay[j])) ||
             ((yClay[j] <= ClayVal) && (ClayVal < yClay[i]))) &&
            (SandVal <= (xSand[j] - xSand[i]) * (ClayVal - yClay[i]) /
                                (yClay[j] - yClay[i]) +
                            xSand[i]))
            textureVER = !textureVER;
    }

    if (textureVER == 1) {
        textureVER = codeTxt;
    }
    else {
        textureVER = 0;
    }
    return textureVER;
}

void reclassTexture(char *SchemeName, char *result)
{ /*reclass texture file with label in scheme file */

    int control, i;
    char c, tag[1024];

    struct label_struct label, *plabel;
    struct Categories pcats;

    FILE *fp_dat;
    DCELL dcat;

    fp_dat = fopen(SchemeName, "r");
    plabel = &label;

    Rast_init_cats("", &pcats); /*Initialize category structure. */
    if (Rast_read_cats(result, G_mapset(), &pcats) <
        0) /*read raster category file */
        G_fatal_error(("%s: %s in %s - can't read category file"),
                      G_program_name(), result, G_mapset());

    if (fp_dat == NULL) {
        G_fatal_error(_("Could not open <%s>"), SchemeName);
    }

    fscanf(fp_dat, "%d", &control);

    while (c != '#') {
        fscanf(fp_dat, "%c", &c);
    }

    sprintf(tag, "NULL");
    /*set a category label. The label is copied into the cats structure for
     * category n. */
    Rast_set_d_cat(&dcat, &dcat, tag, &pcats);
    for (i = 1; i <= control; i++) {
        dcat = (double)i;
        fscanf(fp_dat, "%s", &plabel->etichetta);
        sprintf(tag, "%s", plabel->etichetta);
        Rast_set_d_cat(&dcat, &dcat, tag, &pcats);
    }

    Rast_write_cats(result, &pcats);

    fclose(fp_dat);
    /*return (0); */
}
