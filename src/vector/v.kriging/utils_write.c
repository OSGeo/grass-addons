#include "local_proto.h"

void variogram_type(int code, char *type)
{
    switch (code) {
    case 0:
        strcpy(type, "horizontal");
        break;
    case 1:
        strcpy(type, "vertical");
        break;
    case 2:
        strcpy(type, "bivariate");
        break;
    case 3:
        strcpy(type, "anisotropic");
        break;
    }
}

void write2file_basics(struct int_par *xD, struct opts *opt)
{
    struct write *report = xD->report;

    report->fp = fopen(report->name, "a");

    fprintf(report->fp, "************************************************\n");
    fprintf(report->fp, "*** Input ***\n\n");
    fprintf(report->fp, "- vector layer: %s\n", opt->input->answer);
    switch (xD->v3) {
    case TRUE:
        fprintf(report->fp, "- is 3D: yes\n");
        break;
    case FALSE:
        fprintf(report->fp, "- is 3D: no\n");
        break;
    }
    // todo: move to end
    fprintf(report->fp, "\n");
    fprintf(report->fp, "*** Output *** \n\n");
    switch (xD->i3) {
    case FALSE:
        fprintf(report->fp, "- raster layer: %s\n", opt->output->answer);
        fprintf(report->fp, "- is 3D: no\n");
        break;
    case TRUE:
        fprintf(report->fp, "- volume layer: %s\n", opt->output->answer);
        fprintf(report->fp, "- is 3D: yes\n");
        break;
    }
}

void write2file_vector(struct int_par *xD, struct points *pnts)
{
    struct select in_reg = pnts->in_reg;
    struct write *report = xD->report;

    report->fp = fopen(report->name, "a");

    fprintf(report->fp, "\n");
    fprintf(report->fp, "************************************************\n");
    fprintf(report->fp, "*** Input vector layer properties ***\n\n");
    fprintf(report->fp, "# of points (total): %d\n", in_reg.total);
    fprintf(report->fp, "# of points (in region): %d\n", in_reg.n);
    fprintf(report->fp, "# of points (out of region): %d\n\n", in_reg.out);
    fprintf(report->fp, "- extent:\n");
    switch (xD->i3) {
    case TRUE:
        fprintf(report->fp, "xmin=%f   ymin=%f   zmin=%f\n", pnts->r_min[0],
                pnts->r_min[1], pnts->r_min[2]);
        fprintf(report->fp, "xmax=%f   ymax=%f   zmax=%f\n", pnts->r_max[0],
                pnts->r_max[1], pnts->r_max[2]);
        break;
    case FALSE:
        fprintf(report->fp, "xmin=%f   ymin=%f\n", pnts->r_min[0],
                pnts->r_min[1]);
        fprintf(report->fp, "xmax=%f   ymax=%f\n", pnts->r_max[0],
                pnts->r_max[1]);
        break;
    }
}

void write2file_values(struct write *report, const char *column)
{
    fprintf(report->fp, "\n");
    fprintf(report->fp, "************************************************\n");
    fprintf(report->fp, "*** Values to be interpolated ***\n\n");
    fprintf(report->fp, "- attribute column: %s\n", column);
}

void write2file_varSetsIntro(int code, struct write *report)
{
    char type[12];

    variogram_type(code, type);

    fprintf(report->fp, "\n************************************************\n");
    fprintf(report->fp, "*** Variogram settings - %s ***\n\n", type);
}

void write2file_varSets(struct write *report, struct parameters *var_pars)
{
    char type[12];

    variogram_type(var_pars->type, type);

    fprintf(report->fp, "- number of lags in %s direction: %d\n", type,
            var_pars->nLag);
    fprintf(report->fp, "- lag distance (%s): %f\n", type, var_pars->lag);

    if (var_pars->type == 2) {
        fprintf(report->fp, "- number of lags in vertical direction: %d\n",
                var_pars->nLag_vert);
        fprintf(report->fp, "- lag distance (vertical): %f\n", var_pars->lag);
    }

    fprintf(report->fp, "- azimuth: %f°\n", RAD2DEG(var_pars->dir));
    fprintf(report->fp, "- angular tolerance: %f°\n", RAD2DEG(var_pars->td));

    switch (var_pars->type) {
    case 2:
        fprintf(report->fp,
                "- maximum distance in horizontal direction (1/3): %f\n",
                var_pars->max_dist);
        break;
    default:
        fprintf(report->fp, "- maximum distance (1/3): %f\n",
                var_pars->max_dist);
        break;
    }
}

void write2file_variogram_E(struct int_par *xD, struct parameters *var_pars,
                            mat_struct *c_M)
{
    int i, j;
    int n_h;
    double *h, *vert;
    double *c;
    double *gamma;
    struct write *report = xD->report;

    char type[12];

    variogram_type(var_pars->type, type);

    c = &c_M->vals[0];
    gamma = &var_pars->gamma->vals[0];

    fprintf(report->fp, "\n************************************************\n");
    fprintf(report->fp, "*** Experimental variogram - %s ***\n\n", type);

    if (var_pars->type == 2) { // bivariate variogram:
        vert = &var_pars->vertical.h[0];

        for (i = 0; i < var_pars->vertical.nLag; i++) { // write header - verts
            if (i == 0) {
                fprintf(report->fp, "  lagV  ||"); // column for h
            }
            fprintf(report->fp, " %f ||", *vert);
            vert++;
        }
        fprintf(report->fp, "\n");

        for (i = 0; i < var_pars->vertical.nLag;
             i++) { // write header - h c gamma
            if (i == 0) {
                fprintf(report->fp, "  lagHZ ||"); // column for h
            }
            fprintf(report->fp, " c | ave ||");
        }
        fprintf(report->fp, "\n");

        for (i = 0; i < var_pars->vertical.nLag;
             i++) { // write header - h c gamma
            if (i == 0) {
                fprintf(report->fp, "--------||"); // column for h
            }
            fprintf(report->fp, "-----------");
        }
        fprintf(report->fp, "\n");
    }
    else { // univariate variogram
        fprintf(report->fp, " lag ||  # of pairs | average\n");
        fprintf(report->fp, "------------------------------------\n");
    }

    // Write values
    h = var_pars->type == 2 ? &var_pars->horizontal.h[0] : &var_pars->h[0];
    n_h = var_pars->type == 2 ? var_pars->horizontal.nLag : var_pars->nLag;
    for (i = 0; i < n_h; i++) {
        fprintf(report->fp, "%f ||", *h);
        if (var_pars->type == 2) { // bivariate variogram
            for (j = 0; j < var_pars->vertical.nLag; j++) {
                fprintf(report->fp, " %d | %f ||", (int)*c, *gamma);
                c++;
                gamma++;
            } // end for j
            fprintf(report->fp, "\n");
            for (j = 0; j < var_pars->vertical.nLag; j++) {
                fprintf(report->fp, "-----------");
            }
            fprintf(report->fp, "\n");
        }
        else { // univariate variogram
            fprintf(report->fp, " %d | %f\n", (int)*c, *gamma);
            c++;
            gamma++;
        }
        h++;
    }
    fprintf(report->fp, "------------------------------------\n");
}

void write2file_variogram_T(struct write *report)
{
    fprintf(report->fp, "\n");
    fprintf(report->fp, "************************************************\n");
    fprintf(report->fp, "*** Theoretical variogram ***\n\n");
}

void write_temporary2file(struct int_par *xD, struct parameters *var_pars)
{
    // local variables
    int type = var_pars->type;
    int nLag = type == 2 ? var_pars->horizontal.nLag : var_pars->nLag;
    int nLag_vert = type == 2 ? var_pars->vertical.nLag : var_pars->nLag;
    double *h = type == 2 ? var_pars->horizontal.h : var_pars->h;
    double *vert = type == 2 ? var_pars->vertical.h : var_pars->h;
    ;
    double *gamma = var_pars->gamma->vals;
    double sill = var_pars->sill;

    int i; // index
    FILE *fp;
    int file_length;

    /* Introduction */
    switch (type) {
    case 0: // horizontal variogram
        fp = fopen("variogram_hz_tmp.txt", "w");
        if (xD->report->name) { // write name of report file
            file_length = strlen(xD->report->name);
            if (file_length < 4) { // 4 types of variogram
                G_fatal_error(_("File name must contain more than 2 "
                                "characters...")); // todo: error
            }
            fprintf(fp, "%d 9 %s\n", file_length, xD->report->name);
        }
        fprintf(fp, "%d\n", var_pars->type); // write # of lags
        break;

    case 1: // vertical variogram
        fp = fopen("variogram_vert_tmp.txt", "w");
        if (xD->report->name) { // write name of report file
            file_length = strlen(xD->report->name);
            if (file_length < 3) {
                G_fatal_error(_("File name must contain more than 2 "
                                "characters...")); // todo: error
            }
            fprintf(fp, "%d 9 %s\n", file_length, xD->report->name);
        }
        fprintf(fp, "%d\n", var_pars->type); // write type
        break;

    case 2: // bivariate variogram
        fp = fopen("variogram_final_tmp.txt", "w");

        if (xD->report->name) { // write name of report file
            file_length = strlen(xD->report->name);
            if (file_length < 4) { // 4 types of variogram
                G_fatal_error(_("File name must contain more than 2 "
                                "characters...")); // todo: error
            }
            fprintf(fp, "%d 9 %s\n", file_length, xD->report->name);
        }

        fprintf(fp, "%d\n", var_pars->type);          // write type
        fprintf(fp, "%d\n", var_pars->vertical.nLag); // write # of lags
        fprintf(fp, "%f\n", var_pars->vertical.lag);  // write size of lag
        fprintf(fp, "%f\n",
                var_pars->vertical.max_dist); // write maximum distance

        fprintf(fp, "%d\n", var_pars->horizontal.nLag); // write # of lags
        fprintf(fp, "%f\n", var_pars->horizontal.lag);  // write size of lag
        fprintf(fp, "%f\n",
                var_pars->horizontal.max_dist); // write maximum distance
        break;

    case 3: // anisotropic variogram
        fp = fopen("variogram_final_tmp.txt", "w");
        if (xD->report->name) { // write name of report file
            file_length = strlen(xD->report->name);
            if (file_length < 4) { // 4 types of variogram
                G_fatal_error(_("File name must contain more than 4 "
                                "characters...")); // todo: error
            }
            fprintf(fp, "%d 9 %s\n", file_length, xD->report->name);
        }
        fprintf(fp, "%d\n", var_pars->type);  // write type
        fprintf(fp, "%f\n", xD->aniso_ratio); // write ratio of anisotropy
        break;
    }

    if (type != 2) {
        fprintf(fp, "%d\n", nLag);               // write # of lags
        fprintf(fp, "%f\n", var_pars->lag);      // write size of lag
        fprintf(fp, "%f\n", var_pars->max_dist); // write maximum distance
    }
    if (type != 1) {
        fprintf(fp, "%f\n", var_pars->td); // write maximum distance
    }

    switch (type) {
    case 2: // bivariate variogram
        nLag = var_pars->horizontal.nLag;
        nLag_vert = var_pars->vertical.nLag;
        // write h
        for (i = 0; i < nLag; i++) { // write experimental variogram
            fprintf(fp, "%f\n", *h);
            h++;
        }
        // write vert
        for (i = 0; i < nLag_vert; i++) { // write experimental variogram
            fprintf(fp, "%f\n", *vert);
            vert++;
        }
        // write gamma
        for (i = 0; i < nLag * nLag_vert; i++) { // write experimental variogram
            fprintf(fp, "%f\n", *gamma);
            gamma++;
        }
        fprintf(fp, "%f\n", var_pars->horizontal.sill); // write sill
        fprintf(fp, "%f\n", var_pars->vertical.sill);   // write sill
        break;
    default:
        for (i = 0; i < nLag; i++) { // write experimental variogram
            fprintf(fp, "%f %f\n", *h, *gamma);
            h++;
            gamma++;
        }
        fprintf(fp, "%f", sill); // write sill
        break;
    }

    fclose(fp);
}

void report_error(struct write *report)
{
    if (report->name) { // close report file
        fprintf(report->fp, "Error (see standard output). Process killed...");
        fclose(report->fp);
    }
}
