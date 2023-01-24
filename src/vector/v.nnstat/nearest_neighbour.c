#include "local_proto.h"

void nn_average_distance_real(struct nna_par *xD, struct points *pnts,
                              struct nearest *nna)
{
    int i;
    int i3 = xD->i3; // 2D or 3D NNA
    int n = pnts->n; // # of points
    double sum_r;    // sum of the distances of the NNs

    struct ilist *list;

    G_message(_("Computing average distance between nearest neighbors..."));
    sum_r = 0.;

    for (i = 0; i < n; i++) {
        list = G_new_ilist();         // create list of overlapping rectangles
        list = find_NNs(i3, i, pnts); // search NNs
        sum_r += sum_NN(i3, i, list, pnts); // add NN distance to the sum
        G_percent(i, n - 1, 1);             // progress bar
    }
    nna->rA = sum_r / n; // average NN distance

    return;
}

void density(struct points *pnts, struct nna_par *xD, const char *Acol,
             struct nearest *nna)
{
    if (xD->i3 == TRUE) { // 3D NNA: Minimum Enclosing Block
        nna->A = Acol != NULL
                     ? atof(Acol)
                     : MBB(pnts); // set volume specified by user or MBB volume
        if (nna->A <= 0.) {
            G_fatal_error(_("Volume must be greater than 0"));
        }
    }

    if (xD->i3 == FALSE) { // 2D NNA: Minimum Enclosing Rectangle
        nna->A = Acol != NULL
                     ? atof(Acol)
                     : MBR(pnts); // set area specified by user or MBR area
        if (nna->A <= 0.) {
            G_fatal_error(_("Area must be greater than 0"));
        }
    }

    nna->rho = pnts->n / nna->A; // number of points per area/volume unit

    return;
}

void nn_average_distance_expected(struct nna_par *xD, struct nearest *nna)
{
    if (xD->i3 == TRUE) { // 3D NNA:
        nna->rE =
            0.55396 / pow(nna->rho, 1. / 3.); // according to Chandrasekhar
    }
    if (xD->i3 == FALSE) {              // 2D NNA:
        nna->rE = 0.5 / sqrt(nna->rho); // according to Clark & Evans
    }
}

/* ---------------------------------
 * Two-tailed Student's test of significance of the mean
 * ---------------------------------*/

void nn_results(struct points *pnts, struct nna_par *xD, struct nearest *nna)
{
    G_message(_("\n\n*** Nearest Neighbour Analysis results ***\n"));
    if (xD->zcol != NULL) {
        G_message(
            _("Input settings .. 3D layer: %d .. 3D NNA: %d .. zcolumn: %s"),
            xD->v3, xD->i3, xD->zcol);
    }
    else {
        G_message(_("Input settings .. 3D layer: %d 3D NNA: %d"), xD->v3,
                  xD->i3);
    }
    G_message(_("Number of points .......... %d"), pnts->n);
    if (xD->i3 == TRUE) {
        G_message(_("Volume .................... %f [units^3]"), nna->A);
    }
    else {
        G_message(_("Area ...................... %f [units^2]"), nna->A);
    }
    G_message(_("Density of points ......... %f"), nna->rho);
    G_message(_("Average distance between the nearest neighbours ........... "
                "%.3f [units]"),
              nna->rA);
    G_message(_("Average expected distance between the nearest neighbours .. "
                "%.3f [units]"),
              nna->rE);
    G_message(_("Ratio rA/rE ............... %f"), nna->R);
    G_message(_("\n*** Results of two-tailed test of the mean ***"));
    G_message(_("Null hypothesis: Point set is randomly distributed within the "
                "region."));
    G_message(_("Standard variate of the normal curve> c = %f"), nna->c);

    /* two-tailed test of the mean */
    if (-1.96 < nna->c && nna->c < 1.96) {
        G_message(_("Null hypothesis IS NOT REJECTED at the significance level "
                    "alpha = 0.05"));
    }
    if (-2.58 < nna->c && nna->c <= -1.96) {
        G_message(_("Null hypothesis IS NOT REJECTED at the significance level "
                    "alpha = 0.01 => point set is clustered"));
        G_message(_("Null hypothesis CAN BE REJECTED at the significance level "
                    "alpha = 0.05 => point set is randomly distributed"));
    }

    if (1.96 <= nna->c && nna->c < 2.58) {
        G_message(_("Null hypothesis IS NOT REJECTED at the significance level "
                    "alpha = 0.01 => point set is dispersed"));
        G_message(_("Null hypothesis CAN BE REJECTED at the significance level "
                    "alpha = 0.05 => point set is randomly distributed"));
    }

    if (nna->c <= -2.58) {
        G_message(
            _("Null hypothesis CAN BE REJECTED at the significance levels "
              "alpha = 0.05 and alpha = 0.01 => point set is clustered"));
    }
    if (nna->c >= 2.58) {
        G_message(
            _("Null hypothesis CAN BE REJECTED at the significance levels "
              "alpha = 0.05 and alpha = 0.01 => point set is dispersed"));
    }
    G_message(" ");

    return;
}

void nn_statistics(struct points *pnts, struct nna_par *xD, struct nearest *nna)
{
    double disp_rE, var_rE, sig_rE;

    if (xD->i3 == TRUE) { // 3D NNA:
        disp_rE = 0.347407742479038 /
                  pow(nna->rho,
                      2. / 3.); // standard deviation of average distance
                                // between the NN in randomly distributed set of
                                // points; derived in (Stopkova, 2013)
        var_rE =
            0.0405357524727094 /
            pow(nna->rho, 2. / 3.); // variance of average distance between the
                                    // NN in randomly distributed set of points;
                                    // derived in (Stopkova, 2013)
    }
    if (xD->i3 == FALSE) { // 2D NNA:
        disp_rE =
            1. / (nna->rho *
                  PI); // standard deviation of average distance between the NN
                       // in randomly distributed set of points (Clark & Evans)
        var_rE =
            (4.0 - PI) /
            (4.0 * PI * pnts->n *
             nna->rho); // variance of average distance between the NN in
                        // randomly distributed set of points (Clark & Evans)
    }

    sig_rE = sqrt(var_rE); // standard error of the mean distance
    nna->c =
        (nna->rA - nna->rE) / sig_rE; // standard variate of the normal curve

    nn_results(pnts, xD, nna); // write the result to the command line

    return;
}
