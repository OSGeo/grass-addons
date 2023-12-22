/***********************************************************************/
/*
   v.percolate

   *****

   COPYRIGHT:    (C) 2020 by UCL, Theo Brown and the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the COPYING file that comes with GRASS
   for details.

   *****

   REVISIONS

   Written by Theo Brown and Mark Lake for GRASS 7.x

   This revision (v10) 9/12/2020 adds:
   - Fixed bug where intermediate output files were not written if nothing
   had changed (makes subsequent analysis difficult)
   - Reads meaningful node id from vector file and stores this
   - Choice of rules to subsume groups - oldest wins or biggest wins
   - Records additional info. about cluster birth and death, and role of nodes
   as connectors


   *****

   AUTHOR

   Theo Brown
   Mark Lake <mark.lake@ucl.ac.uk>

   University College London
   Institute of Archaeology
   31-34 Gordon Square
   London.  WC1H 0PY
   United Kingdom

   *****

   ACKNOWLEDGEMENTS


   *****

   PURPOSE

   1) Implements continuum percolation analysis.  Identifies clusters of point
   locations at multiple threshold distances.  For each input point the module
   outputs the following information at each threshdold distance:

   - An ID chosen from the fields in the input vector map
   - Spatial coordinate
   - Cluster membership (cluster ID)
   - Iteration at which the point first joined a cluster
   - Iteration at which the point most recently joined a new cluster
   - Number of changes of cluster membership
   - Threshold distance at which the point first joined a cluster
   - Threshold distance at which the point most recently joined a new cluster
   - Maximum connection coefficient obtained

   2) In addition to idnetifying clusters, this module also computes an
   experimental connection coefficient for each point location.  This is
   intended to capture a property roughly analogous to Betweeness Centrality in
   network analysis.  The connection coefficient is smaller if a point location
   joins 2 small clusters or 1 large and 1 small cluster, and greater is it
   joins 2 large clusters.


   *****

   NOTES

   *****

   TO DO

   Ought to be possible to run without specifying id (currently segfaults
   so id has been made a required parameter).

   Clean code architecture, Specifically, standardise whether to pass
   nodeList, edgeList and groupsList as arguments, or as global
   variables.

   Output vector maps


 */

/***********************************************************************/

#define MAIN

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <float.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>

#include "global_vars.h"
#include "node.h"
#include "edge_array.h"
#include "distance.h"
#include "groups.h"
#include "file.h"
#include "vector.h"
#include "percolate.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *input, *input_type, *input_field, *input_id, *output;
    struct Option *min_thresh, *thresh_inc, *max_thresh, *interval;
    struct Option *keep;
    struct Flag *exitflag;
    int modulo;
    float min, inc, max;
    long int numpoints;
    float maxdist, minNNdist, maxNNdist;
    float **DistanceMatrix;
    char text_file_name[256];
    char group_text_file_name[256];

    G_gisinit(argv[0]);
    G_sleep_on_error(0);

    /* Declare module info. */

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("percolation"));
    G_add_keyword(_("cluster"));
    G_add_keyword(_("point"));
    module->description = _("Continuum percolation analysis");

    /* Define the options */

    input = G_define_standard_option(G_OPT_V_INPUT);
    input->key = "input";
    input->required = YES;
    input->label = _("Name of existing vector map");
    input->guisection = _("Input vector points");

    input_field = G_define_standard_option(G_OPT_V_FIELD);
    input_field->key = "layer";
    input_field->label = _("Layer number or name");
    input_field->guisection = _("Input vector points");

    /* TODO: Wrong G_OPT? */
    input_id = G_define_standard_option(G_OPT_V_FIELD);
    input_id->key = "id";

    input_id->answer = "";
    input_id->label = _("Name of field in input map which contains ID");
    input_id->guisection = _("Input vector points");
    input_id->required = YES;

    input_type = G_define_standard_option(G_OPT_V_TYPE);
    input_type->key = "type";
    input_type->options = "point";
    input_type->answer = "point";
    input_type->required = YES;
    input_type->label = _("Feature type (point only)");
    input_type->guisection = _("Input vector points");

    output = G_define_option();
    output->key = "output";
    output->type = TYPE_STRING;
    output->required = YES;
    output->description = _("Root name for output plain text CSV file");
    output->guisection = _("Output");

    min_thresh = G_define_option();
    min_thresh->key = "min";
    min_thresh->type = TYPE_DOUBLE;
    min_thresh->required = NO;
    min_thresh->answer = "0.0";
    min_thresh->description = _("Minimum distance threshold for analysis");
    min_thresh->guisection = _("Output");

    thresh_inc = G_define_option();
    thresh_inc->key = "inc";
    thresh_inc->type = TYPE_DOUBLE;
    thresh_inc->required = NO;
    thresh_inc->answer = "0.0";
    thresh_inc->description = _("Amount by which distance threshold is "
                                "incremented between minthresh and maxthresh");
    thresh_inc->guisection = _("Output");

    max_thresh = G_define_option();
    max_thresh->key = "max";
    max_thresh->type = TYPE_DOUBLE;
    max_thresh->required = NO;
    max_thresh->answer = "0.0";
    max_thresh->description = _("Maximum distance threshold for analysis");
    max_thresh->guisection = _("Output");

    interval = G_define_option();
    interval->key = "interval";
    interval->type = TYPE_INTEGER;
    interval->answer = "0";
    interval->description =
        _("Choose interval output. E.g. interval 10 will produce output for "
          "every tenth node-pair assigned cluster membership. Zero disables");
    interval->guisection = _("Output");

    keep = G_define_option();
    keep->key = "keep";
    keep->type = TYPE_STRING;
    keep->options = "oldest,biggest";
    keep->answer = "oldest";
    keep->description =
        _("Rule for deciding which cluster to keep: oldest or biggest");
    keep->guisection = _("Output");

    exitflag = G_define_flag();
    exitflag->key = 'e';
    exitflag->description =
        _("Terminate once all points are connected in one group");
    exitflag->guisection = _("Output");

    /* GUI dependency */
    input->guidependency = G_store(input_field->key);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* Make parameters available */

    strcpy(text_file_name, output->answer);
    sprintf(group_text_file_name, "%s_%s", output->answer, "cluster");
    strcpy(keepGroup, keep->answer);

    strcpy(input_id_col, input_id->answer);
    if (strlen(input_id_col) > 0)
        doName = 1;
    else
        doName = 0;

    min = atof(min_thresh->answer);
    inc = atof(thresh_inc->answer);
    max = atof(max_thresh->answer);
    modulo = atof(interval->answer);

    exitFullyConnected = exitflag->answer;

    if (min < 0) {
        G_fatal_error(_("min < 0"));
    }
    if (max <= 0) {
        G_message(_("max will be set to max distance between any two points in "
                    "the input map"));
    }
    if (min > max) {
        G_fatal_error(_("min > max"));
    }
    if ((inc <= 0) && (modulo == 0)) {
        G_message(_("inc will be set automatically"));
    }

    overwrite = G_check_overwrite(argc, argv);

#ifdef VALIDATE
    fprintf(stderr, "\n***** Validation run ************************\n\n");
#endif

    /***********************************************************************
      Read points and compute distance matrix

    ***********************************************************************/

#ifdef VALIDATE
    fprintf(stderr, _("\n\n----- Loading vector file -------------------\n\n"));
#endif
    numpoints = read_input_vector(input->answer, input_field->answer);
    if (numpoints < 2) {
        G_fatal_error(_("Only %ld points, so no distances!"), numpoints);
    }

#ifdef VALIDATE
    fprintf(stderr, _("\n\n----- Computing distance matrix--------------\n\n"));
#endif
    /* Compute a distance matrix based on shortest distance */

    /* Ideally we want to split this off so that the programme takes a
       matrix as input, in order that we can use other distances,
       including those derived from cost-surface analyis */

    DistanceMatrix = initialiseDistanceMatrix(numpoints);
    maxdist = computeDistanceMatrix(DistanceMatrix, numpoints, nodeList);

#ifdef VALIDATE
    printDistanceMatrixWithNodeCats(DistanceMatrix, numpoints, nodeList);
#endif

    /* Set max threshold from data if it was not given by user */
    if (max <= 0.0) {
        max = maxdist;
    }

    /* Set increment from data if it was not given by user */
    if (inc <= 0.0) {
        inc = (max - min) / 10;
    }

    /***********************************************************************
      Create and sort edge list

    ***********************************************************************/

    /* Create a list of all edges (non-directional, i.e. A-B is B-A) */

#ifdef VALIDATE
    fprintf(stderr, "\n\n----- Creating edge list  -------------------\n\n");
#endif

    edgeList = initialiseEdgeArray(numpoints);
    nEdges = constructEdgeArray(edgeList, DistanceMatrix, numpoints);
    sortEdgeArray(edgeList);

    /* Free memory used by distance matrix */

    freeDistanceMatrix(numpoints, DistanceMatrix);

    /***********************************************************************
      Allocate initial group membership

    ***********************************************************************/

    ownGroup = numpoints;
    /* allocateInitialGroupMembership (nodeList, groupList, numpoints); */
    groupList = allocateInitialGroupMembership(nodeList, numpoints);
    groupSize = allocateInitialGroupSize(numpoints);
    /* groupAge = allocateInitialGroupAge (numpoints); */
    groupInfo = allocateInitialGroupInfo(numpoints);

#ifdef VALIDATE
    fprintf(stderr, "\nNumber of points = %ld", numpoints);
    fprintf(stderr, "\nNumber of edges = %d\n", nEdges);
    fprintf(stderr, "\nInitial cluster id = %d\n", ownGroup);
    fprintf(stderr, "\n\nSorted edge list (node cat values) is:");
    printEdgeArrayWithNodeCats(edgeList, nEdges, nodeList);
    fprintf(stderr, "\n\nSorted edge list (node names) is:");
    printEdgeArrayWithNodeNames(edgeList, nEdges, nodeList);

#endif
    /* fprintf (stderr, "\n\nSorted edge list (node names) is:"); */
    /* printEdgeArrayWithNodeNames (edgeList, nEdges, nodeList); */

    /***********************************************************************
      Do percolation

    ***********************************************************************/

#ifdef VALIDATE
    fprintf(stderr, "\n\n----- Doing percolation  --------------------\n\n");
    fprintf(stderr, "\nMinimum threshold = %6.1f", min);
    fprintf(stderr, "\nMaximum threshold = %6.1f", max);

    if (modulo > 0) {
        G_message(
            _("\nOutputing results by every %d node-pair assignment to group"),
            modulo);
    }
    else {
        G_message(_("\nOutputing results at distance thresholds:"));
        float t;

        for (t = min; t < max; t += inc) {
            fprintf(stderr, " %f,", t);
        }
        fprintf(stderr, " %f", max);
    }
    fprintf(stderr, "\n");
#endif

    percolate(min, inc, max, numpoints, text_file_name, group_text_file_name,
              modulo);

    getMinMaxNNdistances(nodeList, numpoints, numpoints, &minNNdist,
                         &maxNNdist);
    G_message(_("Min NN distance = %f, Max NN distance = %f"), minNNdist,
              maxNNdist);
    G_message(_("Analysis complete"));

    /* Tidy up */

    /* printGroupSize (groupSize, numpoints); */

    freeGroupSize(groupSize);
    freeGroupInfo(groupInfo);

    exit(EXIT_SUCCESS);
}

/************Functions*************************************************/
