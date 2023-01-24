/***********************************************************************/
/*
   percolate.c

   Revised by Mark Lake, 13/05/2020
   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include "percolate.h"
#include "global_vars.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void percolate(float mindist, float inc, float maxdist, long int numpoints,
               char *text_file_name, char *group_text_file_name, int modulo)
{
    int e = 0;
    int i;
    int nextNewGroup = 0;
    int targetGroup;
    int leaveGroup;
    int exit = 0;
    int numgroups;
    int iteration = 1;
    float next_output_dist;
    float fully_connected_dist = -1;
    float connectionCoefficient = 0;
    char text_file_name_iter[256];
    char group_text_file_name_iter[256];
    enum targetType { from = 0, to = 1, unknown = 2 };
    enum targetType target;
    int fromSize, toSize;

    /* Set first output distance threshold.  If min is zero set it to
       mindist + inc, otherwise set it to min. */
    if (mindist > 0) {
        next_output_dist = mindist;
    }
    else {
        next_output_dist = mindist + inc;
    }

    while (next_output_dist < edgeList[0].dist)
        next_output_dist = next_output_dist + inc;

    while ((edgeList[e].dist <= maxdist) && (e < nEdges) && (exit != 1)) {
#ifdef VALIDATE
        fprintf(stderr,
                "\nIteration %d, Checking nodes on edge %d (distance %6.1f), "
                "from %d to %d ",
                iteration, edgeList[e].id, edgeList[e].dist,
                edgeList[e].from + 1, edgeList[e].to + 1);
        fflush(stderr);
#endif
        if ((nodeList[edgeList[e].from].group == ownGroup) &&
            (nodeList[edgeList[e].to].group == ownGroup)) {
            /* A. Neither node in a group other than own, add both to a new
               group and increment next new group */
            connectionCoefficient =
                updateGroupSizes(groupSize, nodeList[edgeList[e].from].group,
                                 nodeList[edgeList[e].to].group, nextNewGroup);
            setNodeMaxConnect(nodeList, edgeList[e].from,
                              connectionCoefficient);
            setNodeMaxConnect(nodeList, edgeList[e].to, connectionCoefficient);
            insertNodeAtHeadGroupList(&nodeList[edgeList[e].from], groupList,
                                      nextNewGroup, iteration,
                                      edgeList[e].dist);
            insertNodeAtHeadGroupList(&nodeList[edgeList[e].to], groupList,
                                      nextNewGroup, iteration,
                                      edgeList[e].dist);
            groupInfo[nextNewGroup].birth = iteration;
            groupInfo[nextNewGroup].birth_distance = edgeList[e].dist;
            nextNewGroup++;
        }
        else {
            if (nodeList[edgeList[e].from].group ==
                nodeList[edgeList[e].to].group) {
                /* B. Both nodes in the same group that is not ownGroup, so
                   nothing to do */
            }
            else {
                /* Choose which group should be target according to criteria.
                   One node could still be in ownGroup */
                target = unknown;
                if (strcmp(keepGroup, "biggest") == 0) {
                    /* Set target group to biggest */
                    fromSize = getGroupSize(groupSize,
                                            nodeList[edgeList[e].from].group);
                    toSize =
                        getGroupSize(groupSize, nodeList[edgeList[e].to].group);
                    if ((fromSize > toSize) &&
                        (nodeList[edgeList[e].from].group != ownGroup)) {
                        target = from;
                    }
                    else {
                        if ((fromSize < toSize) &&
                            (nodeList[edgeList[e].to].group != ownGroup)) {
                            target = to;
                        }
                    }
                }
                if (target == unknown) {
                    /* We get here if criterion for choosing which group to keep
                       is "oldest", or if criterion was "biggest" but both
                       groups were the same size */
                    if (nodeList[edgeList[e].from].group <
                        nodeList[edgeList[e].to].group) {
                        /* This implements keep by age because group ids
                           increment by age (apart from own group).  If 'from'
                           group id is less than 'to' group id then it is older,
                           so node should be added to 'from' group and removed
                           from 'to' group.  Convieniently this also prefers any
                           group over own group */
                        target = from;
                    }
                    else {
                        target = to;
                    }
                }

                if (target == to) {
                    /* What to do if target group is 'to' group */
                    targetGroup = nodeList[edgeList[e].to].group;
                    leaveGroup = nodeList[edgeList[e].from].group;
                    if (leaveGroup == ownGroup) {
                        /* C. Node is in own group so move to target group */
                        connectionCoefficient = updateGroupSizes(
                            groupSize, leaveGroup, targetGroup, targetGroup);
                        setNodeMaxConnect(nodeList, edgeList[e].from,
                                          connectionCoefficient);
                        setNodeMaxConnect(nodeList, edgeList[e].to,
                                          connectionCoefficient);
                        insertNodeAtHeadGroupList(&nodeList[edgeList[e].from],
                                                  groupList, targetGroup,
                                                  iteration, edgeList[e].dist);
                    }
                    else {
                        /* D. If leaveGroup is NOT ownGroup then move all nodes
                           in leaveGroup to targetGroup. Here we repeatedly pick
                           up the node at the head of the group list, which
                           works because the head is reset each time a node is
                           removed. */
                        connectionCoefficient = updateGroupSizes(
                            groupSize, leaveGroup, targetGroup, targetGroup);
                        setNodeMaxConnect(nodeList, edgeList[e].from,
                                          connectionCoefficient);
                        setNodeMaxConnect(nodeList, edgeList[e].to,
                                          connectionCoefficient);
                        setNodeLastGroupConnected(nodeList, edgeList[e].from,
                                                  leaveGroup);
                        setNodeLastGroupConnected(nodeList, edgeList[e].to,
                                                  targetGroup);
                        setNodeLastDistanceConnection(
                            nodeList, edgeList[e].from, edgeList[e].dist);
                        setNodeLastDistanceConnection(nodeList, edgeList[e].to,
                                                      edgeList[e].dist);
                        groupInfo[targetGroup].wins++;
                        groupInfo[leaveGroup].death = iteration;
                        groupInfo[leaveGroup].death_distance = edgeList[e].dist;
                        groupInfo[leaveGroup].longevity =
                            iteration - groupInfo[leaveGroup].birth;
                        while (groupList[leaveGroup] != NULL) {
                            insertNodeAtHeadGroupList(
                                groupList[leaveGroup], groupList, targetGroup,
                                iteration, edgeList[e].dist);
                        }
                    }
                }
                else {
                    /* We get here if target group is 'from' group */
                    targetGroup = nodeList[edgeList[e].from].group;
                    leaveGroup = nodeList[edgeList[e].to].group;

                    if (leaveGroup == ownGroup) {
                        /* If leaveGroup is ownGroup then we just want to remove
                           this one node */
                        connectionCoefficient = updateGroupSizes(
                            groupSize, leaveGroup, targetGroup, targetGroup);
                        setNodeMaxConnect(nodeList, edgeList[e].from,
                                          connectionCoefficient);
                        setNodeMaxConnect(nodeList, edgeList[e].to,
                                          connectionCoefficient);
                        insertNodeAtHeadGroupList(&nodeList[edgeList[e].to],
                                                  groupList, targetGroup,
                                                  iteration, edgeList[e].dist);
                    }
                    else {
                        /* If leaveGroup is NOT ownGroup then move all nodes in
                           leaveGroup to targetGroup. Here we repeatedly pick up
                           the node at the head of the group list, which works
                           because the head is reset each time a node is
                           removed. */
                        connectionCoefficient = updateGroupSizes(
                            groupSize, leaveGroup, targetGroup, targetGroup);
                        setNodeMaxConnect(nodeList, edgeList[e].from,
                                          connectionCoefficient);
                        setNodeMaxConnect(nodeList, edgeList[e].to,
                                          connectionCoefficient);
                        setNodeLastGroupConnected(nodeList, edgeList[e].from,
                                                  leaveGroup);
                        setNodeLastGroupConnected(nodeList, edgeList[e].to,
                                                  targetGroup);
                        setNodeLastDistanceConnection(
                            nodeList, edgeList[e].from, edgeList[e].dist);
                        setNodeLastDistanceConnection(nodeList, edgeList[e].to,
                                                      edgeList[e].dist);
                        groupInfo[targetGroup].wins++;
                        groupInfo[leaveGroup].death = iteration;
                        groupInfo[leaveGroup].death_distance = edgeList[e].dist;
                        groupInfo[leaveGroup].longevity =
                            iteration - groupInfo[leaveGroup].birth;
                        while (groupList[leaveGroup] != NULL) {
                            insertNodeAtHeadGroupList(
                                groupList[leaveGroup], groupList, targetGroup,
                                iteration, edgeList[e].dist);
                        }
                    }
                }
            }
        }

        /* Update the number of groups and group status */
        numgroups = 0;
        for (i = 0; i < numpoints; i++) {
            if (groupList[i] != NULL) {
                /* fprintf(stderr, "\nGroup %d not NULL, death %d, size %d", i,
                 * groupAge[i][DEATH], getGroupSize(groupSize, i)); */
                numgroups++;
                /* Note: terminal longevity of final group isn't really
                   meaningful unless -e flag is set */
                groupInfo[i].longevity = iteration - groupInfo[i].birth;
            }
        }

        /* Write intermediate CSV file  */

        if (modulo != 0) {
            /* If output is per n node-pair group assignments */
            if ((iteration % modulo) == 0) {
                sprintf(text_file_name_iter, "%s_%d", text_file_name,
                        iteration);
                sprintf(group_text_file_name_iter, "%s_%d",
                        group_text_file_name, iteration);
                Create_CSV(text_file_name_iter, numpoints, overwrite);
                Create_intermediate_group_CSV(group_text_file_name_iter,
                                              nextNewGroup, iteration,
                                              overwrite);
            }
        }
        else {
            /* Else output is per d distance increments */
            if (e < (nEdges - 1))
            /* Only if not the final edge, since that will be picked up in
               the final output */
            {
#ifdef VALIDATE
                /* fprintf (stderr, "\nOutputing CSV for distance at edge %d,
                 * next_output_dist is %f\n", e, next_output_dist); */
#endif
                /*fprintf (stderr, "\nEdge %d, dist %f, e+1 dist %f, nod %f\n",
                   e, edgeList[e].dist, edgeList[e + 1].dist, next_output_dist);
                 */
                if ((edgeList[e].dist <= next_output_dist) &&
                    (edgeList[e + 1].dist > next_output_dist)) {
                    G_message(_("Computing groups for distance %1.2f"),
                              next_output_dist);
                    sprintf(text_file_name_iter, "%s_%1.0f", text_file_name,
                            next_output_dist);
                    sprintf(group_text_file_name_iter, "%s_%1.0f",
                            group_text_file_name, next_output_dist);
                    /*fprintf (stderr, "\nOutputing CSV file <%s>\n",
                     * text_file_name_iter); */
                    Create_CSV(text_file_name_iter, numpoints, overwrite);
                    Create_intermediate_group_CSV(group_text_file_name_iter,
                                                  nextNewGroup, iteration,
                                                  overwrite);
                    /* If next edge distance is greater than the output
                       increment, we need to write the additional (duplicate)
                       intermediate output files to ease susbsequent analysis
                       (otherwise the sequence of output files will have
                       gaps) */
                    while (next_output_dist < edgeList[e + 1].dist) {
                        if (next_output_dist < maxdist) {
                            G_message(_("Computing groups for distance %1.2f"),
                                      next_output_dist);
                            sprintf(text_file_name_iter, "%s_%1.0f",
                                    text_file_name, next_output_dist);
                            sprintf(group_text_file_name_iter, "%s_%1.0f",
                                    group_text_file_name, next_output_dist);
                            Create_CSV(text_file_name_iter, numpoints,
                                       overwrite);
                            Create_intermediate_group_CSV(
                                group_text_file_name_iter, nextNewGroup,
                                iteration, overwrite);
                        }
                        next_output_dist = next_output_dist + inc;
                    }
                }
            }
        }

        /* Check whether all points are joined in one group */
        /* fprintf(stderr, "\nNext output dist %1.3f  numgroups %d",
         * next_output_dist, numgroups); */
        if ((numgroups == 1) && (groupList[ownGroup] == NULL)) {
            if (fully_connected_dist == -1) {
                /* Don't update once fully connected */
                fully_connected_dist = edgeList[e].dist;
            }
            if (exitFullyConnected) {
                exit = 1;
            }
        }

        iteration++;
        e++;
        /*fprintf (stderr, "\nIteration %d", iteration); printGroupSize
           (groupSize, numpoints); */
    }

    /* Write final CSV file  */
    if (exit == 1) {
        /* Exited because fully connected */
        if (modulo != 0) {
            /* If (iteration-1)%modulo) == 0 would already have written output
             * above */
            if (((iteration - 1) % modulo) != 0) {
                sprintf(text_file_name_iter, "%s_%d", text_file_name,
                        iteration - 1);
                /* fprintf(stderr, "Would output %s", text_file_name_iter); */
                Create_CSV(text_file_name_iter, numpoints, overwrite);
            }
            sprintf(group_text_file_name_iter, "%s_%s", group_text_file_name,
                    "final");
            Create_final_group_CSV(group_text_file_name_iter, numpoints,
                                   iteration - 1, overwrite);
            G_message(_("\nTerminating after iteration %d with all points "
                        "connected at %1.2f"),
                      iteration - 1, fully_connected_dist);
        }
        else {
            sprintf(text_file_name_iter, "%s_%1.0f", text_file_name,
                    next_output_dist);
            sprintf(group_text_file_name_iter, "%s_%s", group_text_file_name,
                    "final");
            /* fprintf(stderr, "Would output %s", text_file_name_iter); */
            Create_CSV(text_file_name_iter, numpoints, overwrite);
            Create_final_group_CSV(group_text_file_name_iter, numpoints,
                                   iteration, overwrite);
            G_message(_("\nTerminating at distance band %1.2f with all points "
                        "connected at %1.2f"),
                      next_output_dist, fully_connected_dist);
        }
    }
    else {
        /* Exited because max distance exceeded */
        if (modulo != 0) {
            /* If (iteration-1)%modulo) == 0 would already have written output
             * above */
            if (((iteration - 1) % modulo) != 0) {
                sprintf(text_file_name_iter, "%s_%d", text_file_name,
                        iteration - 1);
                Create_CSV(text_file_name_iter, numpoints, overwrite);
            }
            sprintf(group_text_file_name_iter, "%s_%s", group_text_file_name,
                    "final");
            Create_final_group_CSV(group_text_file_name_iter, numpoints,
                                   iteration - 1, overwrite);
            G_message(_("\nTerminating at distance band %1.2f"), maxdist);
        }
        else {
            /* CSV file already written for final distance, but still need
               final summary of groups */
            sprintf(group_text_file_name_iter, "%s_%s", group_text_file_name,
                    "final");
            Create_final_group_CSV(group_text_file_name_iter, numpoints,
                                   iteration - 1, overwrite);

            G_message(_("\nTerminating at distance band %1.2f"),
                      next_output_dist - inc);
        }
        if (fully_connected_dist > -1) {
            G_message(_("All points connected at %1.2f"), fully_connected_dist);
        }
        else {
            G_message(_(
                "NOT ALL POINTS CONNECTED so maxNN is not the global maximum"));
        }
    }
}

/***********************************************************************/
/* Private functions                                                   */

/***********************************************************************/
