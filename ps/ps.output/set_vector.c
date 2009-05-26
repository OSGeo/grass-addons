/* File: set_vector.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/symbol.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"

#define DRAW_LINE   0
#define DRAW_HLINE  1

int set_vector(int masked, int type)
{
    int i;
    char buf[1024];

    for (i = PS.vct_files -1; i >= 0; i--)
    {
        if (masked && !PS.vct[i].masked) {
            continue;
        }
        if (!masked && PS.vct[i].masked) {
            continue;
        }
        if (PS.vct[i].type != type) {
            continue;
        }
        /* select the type of output */
        if (PS.vct[i].type == LINES)
        {
            VLINES * vl = (VLINES *)PS.vct[i].data;
            if (vl->hline.width > 0 && !(vl->hline.color.none))
            {
                set_vlines(PS.vct[i], vl, DRAW_HLINE);
                Vect_rewind(&(PS.vct[i].Map));
            }
            set_vlines(PS.vct[i], vl, DRAW_LINE);
        }
        else if (PS.vct[i].type == AREAS)
        {
            VAREAS * va = (VAREAS *)PS.vct[i].data;
            if (va->pat != NULL)
            {
                set_ps_pattern(PS.vct[i].id, va->pat, va);
            }
            if (va->width != 0.)
                set_vline_areas(PS.vct[i], va);
            else
                set_vareas(PS.vct[i], va);
        }
        else if (PS.vct[i].type == POINTS)
        {
            SYMBOL *symb;
            VPOINTS * vp = (VPOINTS *)PS.vct[i].data;
            symb = S_read(vp->symbol);
            if (symb != NULL)
            {
                symbol_save(PS.vct[i].id, vp, symb);
            }
            else
            {
                set_ps_symbol_eps(PS.vct[i].id, vp, vp->symbol);
            }
            set_vpoints(PS.vct[i], vp);
        }
    }

    return 0;
}

/* TO DRAW LINES */
int vector_line(struct line_pnts *lpoints)
{
    if (lpoints->n_points > 0)
    {
        register int i;
        where_moveto(lpoints->x[0], lpoints->y[0]);
        for (i = 1; i <= lpoints->n_points - 1; i++)
        {
            where_lineto(lpoints->x[i], lpoints->y[i]);
        }
    }
    return 0;
}

/* TO DRAW AREAS */
int vector_area(struct line_pnts *lpoints, double sep)
{
    if (lpoints->n_points > 0)
    {
        struct line_pnts *opoints;
        opoints = Vect_new_line_struct();

        register int i;
        where_moveto(lpoints->x[0], lpoints->y[0]);
        for (i = 1; i < lpoints->n_points; i++)
        {
            where_lineto(lpoints->x[i], lpoints->y[i]);
        }
        Vect_line_parallel(lpoints, sep, 0.01, 0, opoints);
        Vect_line_reverse(opoints);
        for (i = 0; i < opoints->n_points; i++)
        {
            where_lineto(opoints->x[i], opoints->y[i]);
        }
        where_lineto(lpoints->x[0], lpoints->y[0]);
    }
    return 0;
}

/** Process a vector of lines */
int set_vlines(VECTOR vec, VLINES *vl, int flag)
{
    int ret, cat;
    int ln, nlines, pt, npoints;
    struct line_cats *lcats;
    struct line_pnts *lpoints;


    nlines = Vect_get_num_lines(&(vec.Map));

    fprintf(PS.fp, "GS 1 setlinejoin\n");  /* lines with linejoin = round */

    /* Create vector array, if required */
    if (vec.cats != NULL)
    {
        vec.Varray = Vect_new_varray(nlines);
        ret = Vect_set_varray_from_cat_string(&(vec.Map), vec.layer,
                        vec.cats, vl->type, 1, vec.Varray);
    }
    else if (vec.where != NULL)
    {
        vec.Varray = Vect_new_varray(nlines);
        ret = Vect_set_varray_from_db(&(vec.Map), vec.layer,
                        vec.where, vl->type, 1, vec.Varray);
    }
    else
        vec.Varray = NULL;

    /* memory for coordinates */
    lcats   = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* process only vectors in current window */
    Vect_set_constraint_region(&(vec.Map),
            PS.map.north, PS.map.south,
            PS.map.east,  PS.map.west,
            PORT_DOUBLE_MAX, -PORT_DOUBLE_MAX);

    /* load attributes if fcolor is named */
    dbCatValArray cv_rgb;
    if (flag == DRAW_LINE)
    {
        if (vl->rgbcol != NULL)
            load_catval_array(&(vec.Map), vl->rgbcol, &cv_rgb);
    }

    /* read and plot lines */
    for (ln = 1; ln <= nlines; ln++)
    {
        ret = Vect_read_line(&(vec.Map), lpoints, lcats, ln);
        if (ret < 0)
            continue;
        if (!(ret & GV_LINES) || !(ret & vl->type))
            continue;
        if (vec.Varray != NULL && vec.Varray->c[ln] == 0)
            continue;

        /* Oops the line is correct, I can draw it */
        /* How I can draw it? */
        if (flag == DRAW_HLINE)
        {
            if (vl->offset != 0.)
            {
                double dis;
                struct line_pnts *opoints = Vect_new_line_struct();

                dis = vl->offset * POINT_TO_MM / 1000. * PS.scale;
                Vect_line_parallel(lpoints, dis, 0.1, 0, opoints);
                vector_line(opoints);
            }
            else
                vector_line(lpoints);
            set_ps_line(&(vl->hline));
        }
        else
        {
            vector_line(lpoints);
            Vect_cat_get(lcats, 1, &cat);
            /* dynamic colors */
            if (vl->rgbcol != NULL)
            {
                PSCOLOR color;
                set_color_name(&color, get_string(&cv_rgb, cat));
                set_ps_color(&color);
            }
            else
            {
                set_ps_color(&(vl->line.color));
            }
            set_ps_line_no_color(&(vl->line));
        }
        /* paint now */
        fprintf(PS.fp, "S\n");
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}

/** Process a vector of areas */
int set_vareas(VECTOR vec, VAREAS *va)
{
    int k, ret, cat;
    int area, nareas, island, nislands, centroid;
    struct line_cats *lcats;
    struct line_pnts *lpoints;
    BOUND_BOX box;

    nareas = Vect_get_num_areas(&(vec.Map));

    fprintf(PS.fp, "GS 1 setlinejoin\n");  /* lines with linejoin = round */

    /* Create vector array, if required */
    if (vec.cats != NULL)
    {
        vec.Varray = Vect_new_varray(nareas);
        Vect_set_varray_from_cat_string(&(vec.Map),
                                          vec.layer, vec.cats, GV_AREA, 1, vec.Varray);
    }
    else if (vec.where != NULL)
    {
        vec.Varray = Vect_new_varray(nareas);
        Vect_set_varray_from_db(&(vec.Map),
                                  vec.layer, vec.where, GV_AREA, 1, vec.Varray);
    }
    else
        vec.Varray = NULL;

    /* memory for categories and coordinates */
    lcats   = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* load attributes if fcolor is named */
    dbCatValArray rgb;
    if (va->rgbcol != NULL)
    {
        load_catval_array(&(vec.Map), va->rgbcol, &rgb);
    }

    /* read and plot vectors */
    for (area = 1; area <= nareas; area++)
    {
        if (vec.Varray != NULL && vec.Varray->c[area] == 0) {
            continue;
        }

        centroid = Vect_get_area_centroid(&(vec.Map), area);
        if (centroid < 1)  /* area is an island */
            continue;

        /* check if in window */
        Vect_get_area_box(&(vec.Map), area, &box);
        if (box.N < PS.map.south || box.S > PS.map.north ||
            box.E < PS.map.west  || box.W > PS.map.east)
            continue;
        /* Oops is a correct area, I can draw it */
        if (Vect_get_area_points(&(vec.Map), area, lpoints) < 0)
            break;
        /* main area */
        fprintf(PS.fp, "NP ");
        vector_line(lpoints);
        fprintf(PS.fp, "CP\n");
        /* islands */
        nislands = Vect_get_area_num_isles(&(vec.Map), area);
        for (island = 0; island < nislands; island++)
        {
            k = Vect_get_area_isle(&(vec.Map), area, island);
            if (Vect_get_isle_points(&(vec.Map), k, lpoints) < 0)
                return -1; /* ? break; */

            vector_line(lpoints);
            fprintf(PS.fp, "CP\n");
        }
        /* set the fill */
        if (!va->fcolor.none || va->rgbcol != NULL)
        {
            double r = va->fcolor.r;
            double g = va->fcolor.g;
            double b = va->fcolor.b;
            /* set the color */
            if (va->rgbcol != NULL) /* dynamic fcolor */
            {
                int R, G, B;
                cat = Vect_get_area_cat(&(vec.Map), area, vec.layer);
                if (G_str_to_color(get_string(&rgb, cat), &R, &G, &B) == 1)
                {
                    r = (double)R/255.;
                    g = (double)G/255.;
                    b = (double)B/255.;
                }
            }
            fprintf(PS.fp, "%.3f %.3f %.3f ", r, g, b);
            /* set the type of fill */
            if (va->pat != NULL)
                fprintf(PS.fp, "PATTERN%d setpattern F ", vec.id);
            else
                fprintf(PS.fp, "C F ");
        }
        /* set the line style */
        if (va->line.width > 0 && !va->line.color.none)
        {
            set_ps_line(&(va->line));
            fprintf(PS.fp, "S\n");
        }
    }

    fprintf(PS.fp, "GR\n");
    return 0;
}

/** Process a vector of lines */
int set_vpoints(VECTOR vec, VPOINTS * vp)
{
    int ret, cat;
    int  x, y, pt, npoints;
    double size, rotate;
    struct line_cats *lcats;
    struct line_pnts *lpoints;

    npoints = Vect_get_num_lines(&(vec.Map));

    /* Create vector array, if required */
    if (vec.cats != NULL)
    {
        vec.Varray = Vect_new_varray(npoints);
        Vect_set_varray_from_cat_string(&(vec.Map), vec.layer,
                    vec.cats, vp->type, 1, vec.Varray);
    }
    else if (vec.where != NULL)
    {
        vec.Varray = Vect_new_varray(npoints);
        Vect_set_varray_from_db(&(vec.Map), vec.layer,
                    vec.where, vp->type, 1, vec.Varray);
    }
    else
        vec.Varray = NULL;

    /* memory for coordinates */
    lcats   = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* load attributes if any */
    dbCatValArray cv_size, cv_rot;
    if (vp->sizecol != NULL)
        load_catval_array(&(vec.Map), vp->sizecol, &cv_size);
    if (vp->rotatecol != NULL)
        load_catval_array(&(vec.Map), vp->rotatecol, &cv_rot);

    /* read and plot lines */
    for (pt = 1; pt <= npoints; pt++)
    {
        ret = Vect_read_line(&(vec.Map), lpoints, lcats, pt);
        if (ret < 0)
            continue;
        if (!(ret & GV_POINTS) || !(ret & vp->type))
            continue;
        if (vec.Varray != NULL && vec.Varray->c[pt] == 0)
            continue;
        /* Is it inside area? */
        G_plot_where_xy(lpoints->x[0], lpoints->y[0], &x, &y);
        PS.x = (double)x / 10.;
        PS.y = (double)y / 10.;
        if (PS.x < PS.map_x || PS.x > PS.map_right ||
            PS.y < PS.map_y || PS.y > PS.map_top)
            continue;
        /* Oops the point is correct, I can draw it */
        Vect_cat_get(lcats, 1, &cat);
        fprintf(PS.fp, "GS ");
        fprintf(PS.fp, "%.4f %.4f TR ", PS.x, PS.y);
        /* symbol size */
        if (vp->sizecol == NULL) {
            size = vp->size;
        }
        else {
            get_number(&cv_size, cat, &size);
            size *= vp->scale;
        }
        if (size > 0.)
            fprintf(PS.fp, "%.3f dup SC ", size);
        /* symbol rotate */
        if (vp->rotatecol == NULL) {
            rotate = vp->rotate;
        }
        else {
            get_number(&cv_rot, cat, &rotate);
        }
        if (rotate > 0.)
            fprintf(PS.fp, "%.3f ROT ", rotate);
        /* symbol line */
        if (size == 0.)
            size = 1.; /* avoid division by zero */
        fprintf(PS.fp, "%.3f LW SYMBOL%d ", (vp->line.width)/size, vec.id);
        fprintf(PS.fp, "GR\n");
    }

    return 0;
}

/** Process a vector of lines as area */
int set_vline_areas(VECTOR vec, VAREAS *va)
{
    int ret, cat;
    int ln, nlines, pt, npoints;
    double width;
    struct line_cats *lcats;
    struct line_pnts *lpoints;


    nlines = Vect_get_num_lines(&(vec.Map));

    fprintf(PS.fp, "GS 1 setlinejoin\n");  /* lines with linejoin = round */

    /* Create vector array, if required */
    if (vec.cats != NULL)
    {
        vec.Varray = Vect_new_varray(nlines);
        ret = Vect_set_varray_from_cat_string(&(vec.Map), vec.layer,
                vec.cats, GV_LINE, 1, vec.Varray);
    }
    else if (vec.where != NULL)
    {
        vec.Varray = Vect_new_varray(nlines);
        ret = Vect_set_varray_from_db(&(vec.Map), vec.layer,
                                        vec.where, GV_LINE, 1, vec.Varray);
    }
    else
        vec.Varray = NULL;

    /* memory for coordinates */
    lcats   = Vect_new_cats_struct();
    lpoints = Vect_new_line_struct();

    /* process only vectors in current window */
    Vect_set_constraint_region(&(vec.Map),
                                 PS.map.north, PS.map.south,
                                 PS.map.east,  PS.map.west,
                                 PORT_DOUBLE_MAX, -PORT_DOUBLE_MAX);

    /* read and plot lines */
    for (ln = 1; ln <= nlines; ln++)
    {
        ret = Vect_read_line(&(vec.Map), lpoints, lcats, ln);
        if (ret < 0)
            continue;
        if (!(ret & GV_LINE))
            continue;
        if (vec.Varray != NULL && vec.Varray->c[ln] == 0)
            continue;

        /* Oops the line is correct, I can draw it */
        fprintf(PS.fp, "NP ");
        vector_area(lpoints, va->width * POINT_TO_MM / 1000. * PS.scale);
        fprintf(PS.fp, "CP\n");
        /* set the fill */
        if (!va->fcolor.none)
        {
            fprintf(PS.fp, "%.3f %.3f %.3f ",
                    va->fcolor.r, va->fcolor.g, va->fcolor.b);
            if (va->pat != NULL)
                fprintf(PS.fp, "PATTERN%d setpattern F ", vec.id);
            else
                fprintf(PS.fp, "C F ");
        }
        /* set the line style */
        if (va->line.width > 0 && !va->line.color.none)
        {
            set_ps_line(&(va->line));
            fprintf(PS.fp, "S\n");
        }
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}
