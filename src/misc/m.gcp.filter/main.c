/****************************************************************************
 *
 * MODULE:       m.gcp.filter
 * AUTHOR(S):    Markus Metz
 *                  based on m.transform
 * PURPOSE:      Utility to filter GCPs with RMS threshold
 * COPYRIGHT:    (C) 2006-2014 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <grass/glocale.h>

struct Max {
    int idx;
    double val;
};

struct Stats {
    struct Max x, y, g;
    double sum2, rms;
};

static char *name;
static int order;
static double threshold;
static int niter;
static int filtered;
static int need_fwd;
static int need_rev;
static int use_rms;

static double E12[10], N12[10], E21[10], N21[10];

static struct Control_Points points;

static int equation_stat;

static int count;
static struct Stats fwd, rev;

static void update_max(struct Max *m, int n, double k)
{
    if (k > m->val) {
        m->idx = n;
        m->val = k;
    }
}

static void update_stats(struct Stats *st, int n, double dx, double dy,
                         double dg, double d2)
{
    update_max(&st->x, n, dx);
    update_max(&st->y, n, dy);
    update_max(&st->g, n, dg);
    st->sum2 += d2;
}

static void diagonal(double *dg, double *d2, double dx, double dy)
{
    *d2 = dx * dx + dy * dy;
    *dg = sqrt(*d2);
}

static void compute_transformation(void)
{
    static const int order_pnts[3] = {3, 6, 10};
    int n;

    equation_stat =
        I_compute_georef_equations(&points, E12, N12, E21, N21, order);

    if (equation_stat == 0)
        G_fatal_error(_("Not enough points, %d are required"),
                      order_pnts[order - 1]);

    if (equation_stat <= 0)
        G_fatal_error(_("Error conducting transform (%d)"), equation_stat);

    count = 0;

    for (n = 0; n < points.count; n++) {
        double e1, n1, e2, n2;
        double fx, fy, fd, fd2;
        double rx, ry, rd, rd2;

        if (points.status[n] <= 0)
            continue;

        count++;

        if (need_fwd) {
            I_georef(points.e1[n], points.n1[n], &e2, &n2, E12, N12, order);

            fx = fabs(e2 - points.e2[n]);
            fy = fabs(n2 - points.n2[n]);

            diagonal(&fd, &fd2, fx, fy);

            update_stats(&fwd, n, fx, fy, fd, fd2);
        }

        if (need_rev) {
            I_georef(points.e2[n], points.n2[n], &e1, &n1, E21, N21, order);

            rx = fabs(e1 - points.e1[n]);
            ry = fabs(n1 - points.n1[n]);

            diagonal(&rd, &rd2, rx, ry);

            update_stats(&rev, n, rx, ry, rd, rd2);
        }
    }

    if (count > 0) {
        fwd.rms = sqrt(fwd.sum2 / count);
        rev.rms = sqrt(rev.sum2 / count);
    }
}

static void filter(void)
{
    static const int order_pnts[3] = {3, 6, 10};
    int i, nvalid;
    double rms1, *rms, *c;

    nvalid = 0;
    for (i = 0; i < points.count; i++) {
        if (points.status[i] > 0)
            nvalid++;
    }

    if (nvalid < order_pnts[order - 1])
        G_fatal_error(_("Not enough points, %d are required"),
                      order_pnts[order - 1]);

    if (nvalid == order_pnts[order - 1]) {
        G_warning(_("The number of valid points can not be reduced"));

        printf("use=%d\n", nvalid);
        printf("filtered=%d\n", filtered);
        printf("rms=0\n");

        return;
    }

    if (niter <= 0)
        niter = nvalid;

    rms1 = -1;
    if (need_fwd)
        rms = &fwd.rms;
    else
        rms = &rev.rms;

    c = rms;
    if (!use_rms) {
        if (need_fwd)
            c = &fwd.g.val;
        else
            c = &rev.g.val;
    }

    i = 0;
    while (i < niter) {
        /* reset stats */
        fwd.sum2 = fwd.rms = 0;
        fwd.x.idx = -1;
        fwd.x.val = -1;
        fwd.y.idx = -1;
        fwd.y.val = -1;
        fwd.g.idx = -1;
        fwd.g.val = -1;

        rev.sum2 = rev.rms = 0;
        rev.x.idx = -1;
        rev.x.val = -1;
        rev.y.idx = -1;
        rev.y.val = -1;
        rev.g.idx = -1;
        rev.g.val = -1;

        compute_transformation();
        i++;

        if (rms1 == -1) {
            rms1 = *rms;
        }

        if (*c < threshold)
            break;

        if (need_fwd) {
            if (fwd.g.val > 0) {
                points.status[fwd.g.idx] = 0;
                filtered++;
                nvalid--;
            }
            else
                break;
        }
        else {
            if (rev.g.val > 0) {
                points.status[rev.g.idx] = 0;
                filtered++;
                nvalid--;
            }
            else
                break;
        }

        if (nvalid == order_pnts[order - 1])
            break;
    }
    printf("use=%d\n", nvalid);
    printf("filtered=%d\n", filtered);
    printf("rms=%g\n", *rms);
}

int main(int argc, char **argv)
{
    struct Option *grp, *val, *thresh, *maxiter;
    struct Flag *up_flag, *rev_flag, *dev_flag;
    struct GModule *module;

    G_gisinit(argv[0]);

    /* Get Args */
    module = G_define_module();
    G_add_keyword(_("miscellaneous"));
    G_add_keyword(_("transformation"));
    G_add_keyword("GCP");
    module->description = _("Filter Ground Control Points (GCPs).");

    grp = G_define_standard_option(G_OPT_I_GROUP);

    val = G_define_option();
    val->key = "order";
    val->type = TYPE_INTEGER;
    val->required = YES;
    val->options = "1-3";
    val->description = _("Rectification polynomial order");

    thresh = G_define_option();
    thresh->key = "threshold";
    thresh->type = TYPE_DOUBLE;
    thresh->required = YES;
    thresh->description = _("Filtering threshold in CRS units");

    maxiter = G_define_option();
    maxiter->key = "iterations";
    maxiter->type = TYPE_INTEGER;
    maxiter->required = NO;
    maxiter->description = _("Maximum number of iterations");

    rev_flag = G_define_flag();
    rev_flag->key = 'b';
    rev_flag->description =
        _("Use backward transformations (default: forward transformations)");

    dev_flag = G_define_flag();
    dev_flag->key = 'd';
    dev_flag->description = _("Use GCP deviation (default: RMS)");

    up_flag = G_define_flag();
    up_flag->key = 'u';
    up_flag->description = _("Update GCPs");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    name = grp->answer;
    order = atoi(val->answer);
    threshold = atof(thresh->answer);
    if (threshold <= 0)
        G_fatal_error(_("Option '%s' must be positive"), thresh->key);
    if (threshold != threshold)
        G_fatal_error(_("Invalid option '%s'"), thresh->key);
    niter = -1;
    if (maxiter->answer)
        niter = atoi(maxiter->answer);

    if (!I_get_control_points(name, &points))
        G_fatal_error(_("Unable to read points for group <%s>"), name);

    filtered = 0;

    need_fwd = rev_flag->answer == 0;
    need_rev = rev_flag->answer != 0;
    use_rms = dev_flag->answer == 0;

    filter();

    if (up_flag->answer && filtered > 0)
        I_put_control_points(name, &points);

    exit(EXIT_SUCCESS);
}
