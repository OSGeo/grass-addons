#ifndef _PS3_INFO_H_
#define _PS3_INFO_H_

/* File: ps_info.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include <grass/gis.h>
#include "lines.h"
#include "colors.h"
#include "notes.h"
#include "papers.h"
#include "raster.h"
#include "rlegend.h"
#include "vector.h"
#include "vlegend.h"
#include "grids.h"
#include "scalebar.h"
#include "draws.h"
#include "conversion.h"

#define MAX_NOTES   10

struct PS3_info
{
    FILE *fp;
    int level;			/* PostScript level: 0 = EPS */
    int flag;			/* 1 = GhostScript, 2 = Upper numbers */
    int draft;			/* Grid of 1x1 cm */
    char *mapset;		/* current mapset */
    struct Cell_head map;	/* current region */

    int scale;			/* 1 : scale of the map */
    PSFONT font;		/* default font of map */

    /* rasters */
    RASTER rst;
    int need_mask;
    RLEGEND rl;
    int do_rlegend;

    /* vectors */
    VECTOR *vct;
    int vct_files;
    VLEGEND vl;
    int do_vlegend;

    /* border, grids, and scales */
    PSCOLOR fcolor;
    PSLINE brd;
    int do_border;
    GRID grid;
    GRID geogrid;
    SCALEBAR sbar;

    /* notes */
    NOTES note[MAX_NOTES];	/* notes */
    int n_notes;		/* number of notes */

    /* draw commands */
    PSDRAW draw;
    int n_draws;

    /* dimensions of the page */
    PAPER page;

    /* dimension and location of the map */
    double x, y;
    double map_x, map_y, map_w, map_h;
    double map_top, map_right;

};

#endif

#ifdef MAIN
struct PS3_info PS;
int sec_draw;			/* used in PS_plot */
#else
extern struct PS3_info PS;
extern int sec_draw;
#endif
