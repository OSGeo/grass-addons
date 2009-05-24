/* Function: vect_legend
 **
 ** Author: Paul W. Carlson April 1992
 ** Modified by: Radim Blazek Jan 2000 area, label added
 ** Modified by: Morten Hulden Mar 2004, support for legend in columns added
 ** Modified by: E. Jorge Tizado Feb 2009, improve postscript code
 */

#include "vlegend.h"
#include "ps_info.h"
#include "local_proto.h"

int set_vlegend(void)
{
    int n, i, j, k, l, rows, cols, st, items, nopos;
    double x, y, fontsize, sc;

    /* Sort categories by user (min value) - In preparation */
    CELL * ip = (CELL *) G_malloc(sizeof( CELL) * PS.vct_files);
    for (items = 0, i = 0; i < PS.vct_files; i++)
    {
        if (PS.vct[i].lpos > 0) {
            /* ip[items++] = PS.vct[i].id; */
            ip[items++] = i;
        }
    }
    if (items == 0)
        return 0;

    if (PS.vl.order[0] != 0)
        sort_list(PS.vl.order, rows, &ip);

	/* define number of rows */
    if (items < PS.vl.legend.cols) PS.vl.legend.cols = items;
    rows = (int)items / PS.vl.legend.cols;	/* lines per column */
    if (items % PS.vl.legend.cols) ++rows;
    cols = PS.vl.legend.cols;

    /* set font */
    fontsize = set_ps_font(&(PS.vl.legend.font));

    /* Array of data */
    fprintf(PS.fp, "/ARh %d array def\n", rows);
    fprintf(PS.fp, "0 1 %d {ARh exch %.2f put} for\n", rows-1, fontsize);

    fprintf(PS.fp, "/ARw %d array def\n", cols);
    for (i = 0, n = 0; n < cols; n++)
    {
        fprintf(PS.fp, "/AR%d [\n", n);
        for (j = 0; j < rows && i < items; j++, i++)
        {
            k = ip[i];
            /* label of de vector file */
            if (PS.vct[k].label == NULL) {
                fprintf(PS.fp, "( %s (%s))", PS.vct[k].name, PS.vct[k].mapset);
            }
            else {
                fprintf(PS.fp, "( %s)", PS.vct[k].label);
            }
            /* vector data */
            fprintf(PS.fp, " %d [", PS.vct[k].type);
            if (PS.vct[k].type == AREAS)
            {
                VAREAS * va = (VAREAS *)PS.vct[k].data;
                if (!va->line.color.none && va->line.width > 0)
                {
                    fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.8f 1 ",
                            va->line.color.r,
                            va->line.color.g,
                            va->line.color.b,
                            va->line.dash,
                            va->line.width);
                }
                else {
                    fprintf(PS.fp, "0 "); /* no line */
                }
                if (!va->fcolor.none || va->pat != NULL)
                {
                    if (va->pat != NULL)
                        fprintf(PS.fp, "PATTERN%d 1 1", PS.vct[k].id);
                    else
                        fprintf(PS.fp, "%.3f %.3f %.3f 0 1",
                            va->fcolor.r,
                            va->fcolor.g,
                            va->fcolor.b);
                }
                else {
                    fprintf(PS.fp, "0"); /* no fill area */
                }
            }
            else if (PS.vct[k].type == LINES)
            {
                VLINES * vl = (VLINES *)PS.vct[i].data;
                fprintf(PS.fp, "%.3f %.3f %.3f [%s] %.8f",
                        vl->line.color.r,
                        vl->line.color.g,
                        vl->line.color.b,
                        vl->line.dash,
                        vl->line.width);
                if (vl->hline.width <= 0)
                    fprintf(PS.fp, " 1");
                else
                {
                    fprintf(PS.fp, " %.3f %.3f %.3f [%s] %.8f",
                            vl->hline.color.r,
                            vl->hline.color.g,
                            vl->hline.color.b,
                            vl->hline.dash,
                            vl->hline.width);
                    fprintf(PS.fp, " 2");
                }
            }
            else if (PS.vct[k].type == POINTS)
            {
                VPOINTS * vp = (VPOINTS *)PS.vct[k].data;
                fprintf(PS.fp, "(SYMBOL%d) ", PS.vct[k].id);
                /* if vp->size == 0 => no draw? */
                fprintf(PS.fp, " %.4f", vp->line.width / vp->size);
                fprintf(PS.fp, " %.3f", vp->rotate);
                fprintf(PS.fp, " %.3f dup", vp->size);
                fprintf(PS.fp, " %.3f", .45*fontsize);
            }
            fprintf(PS.fp, "]\n");
        }
        fprintf(PS.fp, "] def\n");
        fprintf(PS.fp, "/mx 0 def 0 3 AR%d length -- { ", n);
        fprintf(PS.fp, "AR%d exch get SW /t XD t mx gt {/mx t def} if } for\n", n);
        fprintf(PS.fp, "ARw %d mx put\n", n);
    }
    G_free(ip);

    /** Adjust - Legend Box */
    set_box_orig(&(PS.vl.legend.box));
    set_legend_adjust(&(PS.vl.legend), -1.);
    if (PS.vl.legend.title[0])
        set_box_readjust_title(&(PS.vl.legend.box),
                                 PS.vl.legend.title);
    set_box_draw(&(PS.vl.legend.box));

    /* Make the vector legend */
    fprintf(PS.fp, "RESET\n");
    fprintf(PS.fp, "/xw syw %.2f mul def ", 0.9);    /* symbol-width */
    for (n = 0; n < cols; n++)
    {
        fprintf(PS.fp, "%d COL 0 ROW\n"
                "0 3 AR%d length 1 sub {/i XD\n"
                "ARh row get neg /rh XD\n"
                "AR%d i 1 add get /tipe XD\n"
                "AR%d i 2 add get aload pop\n", n, n, n, n);
        fprintf(PS.fp,  "tipe %d eq {", POINTS);
        fprintf(PS.fp,  "GS rh sub 2 div neg y add x xw 2 div add exch "
                "TR SC ROT LW cvx cvn exec GR} if\n");
        fprintf(PS.fp,  "tipe %d eq {", LINES);
        fprintf(PS.fp,  "{LW 0 LD C x xw add y rh 0.65 mul add dup x exch ML} "
                "repeat} if\n");
        fprintf(PS.fp,  "tipe %d eq {[] 0 LD ", AREAS);
        fprintf(PS.fp,  "x y -- x xw add y rh add -- B "
                "0 ne {0 eq {C} {setpattern} ifelse F} if "
                "0 ne {LW 0 LD C} if S} if\n", 0.2, 0.1, 0.6, 0.8);
        set_ps_color(&(PS.vl.legend.font.color));
        fprintf(PS.fp, "AR%d i get x syw add y ARh row get sub MS row ++ ROW} for\n", n);
    }
	fprintf(PS.fp, "[] 0 setdash\n");

    /* Make the title of legend */
    if (PS.vl.legend.title[0] != 0)
    {
        set_ps_font(&(PS.vl.legend.title_font));
        fprintf(PS.fp, "RESET\n");
        if (PS.vl.legend.title[0] == '.')
            fprintf(PS.fp, "(%s) x cwd 2 div add yo mgy mg sub sub M SHC\n",
                    PS.vl.legend.title+1, PS.vl.legend.title_font.size);
        else
            fprintf(PS.fp, "(%s) x yo mgy mg sub sub MS\n",
                    PS.vl.legend.title, PS.vl.legend.title_font.size);
    }

    return 0;
}
