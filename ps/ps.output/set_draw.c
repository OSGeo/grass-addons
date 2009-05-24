/* File: set_draw.c
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
#include <grass/symbol.h>
#include <grass/gprojects.h>
#include "colors.h"
#include "ps_info.h"

#define PI   3.14159265359

#define KEY(x) (strcmp(x,key)==0)

int set_draw(char * key, char *data)
{
    char label[100], buf[256];
    int i;
    double d, lw, e1, e2, n1, n2;
    PSCOLOR color;

    if (KEY("direct"))
    {
        fprintf(PS.fp, " %s ", data);
    }
    else if (KEY("color"))
    {
        set_color_name(&color, data);
        set_ps_color(&color);
    }
    else if (KEY("font"))
    {
        i = sscanf(data, "%s %s %lf", label, buf, &d);
        if (i != 2 && i != 3)
        {
            error(key, data, "font need 2 or 3 parameters (name, size, and [extend])");
        }
        if (scan_dimen(buf, &lw) != 1) {
            error(key, data, "size not valid (font)");
        }
        fprintf(PS.fp, "(%s) FN %.1f ", label, lw);
        if (i == 2 )
            fprintf(PS.fp, "FS ");
        else
            fprintf(PS.fp, "%.2f FE ", d);
    }
    else if (KEY("text"))
    {
        if (sscanf(data, "%lf %lf %[^\n]", &e1, &n1, label) != 3) {
            error(key, data, "text need 3 parameters (east, north and text)");
        }
        set_xy_where("", e1, n1, "M ");
        fprintf(PS.fp, "(%s) SHCC\n", label);
    }
    else if (KEY("moveto"))
    {
        if (sscanf(data, "%s %lf %lf", label, &e1, &n1) != 3) {
            error(key, data, "moveto need 3 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (line)");
        }
        fprintf(PS.fp, "%.1f LW", lw);
        set_xy_where("", e1, n1, "M ");
    }
    else if (KEY("lineto"))
    {
        if (sscanf(data, "%lf %lf", &e1, &n1) != 2) {
            error(key, data, "lineto need 2 parameters (east and north)");
        }
        set_xy_where("", e1, n1, "L ");
    }
    else if (KEY("endto"))
    {
        if (sscanf(data, "%lf %lf", &e1, &n1) != 2) {
            error(key, data, "endto need 2 parameters");
        }
        set_xy_where("", e1, n1, "LS\n");
    }
    else if (KEY("line"))
    {
        if (sscanf(data, "%s %lf %lf %lf %lf", label, &e1, &n1, &e2, &n2) != 5) {
            error(key, data, "line need 5 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (line)");
        }
        fprintf(PS.fp, "%.1f LW", lw);
        set_xy_where("", e1, n1, "M");
        set_xy_where("", e2, n2, "LS\n");
    }
    else if (KEY("rect") || KEY("rectangle"))
    {
        if (sscanf(data, "%s %lf %lf %lf %lf", label, &e1, &n1, &e2, &n2) != 5) {
            error(key, data, "rectangle need 5 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (rectangle)");
        }
        fprintf(PS.fp, "%.1f LW", lw);
        set_xy_where("", e1, n1, "");
        set_xy_where("", e2, n2, "B S\n");
    }
    else if (KEY("circ") || KEY("circle"))
    {
        if (sscanf(data, "%s %lf %lf %lf", label, &e1, &n1, &d) != 4) {
            error(key, data, "circle need 4 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (circle)");
        }
        d *= (MT_TO_POINT / (double)PS.scale);
        fprintf(PS.fp, "%.1f LW", lw);
        set_xy_where("", e1, n1, "");
        fprintf(PS.fp, "%.1f 0 360 arc S\n", d);
    }
    else if (KEY("arc"))
    {
        if (sscanf(data, "%s %lf %lf %lf %lf %lf", label, &e1, &n1, &d, &e2, &n2) != 6) {
            error(key, data, "arc need 6 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (circle)");
        }
        d *= (MT_TO_POINT / (double)PS.scale);
        fprintf(PS.fp, "%.1f LW", lw);
        set_xy_where("", e1, n1, "");
        fprintf(PS.fp, "%.1f %.1f %.1f arc S\n", d, e2, n2);
    }
    else if (KEY("psfile"))
    {
        FILE *fp;
        if ((fp = fopen(data, "r")) != NULL)
        {
            G_message("Reading PostScript include file <%s> ...", data);
            fprintf(PS.fp, "\n");
            while (fgets(buf, 256, fp) != NULL)
                fprintf(PS.fp, "%s", buf);
            fprintf(PS.fp, "\n");
            fclose(fp);
        }
    }
    else if (KEY("limit") || KEY("limits"))
    {
        fprintf(PS.fp, "%.1f %.1f M ", PS.map_right, PS.map_top);
        G_format_northing(PS.map.north, label, PS.map.proj);
        fprintf(PS.fp, "GS (%s) dup SWH ++ neg dup MR pop SHR GR\n", label);
        G_format_easting(PS.map.east, label, PS.map.proj);
        fprintf(PS.fp, "GS (%s) dup SWH ++ dup neg 3 1 roll add neg MR 270 ROT SHR GR\n", label);
        fprintf(PS.fp, "%.1f %.1f M ", PS.map_x, PS.map_y);
        G_format_easting(PS.map.west, label, PS.map.proj);
        fprintf(PS.fp, "GS (%s) dup SWH ++ dup MR pop 90 ROT SHL GR\n", label);
        G_format_northing(PS.map.south, label, PS.map.proj);
        fprintf(PS.fp, "GS (%s) dup SWH ++ 1 MR pop SHL GR\n", label);
    }
    else if (KEY("compass") || KEY("rose"))
    {
        char h;
        int dg, mn;
        double conv, sec;

        if (sscanf(data, "%lf %lf %lf", &e1, &n1, &d) != 3) {
            error(key, data, "compass roses need 3 parameters");
        }
        d *= (MT_TO_POINT / (double)PS.scale);
        set_xy_where(".25 LW", e1, n1, "M ");
        /* exterior */
        fprintf(PS.fp, "GS 90 ROT ");
        fprintf(PS.fp, "%.1f 0 90 270 {GS ROT dup 0 LR [1] 0 LD S GR} for ", d);
        fprintf(PS.fp,
                " 0 -1 -359 {/i XD GS i ROT dup 0 MR i 10 mod 0 eq "
                        "{-9 0 LR i neg to_s dup SW 2 div 10 exch MR GS 270 ROT show GR} "
                        "{i 5 mod 0 eq {-6} {-3} ifelse 0 LR} ifelse S GR} for ");
        fprintf(PS.fp, " pop GR\n");
        /* convergence, only for testing the command must have an angle parameter */
        conv = 0.0;
        if (PS.map.proj != PROJECTION_LL)
        {
            struct pj_info ll_proj, xy_proj;

            init_proj(&ll_proj, &xy_proj);
            e2 = e1; n2 = n1;
            pj_do_proj(&e2, &n2, &xy_proj, &ll_proj);
            n2 = 90.;
            pj_do_proj(&e2, &n2, &ll_proj, &xy_proj);
            conv = -1.*atan2(e2-e1, n2-n1)*180./PI;
        }
        /* interior */
        fprintf(PS.fp, "GS %.3f ROT F0S .8 mul FS ", conv+90.);
        fprintf(PS.fp, "%.1f 0 90 270 {GS ROT dup 0 LR S GR} for ", .60*d);
        fprintf(PS.fp,
                " 0 -1 -359 {/i XD GS i ROT dup 0 MR i 10 mod 0 eq "
                        "{6 0 LR i 30 mod 0 eq "
                        "{i neg to_s dup SW 2 div 1 exch MR GS 270 ROT show GR} if} "
                        "{i 5 mod 0 eq {3} {1.5} ifelse 0 LR} ifelse S GR} for ");

        G_lon_parts(conv, &dg, &mn, &sec, &h);
        fprintf(PS.fp, " 2 div 1 MR F0S 1.25 mul FS (%dº %d' %0.f'' %c) SHC GR\n", dg, mn, sec, h);
    }
    else if (KEY("rute"))
    {
        if (sscanf(data, "%s %lf %lf %[^\n]", label, &e1, &n1, buf) != 4) {
            error(key, data, "rute need 4 parameters");
        }
        if (scan_dimen(label, &lw) != 1) {
            error(key, data, "width not valid (rune)");
        }
        fprintf(PS.fp, "%.1f LW ", lw);
        set_xy_where("cP exch 2 copy", e1, n1, "L cP 2 copy 8 2 roll");
        fprintf(PS.fp,
                " 4 -1 roll add 2 div 3 1 roll add 2 div exch M"
                " 4 1 roll sub 3 1 roll exch sub atan GS ROT 0 1 MR (%s) SHC GR S\n", buf);
    }
    else
    {
        error(key, data, "not found\n");
    }

    return 1;
}

