/* File: papers.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include <string.h>
#include "papers.h"
#include "ps_info.h"
#include "local_proto.h"


PAPER papers[] = {
    {"B0", 2920, 4127, 36., 36., 72., 72.}
    ,
    {"B1", 2064, 2920, 36., 36., 72., 72.}
    ,
    {"B2", 1460, 2064, 36., 36., 72., 72.}
    ,
    {"B3", 1032, 1460, 36., 36., 72., 72.}
    ,
    {"B4", 729, 1032, 36., 36., 72., 72.}
    ,
    {"B5", 516, 729, 36., 36., 72., 72.}
    ,
    {"B6", 363, 516, 36., 36., 72., 72.}
    ,
    {"A6", 297, 420, 36., 36., 72., 72.}
    ,
    {"A5", 420, 595, 36., 36., 72., 72.}
    ,
    {"A4", 595, 842, 36., 36., 72., 72.}
    ,
    {"A3", 842, 1191, 36., 36., 72., 72.}
    ,
    {"A2", 1191, 1684, 36., 36., 72., 72.}
    ,
    {"A1", 1684, 2384, 36., 36., 72., 72.}
    ,
    {"A0", 2384, 3370, 36., 36., 72., 72.}
    ,
    {"Legal", 612, 1008, 36., 36., 72., 72.}
    ,
    {"Ledger", 1224, 792, 36., 36., 72., 72.}
    ,
    {"Letter", 612, 792, 36., 36., 72., 72.}
    ,
    {"Tabloid", 792, 1224, 36., 36., 72., 72.}
    ,
    {"Executive", 522, 756, 36., 36., 72., 72.}
    ,
    {"Folio", 595, 935, 36., 36., 72., 72.}
    ,
    {NULL, 0, 0, 0., 0., 0., 0.}
};

int set_paper(char *name)
{
    register int i;

    for (i = 0; papers[i].name != NULL; i++) {
	if (strcmp(papers[i].name, name) == 0) {
	    PS.page.width = papers[i].width;
	    PS.page.height = papers[i].height;
	    PS.page.left = papers[i].left;
	    PS.page.right = papers[i].right;
	    PS.page.top = papers[i].top;
	    PS.page.bot = papers[i].bot;
	    return 1;
	}
    }

    return 0;
}
