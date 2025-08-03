/***********************************************************************/
/*
   file.c

   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#include <stdlib.h>
#include <string.h>
#include "file.h"
#include "global_vars.h"
#include "groups.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void Create_CSV(char *filename, long int numpoints, int overwrite)
{
    FILE *stream;
    long int nRows = numpoints;
    long int i;
    char message[GMAPSET_MAX + 64];

    stream = Create_file(filename, ".csv", message, overwrite);
    if (stream == NULL)
        G_warning(_("%s"), message);
    else {
        /* Write data to file */
        if (doName)
            fprintf(stream,
                    "Cat,%s,X,Y,Membership,FirstChange,LastChange,NChanges,"
                    "FirstDistance,LastDistance,MaxConCoeff,LastGroupConnected,"
                    "LastDistanceConnection",
                    input_id_col);
        else
            fprintf(stream, "Cat,X,Y,Membership,FirstChange,LastChange,"
                            "NChanges,FirstDistance,LastDistance,MaxConCoeff,"
                            "LastGroupConnected,LastDistanceConnection");
        for (i = 0; i < nRows; i++) {
            fprintf(stream, "\n");

            if (doName)
                fprintf(stream, "%d,%s,%1.2f,%1.2f,%d,%d,%d,%d,%f,%f,%f,%d,%f",
                        nodeList[i].cat, nodeList[i].name, nodeList[i].x,
                        nodeList[i].y, nodeList[i].group,
                        nodeList[i].first_change, nodeList[i].last_change,
                        nodeList[i].count_changes, nodeList[i].first_distance,
                        nodeList[i].last_distance, nodeList[i].max_connect,
                        nodeList[i].lastGroupConnected,
                        nodeList[i].lastDistanceConnection);
            else
                fprintf(stream, "%d,%1.2f,%1.2f,%d,%d,%d,%d,%f,%f,%f,%d,%f",
                        nodeList[i].cat, nodeList[i].x, nodeList[i].y,
                        nodeList[i].group, nodeList[i].first_change,
                        nodeList[i].last_change, nodeList[i].count_changes,
                        nodeList[i].first_distance, nodeList[i].last_distance,
                        nodeList[i].max_connect, nodeList[i].lastGroupConnected,
                        nodeList[i].lastDistanceConnection);
        }

        /* Close file */
        fclose(stream);
    }
}

/***********************************************************************/

void Create_intermediate_group_CSV(char *filename, int nextNewGroup,
                                   int iteration, int overwrite)
{
    FILE *stream;
    long int nRows;
    long int i;
    char message[GMAPSET_MAX + 64];

    stream = Create_file(filename, ".csv", message, overwrite);
    if (stream == NULL)
        G_warning(_("%s"), message);
    else {
        /* Write data to file */

        /* fprintf (stream, "Cluster,Birth,Age,Size"); */
        fprintf(
            stream,
            "Cluster,Birth,BirthDist,Death,DeathDist,Longevity,MaxSize,Wins");

        /* Nothing to record for groups with id <= nextNewGroup, since
           by definition they have never been allocated */
        nRows = nextNewGroup;
        for (i = 0; i < nRows; i++) {
            if (groupList[i] != NULL) {
                /* Only save data for groups that exist */
                fprintf(stream, "\n");
                fprintf(stream, "%ld,%d,%f,%d,%f,%d,%d,%d", i,
                        groupInfo[i].birth, groupInfo[i].birth_distance,
                        groupInfo[i].death, groupInfo[i].death_distance,
                        groupInfo[i].longevity, groupSize[i],
                        groupInfo[i].wins);
            }
        }

        /* Close file */
        fclose(stream);
    }
}

/***********************************************************************/

void Create_final_group_CSV(char *filename, int numpoints, int iteration,
                            int overwrite)
{
    FILE *stream;
    long int nRows;
    long int i;
    char message[GMAPSET_MAX + 64];

    stream = Create_file(filename, ".csv", message, overwrite);
    if (stream == NULL)
        G_warning(_("%s"), message);
    else {
        /* Write data to file */

        /* Note the groupSize is max size attained since there is no
           mechanism by which groups shrink (when cease to have members
           their size is not updated) */

        fprintf(
            stream,
            "Cluster,Birth,BirthDist,Death,DeathDist,Longevity,MaxSize,Wins");

        nRows = numpoints;
        for (i = 0; i < nRows; i++) {
            if (groupInfo[i].birth != -1) {
                /* Only save data for groups that actually existed at some point
                 */
                fprintf(stream, "\n");
                fprintf(stream, "%ld,%d,%f,%d,%f,%d,%d,%d", i,
                        groupInfo[i].birth, groupInfo[i].birth_distance,
                        groupInfo[i].death, groupInfo[i].death_distance,
                        groupInfo[i].longevity, groupSize[i],
                        groupInfo[i].wins);
            }
        }

        /* Close file */
        fclose(stream);
    }
}

/***********************************************************************/

FILE *Create_file(char *name, char *suffix, char *message, int overwrite)
{
    FILE *testStream, *stream;

    strcat(name, suffix);
    testStream = fopen(name, "r");
    if ((testStream != NULL) && (!overwrite)) {
        sprintf(message, _("File <%s> exists - refusing to overwrite "), name);
        fclose(testStream);
        return NULL;
    }
    else {
        stream = fopen(name, "w");
        if (stream == NULL) {
            sprintf(message, _("Can't create file <%s> "), name);
            return NULL;
        }
        else {
            if (testStream != NULL) {
                G_warning(_("Overwriting output file <%s> \n"), name);
            }
            else {
                G_message(_("Writing output file <%s> \n"), name);
            }
        }
    }

    return (stream);
}
