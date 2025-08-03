/***********************************************************************/
/*
   groups.h

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#ifndef GROUPS_H
#define GROUPS_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>

#include "node.h"
#include "file.h"

/***********************************************************************/
/* Types                                                         */

/***********************************************************************/

typedef struct tGroupInfo tGroupInfo; /* We must do this to allow type node to
                                         reference itself  */

struct tGroupInfo {
    int birth;     /* iteration when created */
    int death;     /* iteration when died (incorporated into another group) */
    int longevity; /* in iteration */
    float birth_distance; /* distance at which created */
    float death_distance; /* distance at which died (incorporated into another
                             group) */
    int wins; /* Number of groups (membership > 1) subsumed into this group */
};

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

/* void allocateInitialGroupMembership (node*, node**, long int); */
node **allocateInitialGroupMembership(node *, long int);
void insertNodeAtHeadGroupList(node *, node **, int, int, float);
void printNodesInGroup(node *, node **, int);
void printNodesInAllGroups(node *, node **);
void printNodePositionInGroupList(node *);
int *allocateInitialGroupSize(long int);

/* int* allocateInitialGroupSize (long int numpoints) */
void freeGroupSize(int *);
void printGroupSize(int *, long int);

/* void printGroupSize (int* groupSize, long int numpoints) */
void calculateGroupSize(int *, node **, int);

/* void calculateGroupSize (int* groupSize, node** groups, int group) */
void incrementGroupSize(int *, int);

/* void incrementGroupSize (int* groupSize, int group) */
void decrementGroupSize(int *, int);

/* void decrementGroupSize (int* groupSize, int group) */
void addToGroupSize(int *, int, int);

/* void addToGroupSize (int* groupSize, int group, int value) */
void subtractFromGroupSize(int *, int, int);

/* void subtractFromGroupSize (int* groupSize, int group, int value) */
void resetGroupSize(int *, int);

/* void resetGroupSize (int* groupSize, int group) */
int getGroupSize(int *, int);

/* int getGroupSize (int* groupSize, int group) */
float updateGroupSizes(int *, int, int, int);

/* float updateGroupSizes (int* groupSize, int fromGroup, int toGroup, int
 * targetGroup) */
/* int** allocateInitialGroupAge (long int); */
tGroupInfo *allocateInitialGroupInfo(long int);

/* int** allocateInitialGroupAge (long int numpoints) */
/* void freeGroupAge (int**, int); */
void freeGroupInfo(tGroupInfo *);

/* void freeGroupAge (groupAgePtr) */

#endif
