/***************************************************************************
 *            globals.h
 *
 *  Mon Apr 18 15:04:11 2005
 *  Copyright  2005  Benjamin Ducke
 ****************************************************************************/

/*
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Library General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

/*
#define EXPERIMENTAL
*/

#ifndef _GLOBALS_H
#define _GLOBALS_H

/* put a 
#define LOCAL
into main.c ! */

#ifdef LOCAL
#define EXTERN
#else
#define EXTERN extern
#endif

/* uncomment for latest GRASS 6.3.CVS features */
#define GRASS64

#define PROGVERSION 0.99
#define PROGNAME "r.xtent"

/* if DEBUG > 1 we will dump even more details */
#define DEBUG 0

/* enable progress display? */
EXTERN int PROGRESS;

/* additional verbosity? */
EXTERN int VERBOSE;

/* overwrite existing output map? */
EXTERN int OVERWRITE;

/* GEOGRAPHIC OR XY COORDINATES? */
#define XY 0
#define GEOGRAPHIC 1
EXTERN int SYSTEM;

/* STUFF FOR MOVEMENT COST CALCULATIONS */
#define STRAIGHT 0
#define COST 1
EXTERN int DISTANCE;

#define NONE 0
#define BASENAME 1
#define ATTNAME 2
#define MAPNAME 3
#define ADHOC 4
#define PSEUDO 5
EXTERN int COSTMODE;

#define MAXFPVAL 2000000000.0 /* maximum FP value (e.g. for absolute boundaries) */

#define LAMBDA_DEFAULT 1.0
#define WEIGHT_DEFAULT 1000.0	/* default weight of boundaries */
#define PATH_DEFAULT 0.0		/* default weight of pathways */


/* ================================================================================

				STRUCTURES AND TYPES

===================================================================================*/



/* stores report results for one center */
struct report_struct {
	int id;
	char *name;
	long int out_count;
	double area;
	double percentage;	
	double max_cost;	
	long int sec_count;
	long int err_count;
	double err_sum;
	double err_avg;
	double err_var;
	double err_std;
	int competitor;
	int competitor_id;	
	double competitor_p;
	long int aggressor;
	double aggressor_p;
	/* the following point to other centers */
	int boss;
	int boss_id;
	char *boss_name;
	int num_subjects;
	int *subject;
	int *subject_id;
	char **subject_name;
};


/* ================================================================================

				GLOBAL MODULE OPTIONS AND FLAGS

===================================================================================*/


/* by making this global, all func's will have access to module options and flags */
EXTERN 	struct GModule *module;

EXTERN struct
{
	struct Option *centers; /* known political centers */
	struct Option *output; /* name of new raster map */		
	struct Option *report; /* name of ASCII report file */
	struct Option *costs_att; /* att name for cost surfaces */
	struct Option *labels; /* name of attribute in centers map used for raster category labels */
	struct Option *rgbcol; /* column with color specs in format RRR:GGG:BBB */
	struct Option *cats; /* name of indexing attribute for writing result map values */
	struct Option *errors; /* raster map/attribute in to store normalized error term */
	struct Option *second; /* raster map to store ID of center with second-highest I */
	struct Option *maxdist; /* maximum dist/cost attribute for each center */
	struct Option *ruler;  /* int attribute that points to a dominating center */
	struct Option *ally;  /* str attribut with comma-separated indices to allied centers */
	struct Option *c; /* read C from this attribute in centers map */	
	struct Option *k; /* global k */
	struct Option *a; /* global a */
}
parm;
EXTERN struct
{
	struct Flag *tabular; /* tabular output format for report */
	struct Flag *strict; /* imposes I >= 0 restriction (original formula) */
}
flag;

/* WE NEED TO KEEP THE FOLLOWING GLOBAL, IN ORDER TO BE ABLE
 * TO EASILY SPLIT UP THE COMPLEX PROGRAM LOGICS IN THE MAIN
 * ROUTINE AND TO PASS INFORMATION TO THE AT_EXIT CLEAN UP
 * FUNCTION
 */

/* basic XTENT parameters */
EXTERN double a,k;
EXTERN double *C;
EXTERN double *C_norm; /* normalized C */
EXTERN int I, I_second;
EXTERN int num_centers;

/* for adhoc generation of cost surface maps */
EXTERN char **costcmds;
EXTERN char **tmapnames; /* array of temp map names (costs) */
EXTERN char *temapname; /* temp map name (unnormalized error map) */
EXTERN int make_pseudo;
EXTERN int make_error;
EXTERN int make_colors;

#endif /* _GLOBALS_H */
