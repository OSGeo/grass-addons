/* File: set_grid.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <string.h>
#include <math.h>
#include "grids.h"
#include "conversion.h"
#include "ps_info.h"
#include "local_proto.h"


/*
 * LINES OF THE GRATICULE
 */

int set_lines_grid(void)
{
    fprintf(PS.fp, "/XY {get aload pop exch pop} D\n");

    set_grid_lines('m', &(PS.grid.mline), PS.grid.msep);
    set_grid_lines('M', &(PS.grid.line), PS.grid.sep);
}

int set_grid_lines(char code, PSLINE * line, int grid_sep)
{
    char label[50], h;
    int i, x, y, zero;
    double sep, north, west, dx, dy;

    if (grid_sep <= 0)
        return 0;

    /* detect max trailer zeros if format zero and not LL */
    zero = 1;
    if (PS.map.proj == PROJECTION_LL)
    {
        sep = (double)grid_sep / 3600.;
    }
    else
    {
        sep = (double)grid_sep;
        if (PS.grid.format < 3 && PS.grid.round > 0) {
            while (PS.grid.sep % zero == 0) zero *= 10;
            if (zero > 1)
            {
                zero /= 10;
                for (i=0, x=1; i < PS.grid.round; i++)  x *= 10;
                if (zero > x) zero = x;
            }
        }
    }

    /* vertical numbers */
    fprintf(PS.fp, "/VGR%c [\n", code);
    north = floor(PS.map.north / sep) * sep;
    for (; north >= PS.map.south; north -= sep)
    {
        G_plot_where_xy(PS.map.east, north, &x, &y);
        dy = ((double)y) / 10.;
        G_format_northing(north/zero, label, PS.map.proj);
        fprintf(PS.fp, "[(%s) %.1f]\n", label, dy);
    }
    fprintf(PS.fp, "] def\n");

    /* horizontal numbers */
    fprintf(PS.fp, "/HGR%c [\n", code);
    west = ceil(PS.map.west / sep) * sep;
    for (; west < PS.map.east; west += sep)
    {
        G_plot_where_xy(west, PS.map.south, &x, &y);
        dx = ((double)x) / 10.;
        G_format_easting(west/zero, label, PS.map.proj);
        fprintf(PS.fp, "[(%s) %.1f]\n", label, dx);
    }
    fprintf(PS.fp, "] def\n");


    if (line->color.none != 1)
    {
        set_ps_line(line);
        if (PS.grid.cross <= 0.) /* draw lines */
        {
            fprintf(PS.fp,
                "VGR%c 0 1 2 index length -- {1 index exch XY "
                "%.1f exch dup %.1f exch M LS} for pop\n", code, PS.map_x, PS.map_right);
            fprintf(PS.fp,
                "HGR%c 0 1 2 index length -- {1 index exch XY "
                "%.1f 1 index %.1f M LS} for pop\n", code, PS.map_y, PS.map_top);
        }
        else /* draw crosses */
        {
            G_plot_where_xy(PS.map.east, PS.map.north, &x, &y);
            dx = ((double)x) / 10.;
            G_plot_where_xy(PS.map.east - PS.grid.cross, PS.map.north, &x, &y);
            dy = ((double)x) / 10.;

            fprintf(PS.fp,
                    "VGR%c 0 1 2 index length -- {1 index exch XY "
                    "HGR%c 0 1 2 index length -- {1 index exch XY "
                    "2 index M 0 90 270 {GS ROT 0 %.1f LRS GR} for} "
                    "for pop pop} for pop\n", code, code, dx-dy);
        }
    }
    /* draw crosses como rotate una longitud desde el punto central*/
    return 0;
}

/*
 * NUMBERS OF THE GRATICULE
 */

int set_numbers_grid(void)
{
    /* make fine border */
    set_ps_color(&(PS.grid.fcolor));
    set_ps_brd(.2*MM_TO_POINT, 0.);

    /* make numbers */
    switch (PS.grid.format)
    {
        case 0:
            set_grid_inner_numbers();
            break;
        case 1:
            set_grid_minor_border(0., PS.brd.width, PS.brd.width);
            set_grid_outer_numbers();
            break;
        case 2:
            set_grid_fine_border (0.2*MM_TO_POINT, 0.8*MM_TO_POINT);
            set_grid_minor_border(1.0*MM_TO_POINT, 1.2*MM_TO_POINT, 0.2*MM_TO_POINT);
            set_grid_major_border(2.2*MM_TO_POINT, 9.5*MM_TO_POINT);
            set_grid_iho_numbers();
            break;
    }
    return 1;
}


/* FORMAT 0: inner numbers */
int set_grid_inner_numbers(void)
{
    fprintf(PS.fp, "GS\n");
    fprintf(PS.fp, "/m %.3f def \n", 0.2 * PS.grid.font.size);

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.1f exch M ", PS.map_x);
    if (PS.grid.fcolor.none) {
        fprintf(PS.fp, ".5 .5 MR ");
    }
    else  {
        fprintf(PS.fp,
                "dup SWH m 2 mul add exch m 1 add add exch "
                "dup 2 div neg 0 exch MR GS ");
        set_ps_color(&(PS.grid.fcolor));
        fprintf(PS.fp, "Rf GR 1 m MR ");
    }
    fprintf(PS.fp, "show} for\n");

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.1f M ", PS.map_top);
    if (PS.grid.fcolor.none) {
        fprintf(PS.fp, "dup SW .5 add neg -.5 exch MR ");
    }
    else  {
        fprintf(PS.fp,
                "dup SWH m 2 mul add exch m 1 add add "
                "1 index 2 div 1 index neg MR exch neg exch GS ");
        set_ps_color(&(PS.grid.fcolor));
        fprintf(PS.fp, "Rf GR m neg m MR ");
    }
    fprintf(PS.fp, "GS 90 ROT show GR} for\n");

    fprintf(PS.fp, "GR\n");
    return 0;
}


/* FORMAT 1: outer numbers */
int set_grid_outer_numbers(void)
{
    fprintf(PS.fp, "GS\n");

    set_ps_font(&(PS.grid.font));

    /* vertical numbers */
    fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch GET %.1f exch M ", PS.map_x);
    fprintf(PS.fp, "dup SW -2 div -%.2f exch MR ", PS.brd.width+1.);
    fprintf(PS.fp, "GS 90 ROT show GR} for\n");

    /* horizontal numbers */
    fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch GET %.1f M ", PS.map_top);
    fprintf(PS.fp, "dup SW -2 div %.2f MR ", PS.brd.width+1.);
    fprintf(PS.fp, "show} for\n");

    fprintf(PS.fp, "GR\n");
    return 0;
}

/* FORMAT 2: I.H.O. numbers */
int set_grid_iho_numbers(void)
{
//     fprintf(PS.fp, "GS\n");
//     fprintf(PS.fp, "/m %.3f def \n", 0.2 * PS.grid.font.size);
//
//     set_ps_font(&(PS.grid.font));
//
//     /* vertical numbers */
//     fprintf(PS.fp, "0 1 VGRM length -- {VGRM exch get aload pop %.1f exch M ", PS.map_x);
//     fprintf(PS.fp, "dup SW -2 div -%.2f exch MR ", PS.brd.width+1.);
//     fprintf(PS.fp, "GS 90 ROT show GR} for\n");
//
//     /* horizontal numbers */
//     fprintf(PS.fp, "0 1 HGRM length -- {HGRM exch get aload pop %.1f M ", PS.map_top);
//     fprintf(PS.fp, "dup SW -2 div %.2f MR ", PS.brd.width+1.);
//     fprintf(PS.fp, "show} for\n");
//
//     fprintf(PS.fp, "GR\n");
    return 0;
}

/*
 * BORDER TYPES OF THE GRATICULE
 */

int set_grid_fine_border(double margin, double width)
{
    int div;

    div = (PS.map.proj == PROJECTION_LL) ? 6 : 10;

    set_ps_brd(.2*MM_TO_POINT, margin+width);
    set_grid_corners(margin, width);

    fprintf(PS.fp,
            "1 1 VGRm length -- {dup VGRm exch XY exch -- VGRm exch XY "
            "1 index sub %d div exch "
            "%d {dup %.1f exch M %.2f 0 LR dup %.1f exch M %.2f 0 LR S "
            "1 index add} repeat pop pop} for ",
            div, div, PS.map_x-margin, -width, PS.map_right+margin, width);

    fprintf(PS.fp,
            "1 1 HGRm length -- {dup HGRm exch XY exch -- HGRm exch XY "
            "1 index sub %d div exch "
            "%d {dup %.1f M 0 %.2f LR dup %.1f M 0 %.2f LR S "
            "1 index add} repeat pop pop} for ",
            div, div, PS.map_y-margin, -width, PS.map_top+margin, width);

    fprintf(PS.fp,
            "VGRm 0 XY VGRm 1 XY 1 index sub neg "
            "%d div exch {dup %.1f gt {exit} "
            "{dup %.1f exch M %.2f 0 LR dup %.1f exch M %.2f 0 LR S 1 index add} ifelse} loop ",
            div, PS.map_top, PS.map_x-margin, -width, PS.map_right+margin, width);

    fprintf(PS.fp,
            "/i VGRm length -- def "
            "VGRm i XY VGRm i -- XY "
            "1 index sub neg %d div exch {dup %.1f lt {exit} "
            "{dup %.1f exch M %.2f 0 LR dup %.1f exch M %.2f 0 LR S 1 index add} ifelse} loop ",
            div, PS.map_y, PS.map_x-margin, -width, PS.map_right+margin, width);

    fprintf(PS.fp,
            "HGRm 0 XY HGRm 1 XY 1 index sub neg "
            "%d div exch {dup %.1f lt {exit} "
            "{dup %.1f M 0 %.2f LR dup %.1f M 0 %.2f LR S 1 index add} ifelse} loop ",
            div, PS.map_x, PS.map_y-margin, -width, PS.map_top+margin, width);

    fprintf(PS.fp,
            "/i HGRm length -- def "
            "HGRm i XY HGRm i -- XY "
            "1 index sub neg %d div exch {dup %.1f gt {exit} "
            "{dup %.1f M 0 %.2f LR dup %.1f M 0 %.2f LR S} ifelse 1 index add} loop\n",
            div, PS.map_right, PS.map_y-margin, -width, PS.map_top+margin, width);
}

int set_grid_minor_border(double margin, double width, double midline)
{
    double dist;

    dist = margin + width/2. + .1*MM_TO_POINT;

    set_ps_brd(.2*MM_TO_POINT, margin+width);

    fprintf(PS.fp, ".2 mm LW ");
    set_grid_corners(margin, width);

    fprintf(PS.fp,
            "0 1 VGRm length -- {VGRm exch XY dup "
            "%.1f exch M %.2f 0 LR %.1f exch M %.2f 0 LRS} for\n",
            PS.map_x-margin, -width, PS.map_right+margin, width);

    fprintf(PS.fp,
            "0 1 HGRm length -- {HGRm exch XY dup "
            "%.1f M %.2f 0 exch LR %.1f M %.2f 0 exch LRS} for\n",
            PS.map_y-margin, -width, PS.map_top+margin, width);


    fprintf(PS.fp, "%.1f LW ", midline);

    fprintf(PS.fp,
            "1 2 VGRm length -- {/i XD VGRm i XY VGRm i -- XY 2 copy "
            "%.1f exch M cP pop exch LS %.1f exch M cP pop exch LS} for\n",
            PS.map_x-dist, PS.map_right+dist);

    fprintf(PS.fp,
            "1 2 HGRm length -- {/i XD HGRm i XY HGRm i -- XY 2 copy "
            "%.1f M cP exch pop LS %.1f M cP exch pop LS} for\n",
            PS.map_y-dist, PS.map_top+dist);

    fprintf(PS.fp,
            "VGRm length 2 mod 0 ne {VGRm dup length -- XY %.1f 2 copy "
                    "%.1f exch M cP pop exch LS %.1f exch M cP pop exch LS} if\n",
                    PS.map_y, PS.map_x-dist, PS.map_right+dist);

    fprintf(PS.fp,
            "HGRm length 2 mod 0 ne {HGRm dup length -- XY %.1f 2 copy "
            "%.1f M cP exch pop LS %.1f M cP exch pop LS} if\n",
            PS.map_right, PS.map_y-dist, PS.map_top+dist);
}

int set_grid_major_border(double margin, double width)
{
    set_ps_brd(.8*MM_TO_POINT, margin+width);

    fprintf(PS.fp, ".2 mm LW ");

    fprintf(PS.fp,
            "0 1 VGRM length -- {VGRM exch XY dup "
            "%.1f exch M %.2f 0 LR %.1f exch M %.2f 0 LR S} for\n",
            PS.map_x-margin, -width, PS.map_right+margin, width);

    fprintf(PS.fp,
            "0 1 HGRM length -- {HGRM exch XY dup "
            "%.1f M %.2f 0 exch LR %.1f M %.2f 0 exch LR S} for\n",
            PS.map_y-margin, -width, PS.map_top+margin, width);
}


int set_grid_corners(double margin, double width)
{
    fprintf(PS.fp, "%.1f %.1f M %.2f 0 LRS ", PS.map_x-margin, PS.map_y, -width);
    fprintf(PS.fp, "%.1f %.1f M 0 %.2f LRS ", PS.map_x, PS.map_y-margin, -width);

    fprintf(PS.fp, "%.1f %.1f M %.2f 0 LRS ", PS.map_x-margin, PS.map_top, -width);
    fprintf(PS.fp, "%.1f %.1f M 0 %.2f LRS ", PS.map_x, PS.map_top+margin, width);

    fprintf(PS.fp, "%.1f %.1f M %.2f 0 LRS ", PS.map_right+margin, PS.map_y, width);
    fprintf(PS.fp, "%.1f %.1f M 0 %.2f LRS ", PS.map_right, PS.map_y-margin, -width);

    fprintf(PS.fp, "%.1f %.1f M %.2f 0 LRS ", PS.map_right+margin, PS.map_top, width);
    fprintf(PS.fp, "%.1f %.1f M 0 %.2f LRS ", PS.map_right, PS.map_top+margin, width);
}

