/***********************************************************************/
/*
   groups.c

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include "groups.h"
#include "global_vars.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

/* void allocateInitialGroupMembership (node* nodes, node** groups, long int
 * numpoints) { */
node **allocateInitialGroupMembership(node *nodes, long int numpoints)
{
    int i;
    node **groups;
    node *ptr;
    node *prevPtr;

    groups = (node **)malloc((numpoints + 1) * sizeof(node *));
    if (!groups) {
        G_fatal_error(_("\n\nFATAL ERROR - failure to allocate memory for "
                        "groupList in allocateInitialGroupMembership()\n\n"));
    }

    /* Set up tails of group lists */
    groups[ownGroup] = &nodes[0]; /* First point in point list */
    for (i = 0; i < numpoints; i++) {
        groups[i] = NULL; /* No members yet */
        /* fprintf(stderr, "nodeList:%d   groupList:%d", nodes, groups); */
    }

    /* Set up initial membership (own group) and forward pointers */
    for (i = 0; i < (numpoints - 1); i++) {
        nodes[i].group = ownGroup;       /* Member of own group only */
        nodes[i].nGroup = &nodes[i + 1]; /* Next node */
    }
    nodes[numpoints - 1].group = ownGroup;
    nodes[numpoints - 1].nGroup = NULL; /* End of list */

    /* Set up backward pointers */
    ptr = groups[ownGroup];
    prevPtr = NULL;
    while (ptr != NULL) {
        ptr->pGroup = prevPtr;
        prevPtr = ptr;
        ptr = ptr->nGroup;
    }
    return (groups);
}

/***********************************************************************/

void printNodesInAllGroups(node *nodes, node **groups)
{
    int g;

    for (g = 0; g <= ownGroup; g++) {
        printNodesInGroup(nodes, groups, g);
    }
}

/***********************************************************************/

void printNodesInGroup(node *nodes, node **groups, int group)
{
    node *ptr;

    fprintf(stderr, "\n\nPoints in group %d (ids)", group);
    ptr = groups[group];
    while (ptr != NULL) {
        printNodePositionInGroupList(ptr);
        ptr = ptr->nGroup;
    }
}

/***********************************************************************/

void insertNodeAtHeadGroupList(node *this, node **groups, int group,
                               int iteration, float distance)
{

    int oldGroup;
    node *oldNext;
    node *oldPrevious;
    node *newGroupOldHead;

#ifdef DEBUG
    fprintf(
        stderr,
        "\nthis cat= %d\nthis group= %d\n this nGroup= %d\n this pGroup= %d\n",
        this->cat, this->group, this->nGroup, this->pGroup);
#endif
    oldGroup = this->group;
    oldNext = this->nGroup;
    oldPrevious = this->pGroup;

    if (oldPrevious != NULL) {
        oldPrevious->nGroup = oldNext;
    }
    else {
        groups[oldGroup] = oldNext;
    }
    if (oldNext != NULL) {
        oldNext->pGroup = oldPrevious;
    }
#ifdef DEBUG
    fprintf(stderr, "\nAdding %d to group %d. New position is:", this->cat,
            group);
#endif
    newGroupOldHead = groups[group];
    groups[group] = this;
    this->pGroup = NULL;
    this->nGroup = newGroupOldHead;
    if (newGroupOldHead != NULL) {
        newGroupOldHead->pGroup = this;
    }

    this->group = group;

    if (this->first_change == 0) {
        this->first_change = iteration;
    }
    this->last_change = iteration;
    this->count_changes += 1;

    if (this->first_distance == -1.0) {
        this->first_distance = distance;
    }
    this->last_distance = distance;

#ifdef DEBUG
    fprintf(stderr, "\nthis: %d", group);
    printNodePositionInGroupList(this);
#endif
}

/***********************************************************************/

void printNodePositionInGroupList(node *this)
{
    fprintf(stderr, "\ncat=%d", this->cat);
    fprintf(stderr, " grp=%d", this->group);

    if (this->pGroup != NULL) {
        fprintf(stderr, " p=%d", this->pGroup->cat);
    }
    else {
        fprintf(stderr, " p=NULL");
    }
    if (this->nGroup != NULL) {
        fprintf(stderr, " n=%d", this->nGroup->cat);
    }
    else {
        fprintf(stderr, " n=NULL");
    }
}

/***********************************************************************/

int *allocateInitialGroupSize(long int numpoints)
{
    int *groupSizePtr;
    long int i;

    groupSizePtr = (int *)malloc((numpoints + 1) * sizeof(int));
    if (!groupSizePtr) {
        G_fatal_error(_("\n\nFATAL ERROR - failure to allocate memory for "
                        "groupSize in allocateInitialGroupSize()\n\n"));
    }
    else {
        for (i = 0; i <= numpoints; i++) {
            groupSizePtr[i] = 0;
        }
        groupSizePtr[numpoints] = ownGroup;
    }
    return (groupSizePtr);
}

/***********************************************************************/

void freeGroupSize(int *groupSizePtr)
{
    G_free(groupSizePtr);
}

/***********************************************************************/

void calculateGroupSize(int *groupSize, node **groups, int group)
{
    node *ptr;
    int i = 0;

    /*fprintf (stderr, "\n\nComputing size of group %d (ids)", group); */
    ptr = groups[group];
    while (ptr != NULL) {
        i++;
        ptr = ptr->nGroup;
    }
    groupSize[group] = i;
}

/***********************************************************************/

void incrementGroupSize(int *groupSize, int group)
{

    /*fprintf (stderr, "\n\nIncrementing size of group %d (ids)", group); */
    groupSize[group]++;
}

/***********************************************************************/

void decrementGroupSize(int *groupSize, int group)
{

    /*fprintf (stderr, "\n\nDecrementing size of group %d (ids)", group); */
    groupSize[group]--;
}

/***********************************************************************/

void addToGroupSize(int *groupSize, int group, int value)
{

    /*fprintf (stderr, "\n\nAdding %d to size of group %d (ids)", value, group);
     */
    groupSize[group] += value;
}

/***********************************************************************/

void subtractFromGroupSize(int *groupSize, int group, int value)
{

    /*fprintf (stderr, "\n\nSubtracting %d from size of group %d (ids)", value,
     * group); */
    groupSize[group] -= value;
}

/***********************************************************************/

void resetGroupSize(int *groupSize, int group)
{

    /*fprintf (stderr, "\n\nResetting size of group %d (ids)", group); */
    groupSize[group] = 0;
}

/***********************************************************************/

int getGroupSize(int *groupSize, int group)
{

    /* fprintf (stderr, "\n\nSize of group %d (ids) is %d", group,
     * groupSize[group]); */
    return (groupSize[group]);
}

/***********************************************************************/

void printGroupSize(int *groupSize, long int numpoints)
{
    long int i;

    fprintf(stderr, "\n       Group          Size");
    for (i = 0; i <= numpoints; i++) {
        fprintf(stderr, "\n%12ld  %12d", i, groupSize[i]);
    }
    fprintf(stderr, "\n");
}

/***********************************************************************/

float updateGroupSizes(int *groupSize, int groupA, int groupB, int targetGroup)
{
    long int fromSize, toSize, newSize;
    float numerator, denominator;
    float connectionCoefficient;

    /*fprintf(stderr, "\nfg = %d  tg = %d  TG = %d", groupA, groupB,
     * targetGroup); */

    if ((groupA == ownGroup) && (groupB == ownGroup)) {
        /* Neither node in a group other than own */
        fromSize = 1;
        toSize = 1;
        addToGroupSize(groupSize, targetGroup, 2);
        subtractFromGroupSize(groupSize, ownGroup, 2);
    }
    else {
        if ((groupA != ownGroup) && (groupB != ownGroup)) {
            if (groupA == targetGroup) {
                toSize = getGroupSize(groupSize, groupA);
                fromSize = getGroupSize(groupSize, groupB);
                addToGroupSize(groupSize, targetGroup, fromSize);
                /* Don't reset group size.  Once a group has lost all members
                   it no longer plays a role in the algorithm, but it
                   potentially useful data (a record of the maximum size
                   attained by that group) */
                /*resetGroupSize (groupSize, groupB); */
            }
            else {
                toSize = getGroupSize(groupSize, groupB);
                fromSize = getGroupSize(groupSize, groupA);
                addToGroupSize(groupSize, targetGroup, fromSize);
                /* Don't reset group size.  Once a group has lost all members
                   it no longer plays a role in the algorithm, but it
                   potentially useful data (a record of the maximum size
                   attained by that group) */
                /*resetGroupSize (groupSize, groupA); */
            }
        }
        else {
            if (groupA == targetGroup) {
                toSize = getGroupSize(groupSize, groupA);
                fromSize = 1; /* Must be ownGroup */
                incrementGroupSize(groupSize, targetGroup);
                decrementGroupSize(groupSize, groupB);
            }
            else {
                toSize = getGroupSize(groupSize, groupB);
                fromSize = 1; /* Must be ownGroup */
                incrementGroupSize(groupSize, targetGroup);
                decrementGroupSize(groupSize, groupA);
            }
        }
    }

    /* Compute the connection coefficent.  The more equal the the
       joining groups and the bigger the new group, the greater the
       coefficient */
    newSize = fromSize + toSize;
    numerator = ((newSize - fromSize) <= (newSize - toSize))
                    ? (newSize - fromSize)
                    : (newSize - toSize);
    denominator = ((newSize - fromSize) >= (newSize - toSize))
                      ? (newSize - fromSize)
                      : (newSize - toSize);
    connectionCoefficient = newSize * numerator / denominator;
    /*fprintf(stderr, "NS=%ld FS=%ld TS=%ld Num=%lf Den=%lf CC=%f",
       newSize, fromSize, toSize, numerator, denominator,
       connectionCoefficient); */
    return (connectionCoefficient);
}

/***********************************************************************/

tGroupInfo *allocateInitialGroupInfo(long int numpoints)
{
    tGroupInfo *groupInfoPtr;
    long int i;

    groupInfoPtr = (tGroupInfo *)malloc((numpoints + 1) * sizeof(tGroupInfo));
    if (!groupInfoPtr) {
        G_fatal_error(_("\n\nFATAL ERROR - failure to allocate memory for "
                        "groupAge in allocateInitialGroupAge()\n\n"));
    }

    for (i = 0; i < numpoints; i++) {
        groupInfoPtr[i].birth = -1;
        groupInfoPtr[i].death = -1;
        groupInfoPtr[i].longevity = -1;
        groupInfoPtr[i].birth_distance = -1.0;
        groupInfoPtr[i].death_distance = -1.0;
        groupInfoPtr[i].wins = 0;
    }
    groupInfoPtr[i].birth = 0;
    groupInfoPtr[i].death = -1;
    groupInfoPtr[i].longevity = -1;
    groupInfoPtr[i].birth_distance = -1.0;
    groupInfoPtr[i].death_distance = -1.0;
    groupInfoPtr[i].wins = 0;

    return (groupInfoPtr);
}

/***********************************************************************/

void freeGroupInfo(tGroupInfo *groupInfoPtr)
{
    G_free(groupInfoPtr);
}
