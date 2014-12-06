
/****************************************************************************
 *
 * MODULE:       i.theilsen
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculate spectral/temporal Theil-Sen estimator
 *               https://en.wikipedia.org/wiki/Theil-Sen_estimator
 *
 * COPYRIGHT:    (C) 2014 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General Public
 *               License. Read the file COPYING that comes with GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/imagery.h>
#include <grass/glocale.h>

/* Separate function for opening maps (see after main function) */
char *group;
char *subgroup;
struct Ref ref;
DCELL **cell;
int *cellfd;
int open_files(void);
/*-------------------------------------*/

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *grp, *sgrp, *out0, *out1;
    struct History history;  /*metadata */
    struct Colors colors;    /*Color rules */

    int outfd0, outfd1;
    int nfiles=0, count=0, n=0, n0=0, n1=0, n0n1=0;
    DCELL *signal;/*spectral/temporal signal*/
    DCELL *sorted;/*spectral/temporal sorted slope*/
    DCELL **slope;/*Theil-Sen slope matrix*/
    float max=0.0;/*value total max for colour palette */
    float min=0.0;/*value total min for colour palette */
    float mk_max=0.0;/*Mann-Kendall total max for colour palette */
    float mk_min=0.0;/*Mann-Kendall total min for colour palette */
    float temp=0.0;/*swapping temp value*/
    DCELL *outrast0, *outrast1;

    CELL val1, val2;
    /************************************/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("Theil-Sen"));
    G_add_keyword(_("Estimator"));
    G_add_keyword(_("Mann-Kendall"));
    module->description = _("Computes Theil-Sen estimator from spectrum.");

    /* Define the different options */
    grp = G_define_standard_option(G_OPT_I_GROUP);
    grp->description = _("Name of imagery group");

    sgrp = G_define_standard_option(G_OPT_I_SUBGROUP);
    sgrp->description = _("Name of imagery subgroup");

    out0 = G_define_standard_option(G_OPT_R_OUTPUT);
    out0->description = _("Name of Theil-Sen slope map");
    
    out1 = G_define_standard_option(G_OPT_R_OUTPUT);
    out1->description = _("Name of Mann-Kendall test map");

    if (G_parser(argc, argv)) exit(EXIT_FAILURE);
    /*------------------------------------------*/

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Allocate output buffer, use input map data_type */
    outrast0 = Rast_allocate_buf(DCELL_TYPE);
    outrast1 = Rast_allocate_buf(DCELL_TYPE);
    /* Create New raster files */
    outfd0 = Rast_open_new(out0->answer,DCELL_TYPE);
    outfd1 = Rast_open_new(out1->answer,DCELL_TYPE);

    /* Open input files */
    nfiles = open_files();
    
    /* Allocate spectral pixel memory */
    signal = (DCELL *) G_malloc(nfiles * sizeof(DCELL));

    /* Allocate Theil-Sen Slope Matrix */
    slope = (DCELL **) G_malloc(nfiles*nfiles*sizeof(DCELL));

    /* Allocate 1D Theil-Sen Slope sorting array */
    sorted = (DCELL *) G_malloc(nfiles*nfiles*sizeof(DCELL));

    /* Process pixels */
    count = 0;
    for (row=0; row<nrows; row++) {
        G_percent(row, nrows, 2);
        for (n=0; n<nfiles; n++)
            Rast_get_d_row(cellfd[n], cell[n], row);
        for (col=0; col<ncols; col++) {
            count++;
            for (n=0; n<nfiles; n++)
                signal[n] = cell[n][col];
            /* Combinatorics of all in all pairs slopes */
            /* x-axis is spectral/temporal dim., index n is its value */
            /* y-axis is from cell[n] */
            /* Duplicate n index as matrix axis */
            n0=0;
            n1=0;
            for (n0=0; n0<n; n0++){
                for (n1=0; n1<n; n1++){
                    /* Compute outside of diagonal */
                    if(n0!=n1)
                        slope[n0][n1]=(cell[n1]-cell[n0])/(n1-n0);
                }
            }
            /* Sorting all slopes computed */
            n0n1=0;
            /* Reduce dimensionality */
            for (n0=0; n0<n; n0++){
                for (n1=0; n1<n; n1++){
                    if(n0!=n1){
                        sorted[n0n1]=slope[n0][n1];
                        n0n1++;
                    }
                }
            }
            /* Actual Sorting, needs to transport max n0n1 length */
            for (n0=0;n0<n0n1;n0++){
                for (n=1; n<n0n1; n++){
                    if(sorted[n-1]>sorted[n]){
                        temp=sorted[n];
                        sorted[n]=sorted[n-1];
                        sorted[n-1]=temp;
                    }
                }
            }
            /* Extract median slope (list halfway) */
            outrast0[col] = sorted[n0n1/2];
            /* Prepare Theil-Sen colour palette range from data */
            if (sorted[n0n1/2]<min)
                min=sorted[n0n1/2];
            if (sorted[n0n1/2]>max)
                max=sorted[n0n1/2];
            /* Mann-Kendall Trend Test */
            /* Not yet implemented     */
            mk_min=min;
            mk_max=max;
            outrast1[col] = sorted[n0n1/2];
            /*-------------------------*/
        }
        Rast_put_d_row(outfd0, outrast0);
        /* Mann-Kendall Trend Test */
        /* Not yet implemented     */
        /* Rast_put_d_row(outfd1, outrast1);*/
        Rast_put_d_row(outfd1, outrast1);
        /*-------------------------*/
    }

    for (n = 0; n < nfiles; n++) {
        G_free(cell[n]);
        G_free(slope[n]);
        Rast_close(cellfd[n]);
    }
    G_free(signal);
    G_free(sorted); 
    G_free(outrast0);
    G_free(outrast1);
    Rast_close(outfd0);
    Rast_close(outfd1);

    /* For the time being dont touch this */ 
    /* Color table from slope min to slope max */
    Rast_init_colors(&colors);
    val1 = min;
    val2 = max;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    /* Metadata */
    Rast_short_history(out0->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out0->answer, &history);

    /* Color table from Mann-Kendall test min and max */
    Rast_init_colors(&colors);
    val1 = mk_min;
    val2 = mk_max;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    /* Metadata */
    Rast_short_history(out1->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out1->answer, &history);

    exit(EXIT_SUCCESS);
}


/* Separate function for opening maps */
int open_files(void)
{
    char *name, *mapset;
    int n, missing;

    I_init_group_ref(&ref);

    G_strip(group);
    if (!I_find_group(group))
    G_fatal_error(_("Group <%s> not found in current mapset"), group);

    G_strip(subgroup);
    if (!I_find_subgroup(group, subgroup))
    G_fatal_error(_("Subgroup <%s> in group <%s> not found"),
              subgroup, group);

    I_free_group_ref(&ref);
    I_get_subgroup_ref(group, subgroup, &ref);

    missing = 0;
    for (n = 0; n < ref.nfiles; n++) {
    name = ref.file[n].name;
    mapset = ref.file[n].mapset;
        if (G_find_raster(name, mapset) == NULL) {
        missing = 1;
        G_warning(_("Raster map <%s> do not exists in subgroup <%s>"),
              G_fully_qualified_name(name, mapset), subgroup);
        }
    }
    if (missing)
        G_fatal_error(_("No raster maps found"));

    if (ref.nfiles <= 1) {
    if (ref.nfiles <= 0)
        G_warning(_("Subgroup <%s> doesn't have any raster maps"),
              subgroup);
    else
        G_warning(_("Subgroup <%s> only has 1 raster map"), subgroup);
    G_fatal_error(_("Subgroup must have at least 2 raster maps"));
    }

    cell = (DCELL **) G_malloc(ref.nfiles * sizeof(DCELL *));
    cellfd = (int *)G_malloc(ref.nfiles * sizeof(int));
    for (n = 0; n < ref.nfiles; n++) {
        cell[n] = Rast_allocate_d_buf();
        name = ref.file[n].name;
        mapset = ref.file[n].mapset;
        cellfd[n] = Rast_open_old(name, mapset);
    }

    return(ref.nfiles);
}

