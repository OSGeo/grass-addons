/******************************************************************************
* 
* Computes the Cluster home range from a file of relocations
* 
* 5 September 2007
*
* Clement Calenge
* This file is part of GRASS GIS. It is free software. You can
* redistribute it and/or modify it under the terms of
* the GNU General Public License as published by the Free Software
* Foundation; either version 2 of the License, or (at your option)
* any later version.

* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
******************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/site.h>
#include <grass/glocale.h>


/* *************************************************************
   
*                          The sources from ADE-4

**************************************************************** */


void vecalloc (double **vec, int n)
/*--------------------------------------------------
 * Memory Allocation for a vector of length n
 --------------------------------------------------*/
{
    if ( (*vec = (double *) calloc(n+1, sizeof(double))) != 0) {
	**vec = n;
	return;
    } else {
	return;
    }
}

/*****************/
void vecintalloc (int **vec, int n)
/*--------------------------------------------------
 * Memory allocation for an integer vector of length  n
 --------------------------------------------------*/
{
    if ( (*vec = (int *) calloc(n+1, sizeof(int))) != NULL) {
	**vec = n;
	return;
    } else {
	return;
    }
}


void taballoc (double ***tab, int l1, int c1)
/*--------------------------------------------------
 * Dynamic Memory Allocation for a table (l1, c1)
 --------------------------------------------------*/
{
    int i, j;
    
    if ( (*tab = (double **) calloc(l1+1, sizeof(double *))) != 0) {
	for (i=0;i<=l1;i++) {
	    if ( (*(*tab+i)=(double *) calloc(c1+1, sizeof(double))) == 0 ) {
		return;
		for (j=0;j<i;j++) {
		    free(*(*tab+j));
		}
	    }
	}
    }
    
    **(*tab) = l1;
    **(*tab+1) = c1;
}





/***********************************************************************/
void freevec (double *vec)
/*--------------------------------------------------
 * Free memory for a vector
 --------------------------------------------------*/
{
    free((char *) vec);	
}

/***********************************************************************/
void freeintvec (int *vec)
/*--------------------------------------------------
* Free memory for an integer  vector
--------------------------------------------------*/
{
    
    free((char *) vec);
    
}




void freetab (double **tab)
/*--------------------------------------------------
 * Free memory for a table
 --------------------------------------------------*/
{
    int 	i, n;
    
    n = *(*(tab));
    for (i=0;i<=n;i++) {
	free((char *) *(tab+i) );
    }
    free((char *) tab);
}



/* *************************************************************
   
*                          Code from v.hull

**************************************************************** */


int read_points( struct Map_info *In, double ***coordinate)
{
  int    line, nlines, npoints, ltype, i = 0;
  double **xySites;
  static struct line_pnts *Points = NULL;
  
  if (!Points)
      Points = Vect_new_line_struct ();
  
  /* Allocate array of pointers */
  npoints = Vect_get_num_primitives(In,GV_POINT);
  xySites = (double **) G_calloc ( npoints, sizeof(double*) );
  
  nlines = Vect_get_num_lines(In);

  for ( line = 1; line <= nlines; line++){
      ltype = Vect_read_line (In, Points, NULL, line);
      if ( !(ltype & GV_POINT ) ) continue;
      
      xySites[i] = (double *)G_calloc((size_t)2, sizeof(double));
      
      xySites[i][0] = Points->x[0];
      xySites[i][1] = Points->y[0]; 
      i++;
  }	

  *coordinate = xySites;

  return (npoints);
}





struct Point {
   double x;
   double y;
};


int rightTurn(struct Point *P, int i, int j, int k) {
    double a, b, c, d;
    a = P[i].x - P[j].x;
    b = P[i].y - P[j].y;
    c = P[k].x - P[j].x;
    d = P[k].y - P[j].y;
    return a*d - b*c < 0;	
}


int cmpPoints(const void* v1, const void* v2) {
    struct Point *p1, *p2;
    p1 = (struct Point*) v1;
    p2 = (struct Point*) v2;
    if( p1->x > p2->x )
        return 1;
    else if( p1->x < p2->x )
        return -1;
    else
        return 0;
}


int convexHull(struct Point* P, const int numPoints, int **hull) {
    int pointIdx, upPoints, loPoints;
    int *upHull, *loHull;

    /* sort points in ascending x order*/
    qsort(P, numPoints, sizeof(struct Point), cmpPoints);

    *hull = (int*) G_malloc(numPoints * 2 * sizeof(int));

    /* compute upper hull */
    upHull = *hull;
    upHull[0] = 0;
    upHull[1] = 1;
    upPoints = 1;
    for(pointIdx = 2; pointIdx < numPoints; pointIdx++) {
        upPoints++;
        upHull[upPoints] = pointIdx;
        while( upPoints > 1 &&
               !rightTurn(P, upHull[upPoints], upHull[upPoints-1],
                             upHull[upPoints-2])
             ) {
            upHull[upPoints-1] = upHull[upPoints];
            upPoints--;
        }
    }

    /*
    printf("upPoints: %d\n", upPoints);
    for(pointIdx = 0; pointIdx <= upPoints; pointIdx ++)
        printf("%d ", upHull[pointIdx]);
    printf("\n");
    */

    /* compute lower hull, overwrite last point of upper hull */
    loHull = &(upHull[upPoints]);
    loHull[0] = numPoints - 1;
    loHull[1] = numPoints - 2;
    loPoints = 1;
    for(pointIdx = numPoints - 3; pointIdx >= 0; pointIdx--) {
        loPoints++;
        loHull[loPoints] = pointIdx;
        while( loPoints > 1 &&
               !rightTurn(P, loHull[loPoints], loHull[loPoints-1],
                             loHull[loPoints-2])
             ) {
             loHull[loPoints-1] = loHull[loPoints];
             loPoints--;
        }
    }

    G_debug(3, "numPoints:%d loPoints:%d upPoints:%d",
                numPoints, loPoints, upPoints);
    /*
    printf("loPoints: %d\n", loPoints);
    for(pointIdx = 0; pointIdx <= loPoints; pointIdx ++)
        printf("%d ", loHull[pointIdx]);
    printf("\n");
    */

    /* reclaim uneeded memory */
    *hull = (int *) G_realloc(*hull, (loPoints + upPoints) * sizeof(int));
    return loPoints + upPoints;
}





/* *********************************************************************
 *                                                                     *
 *              Home range by Clustering (Kenward et al. 2001)         *
 *                     Sources from adehabitat                         *
 *                                                                     *
 ***********************************************************************/


/* finds the cluster with the minimum average distance between the 3 points
   not assigned to a cluster */

void trouveclustmin(double **xy, int *clust, int *lo1, int *lo2,
		    int *lo3, double *dist)
{
    /* Declaration */
    int i, j, k, m, npas, nr, *indice;
    double **xy2, di1, di2, di3, ditmp;
    
    /* Memory allocation */
    nr = (int) xy[0][0];
    npas = 0;
    di1 = 0;
    di2 = 0;
    di3 = 0;
    ditmp = 0;
    
    /* Number of non assigned points */
    for (i = 1; i <= nr; i++) {
	if (clust[i] == 0) {
	    npas++;
	}
    }
    taballoc(&xy2, npas, 2);
    vecintalloc(&indice, npas);
    
    /* The non assigned points are stored in xy2 */
    k = 1;
    for (i = 1; i <= nr; i++) {
	if (clust[i] == 0) {
	    xy2[k][1] = xy[i][1];
	    xy2[k][2] = xy[i][2];
	    indice[k] = i;
	    k++;
	}
    }
    
    /* Computes the distane between the relocations */
    *dist = 0;
    m=0;
    for (i = 1; i <= (npas-2); i++) {
	for (j = (i+1); j <= (npas-1); j++) {
	    for (k = (j+1); k <= npas; k++) {
		di1 = sqrt((xy2[i][1] - xy2[j][1]) * (xy2[i][1] - xy2[j][1]) + 
			   (xy2[i][2] - xy2[j][2]) * (xy2[i][2] - xy2[j][2]) );
		di2 = sqrt((xy2[i][1] - xy2[k][1]) * (xy2[i][1] - xy2[k][1]) + 
			   (xy2[i][2] - xy2[k][2]) * (xy2[i][2] - xy2[k][2]));
		di3 = sqrt((xy2[k][1] - xy2[j][1]) * (xy2[k][1] - xy2[j][1]) + 
			   (xy2[k][2] - xy2[j][2]) * (xy2[k][2] - xy2[j][2]));
		/* average distance */
		ditmp = (di1 + di2 + di3) / 3;
		/* minimum distance */
		if ((m == 0) || (ditmp < *dist)) {
		    *dist = ditmp;
		    *lo1 = indice[i];
		    *lo2 = indice[j];
		    *lo3 = indice[k];
		}
		m = 1;
	    }
	}
    }
    /* free memory */
    freeintvec(indice);
    freetab(xy2);
}



/* Finds the distance between a cluster of points and the nearest point*/
void nndistclust(double **xy, double *xyp, double *dist)
{
    /* Declaration */
    int n, i, m;
    double di;

    m = 0;
    di =0;
    n = (int) xy[0][0];
    *dist = 0;
    
    /* finds the distance and the corresponding point */
    for (i = 1; i <= n; i++) {
	di = sqrt( (xy[i][1] - xyp[1]) * (xy[i][1] - xyp[1]) + 
		   (xy[i][2] - xyp[2]) * (xy[i][2] - xyp[2]) );
	if ( (di < *dist) || (m == 0) ) {
	    *dist = di;
	}
	m = 1;
    }
}


/* The function nndistclust is applied for all available clusters */
void parclust(double **xy, int *clust, int *noclust, 
	      int *noloc, double *dist)
{
    /* Declaration */
    int i, k, m, nr2, nr, nocl;
    double **xy2, *xyp, di, di2;
    
    /* Memory allocation */
    nocl = *noclust;
    nr = xy[0][0];
    nr2 = 0;
    
    /* The number of available clusters */
    for (i = 1; i <= nr; i++) {
	if (clust[i] == nocl) {
	    nr2++;
	}
    }

    taballoc(&xy2, nr2, 2);
    vecalloc(&xyp, 2);
    
    /* stores the non assigned points in xy2 */
    k = 1;
    for (i = 1; i <= nr; i++) {
	if (clust[i] == nocl) {
	    xy2[k][1] = xy[i][1];
	    xy2[k][2] = xy[i][2];
	    k++;
	}
    }
    
    /* Finds the minimum distance between a point and a cluster, 
       performed for all clusters */
    di = 0;
    di2 = 0;
    m = 0;
    *dist = 0;
    for (i = 1; i <= nr; i++) {
	if (clust[i] != nocl) {
	    xyp[1] = xy[i][1];
	    xyp[2] = xy[i][2];
	    nndistclust(xy2, xyp, &di);
	    if ( (di < *dist) || (m == 0) ) {
		*dist = di;
		*noloc = i;
	    }
	    m = 1;
	}
    }

    /* Free memory */
    freetab(xy2);
    freevec(xyp);
}


/* The function trouveminclust identifies the cluster for which the nearest 
   point is the closest */
void trouveminclust(double **xy, int *liclust, int *clust, 
		    int *noclust, int *noloc, double *dist)
{
    /* Declaration */
    int i, nr, nc, m, labclust, nolo;
    double di;
    
    nr = (int) xy[0][0];
    nc = 0;
    di = 0;
    labclust = 0;
    nolo = 0;
    
    /* Assigned clusters */
    for (i = 1; i <= nr; i++) {
	if (liclust[i] > 0) {
	    nc++;
	}
    }
    
    /* finds the minimum distance between a cluster and its nearest point 
       (the cluster name and the point ID are searched) */
    m = 0;
    *dist = 0;
    for (i = 1; i <= nc; i++) {
	labclust = liclust[i];
	parclust(xy, clust, &labclust, &nolo, &di);
	if ( (m == 0) || (di < *dist) ) {
	    *dist = di;
	    *noloc = nolo;
	    *noclust = labclust;
	}
	m = 1;
    }
}


/* What should be done: create a new cluster or add a relocation 
   to an existing one ? */

void choisnvclust(double **xy, int *liclust, int *clust, int *ordre)
{
    /* Declaration */
    int i, k, nr, noloat, cluat, nolo1, nolo2, nolo3, maxclust;
    int maxindiceclust, clu1, *liclub, nz;
    double dmoyclust, dminloc;
    
    /* Memory allocation */
    nz = 0;
    i = 0;
    k = 0;
    nr = (int) xy[0][0];
    maxclust = 0;
    maxindiceclust = 0;
    nolo1 = 0;
    nolo2 = 0;
    nolo3 = 0;
    noloat = 0;
    cluat = 0;
    clu1 = 0;
    vecintalloc(&liclub, nr);
    
    /* finds the max label for the cluster */
    for (i = 1; i <= nr; i++) {
	if (clust[i] != 0) {
	    if (clust[i] > maxclust) {
		maxclust = clust[i];
	    }
	    if (liclust[i] != 0) {
		maxindiceclust = i;
	    }
	}
    }
    
    /* Finds the min distance between 3 relocations */
    trouveminclust(xy, liclust, clust, &cluat, &noloat, &dminloc);
    
    /* Computes the average distance between the locs of the smaller cluster */
    /* First, one verifies that there is at least Three non assigned locs */
    dmoyclust = dminloc +1;
    for (i = 1; i <= nr; i++) {
	if (clust[i] == 0) {
	    nz++;
	}
    }
    if (nz > 3) {
	dmoyclust = 0;
	trouveclustmin(xy, clust, &nolo1, &nolo2, &nolo3, &dmoyclust);
    }
    
    /* First case: A new cluster independent from the others */
    if (dmoyclust < dminloc) {
	ordre[nolo1] = 1;
	ordre[nolo2] = 1;
	ordre[nolo3] = 1;
	
	clust[nolo1] = maxclust + 1;
	clust[nolo2] = maxclust + 1;
	clust[nolo3] = maxclust + 1;
	
	liclust[maxindiceclust+1] = maxclust + 1;
	
    } else {
	/* Second case: one loc is added to a cluster */
	
	/* Case 2.1: the loc does not belong to one cluster */
	if (clust[noloat] == 0) {
	    ordre[noloat] = 1;
	    clust[noloat] = cluat;
	} else {
	    
	    /* Case 2.2: the loc belong to one cluster: fusion */
	    clu1 = clust[noloat];
	    for (i = 1; i <= nr; i++) {
		if (clust[i] == clu1) {
		    clust[i] = cluat;
		    ordre[i] = 1;
		}
		if (liclust[i] == clu1) {
		    liclust[i] = 0;
		}
	    }
	    /* and cleaning of liclust */
	    k = 1;
	    for (i = 1; i <= nr; i++) {
		if (liclust[i] != 0) {
		    liclub[k] = liclust[i];
		    k++;
		}
	    }
	    for (i = 1; i <= nr; i++) {
		liclust[i] = liclub[i];
	    }
	}
    }
    freeintvec(liclub);
}


/* The main function for home range computation */

void clusterhr(double **xy, int *facso, int *nolocso, int *cluso)
{
    /* Declaration */
    int i, nr, lo1, lo2, lo3, *clust, len, con, *ordre, *liclust, courant;
    double di;

    /* Memory allocation */
    courant = 1;
    nr = (int) xy[0][0];
    vecintalloc(&clust, nr);
    vecintalloc(&ordre, nr);
    vecintalloc(&liclust, nr);
    lo1 = 0;
    lo2 = 0;
    lo3 = 0;
    di = 0;
    con = 1;
    len = 0;
    
    /* Begin: Search for the first cluster */
    trouveclustmin(xy, clust, &lo1, &lo2,
		   &lo3, &di);
    
    clust[lo1] = 1;
    clust[lo2] = 1;
    clust[lo3] = 1;
    liclust[1] = 1;
    len = 3;
    
    /* We store it in the output */
    cluso[1] = 1;
    cluso[2] = 1;
    cluso[3] = 1;
    nolocso[1] = lo1;
    nolocso[2] = lo2;
    nolocso[3] = lo3;
    facso[1] = 1;
    facso[2] = 1;
    facso[3] = 1;
    
    /* Then repeat until all relocations belong to the same cluster */
    while (con == 1) {
	courant++;
	
	for (i = 1; i <= nr; i++) {
	    ordre[i] = 0;
	}
	
	choisnvclust(xy, liclust, clust, ordre);
	
	for (i = 1; i <= nr; i++) {
	    if (ordre[i] != 0) {
		len++;
		cluso[len] = clust[i];
		nolocso[len] = i;
		facso[len] = courant;
	    }
	}
	
	con = 0;
	for (i = 2; i <= nr; i++) {
	    if (clust[i] != clust[1])
		con = 1;
	}
	if (con == 0) {
	    con = 0;
	}
    }
    
    /* Free memory */
    freeintvec(clust);
    freeintvec(ordre);
    freeintvec(liclust);
}



/* Finds the length of the output for the table containing the home range */

void longfacclust(double **xy, int *len2)
{
    /* Declaration */
    int i, nr, lo1, lo2, lo3, *clust, len, con, *ordre, *liclust, courant;
    double di;
    
    /* Memory allocation */
    courant = 1;
    nr = (int) xy[0][0];
    vecintalloc(&clust, nr);
    vecintalloc(&ordre, nr);
    vecintalloc(&liclust, nr);
    lo1 = 0;
    lo2 = 0;
    lo3 = 0;
    di = 0;
    con = 1;
    len = 0;
    
    /* Begin: search for the first cluster */
    trouveclustmin(xy, clust, &lo1, &lo2,
		   &lo3, &di);
    clust[lo1] = 1;
    clust[lo2] = 1;
    clust[lo3] = 1;
    liclust[1] = 1;
    len = 3;
    
    /* Counts the number of rows needed for the table, which will contain the results */
    while (con == 1) {
	courant++;
	
	for (i = 1; i <= nr; i++) {
	    ordre[i] = 0;
	}
	
	choisnvclust(xy, liclust, clust, ordre);
	
	for (i = 1; i <= nr; i++) {
	    if (ordre[i] != 0) {
		len++;
	    }
	}
	con = 0;
	for (i = 2; i <= nr; i++) {
	    if (clust[i] != clust[1])
		con = 1;
	}
	if (con == 0) {
	    con = 0;
	}
    }

    *len2 = len;

    /* Free memory */
    freeintvec(clust);
    freeintvec(ordre);
    freeintvec(liclust);
}








/* *********************************************************************
 *                                                                     *
 *                               Main code                             *
 *                                                                     *
 ***********************************************************************/


int main(int argc, char **argv) {

    struct GModule *module;
    struct Option *input, *output, *percent, *step;
    struct Flag *all;
    struct Cell_head window;
    struct Map_info Map, In;
    struct Point *points;
    struct line_pnts *Pointsb;
    struct line_cats *Cats;
    struct Flag *flag_s, *flag_a;
    
    char *mapset;

    double **coordinate, **coor, *tmpx, *tmpy;
    int numSitePoints, numHullPoints;
    int ntab, *facso, *nolocso, *cluso, *assigne, *numclust;
    int *nomclust, *nbptsclu, *hull;
    double perc, tmp, xc, yc;
    int stepn, nolig, maxstep, i, k, j, m, ok, kk, pointIdx, maxid;
    

    G_gisinit (argv[0]);

    module = G_define_module();
    module->keywords = _("vector, geometry");
    module->description = "Uses a GRASS vector points map to compute the cluster home range";

    input = G_define_option ();
    input->key = "input";
    input->type = TYPE_STRING;
    input->required = YES;
    input->description = "Name of map containing the relocations to be input";
    input->gisprompt = "old,vector,vector,input";

    output = G_define_option ();
    output->key = "output";
    output->type = TYPE_STRING;
    output->required = YES;
    output->description = "Name of a vector area map to be output";
    output->gisprompt = "new,dig,binary file,output";

    percent = G_define_option ();
    percent->key = "percent";
    percent->type = TYPE_STRING;
    percent->required = NO;
    percent->description = "Percentage of the relocations to keep";
    percent->answer = "100";
    
    step = G_define_option ();
    step->key = "step";
    step->type = TYPE_STRING;
    step->required = NO;
    step->description = "Step number";
    step->answer = "1";
    
    flag_s = G_define_flag();
    flag_s->key = 's';
    flag_s->description = _("Use step number");
    
    flag_a = G_define_flag();
    flag_a->key = 'a';
    flag_a->description = _("Return all steps");
    
    /* Arguments OK ? */
    if (G_parser (argc, argv)) exit (1);
    
    /* Output name OK? */
    Vect_check_input_output_name ( input->answer, output->answer, 
				   GV_FATAL_EXIT );
    
    /* récupère la région */
    G_get_window (&window);
    
    
    /* open relocations file */
    if ((mapset = G_find_vector2 (input->answer, "")) == NULL) 
	G_fatal_error (_("Could not find input map '%s'."), input->answer);

    Vect_set_open_level (2); /* Essential before opening a map! 
				defines the level */
    Vect_open_old (&In, input->answer, mapset); /* Opens the vector map */
    
    
    /* checks for legal file name */
    if(G_legal_filename( output->answer ) < 0)
	G_fatal_error(_("illegal file name [%s]."), output->answer);

    
    /* load coordinates */
    numSitePoints = read_points ( &In, &coordinate );

    /* verifier l'allocation de memoire pour coordinate 
       mais ça a l'air d'être bon */
        
    if(numSitePoints < 3 )
        G_fatal_error ("Cluster Home Range calculation requires at least three points");
    
    /* load the percent or the step */
    if (!(flag_s->answer)) {
	perc = atof(percent->answer);
    } else {
	stepn = ((int) atof(step->answer));
    }


    /* create vector file */
    if (0 > Vect_open_new (&Map, output->answer, 0) )
        G_fatal_error ("Unable to open vector file <%s>\n", output->answer);
    Vect_hist_command ( &Map );
    
    
    /* ***************************************************
       
    *       Ici, on passe aux instructions pour ADE-4    *
       
    ****************************************************** */

    /* Les coordonees */
    taballoc(&coor, numSitePoints, 2);
    
    for (i = 1; i <= numSitePoints; i++) {
	coor[i][1] = coordinate[i-1][0];
	coor[i][2] = coordinate[i-1][1];
    }

    
    /* size of the output */
    longfacclust(coor, &ntab);    
    
    /* Memory allocation */
    vecintalloc(&facso, ntab);
    vecintalloc(&nolocso, ntab);
    vecintalloc(&cluso, ntab);
    
    /* Clustering */
    clusterhr(coor, facso, nolocso, cluso);
    
    
    /* Le nombre de lignes à facso */
    nolig = facso[0];

    /* Le nombre d'étapes à l'algorithme */
    maxstep = facso[nolig];
    G_message(_("Maximum step = %d"), maxstep);
    if (flag_s->answer) {
	if (stepn > maxstep) {
	    G_fatal_error(_("The step number should be lower than the max = %d."), maxstep);
	}
	if (stepn < 1) {
	    G_fatal_error(_("The step number should be greater than 1"));
	}
	
    }
    
    /* On détermine la limite du numero de step correspondant 
       au pourcent donne et le numero de ligne max correspondant */
    
    if (!(flag_a->answer)) {
	tmp=0.;
	vecintalloc(&assigne, numSitePoints);
	vecintalloc(&numclust, numSitePoints);
	
	if (!(flag_s->answer)) {
	    for (i = 1; i <= maxstep; i++) {
		if (tmp < perc) {
		    for (j = 1; j <= nolig; j++) {
			if (facso[j] == i) {
			    if (assigne[nolocso[j]] == 0) {
				tmp += 100. * (1. / ((double) numSitePoints));
				assigne[nolocso[j]] = 1;
			    }
			    /* dans tous les cas */
			    maxid = j;
			}
		    }
		}
	    }
	} else {
	    for (j = 1; j <= nolig; j++) {
		if (facso[j] == stepn) {
		    maxid = j;
		}
	    }
	    
	}
	
	/* on pose assigne = 0 pour tout j */
	for (j = 1; j <= numSitePoints; j++) {
	    assigne[j] = 0;
	}
	
	/* Puis, on determine les clusters encore pas "resolved" pour
	   la limite donnée */
	vecintalloc(&numclust, numSitePoints);
	for (j = 1; j <= numSitePoints; j++) {
	    numclust[j] = 0;
	}
	
	for (i = maxid; i>=1; i--) {
	    j = nolocso[i];
	    if (assigne[j] == 0) {
		assigne[j] = 1;
		numclust[j] = cluso[i];
	    }
	}
	
	
	
	/* et leur nombre */
	k = 1;
	vecintalloc(&nomclust, numSitePoints);
	for (i = 1; i <= numSitePoints; i++) {
	    ok = 0;
	    for (j = 1; j <= k; j++) {
		if (nomclust[j] == numclust[i]) {
		    if (nomclust[j] != 0) {
			ok = 1;
		    }
		}
	    }
	    if (ok == 0) {
		if (numclust[i] != 0) {
		    nomclust[k] = numclust[i];
		    k++;
		}
	    }
	}
	k--;
	
	
	/* et le nombre de locs pour chacun */
	vecintalloc(&nbptsclu, k);
	for (i = 1; i <= k; i++) {
	    for (j = 1; j <= numSitePoints; j++) {
		if (numclust[j] == nomclust[i])
		    nbptsclu[i]++;
	    }
	}
	
	
	/* *****************************************************
	 *                                                     *
	 *      Enfin, on repasse à GRASS: on calcule un MCP   *
	 *      par cluster de localisations, que le sort dans *
	 *      la carte de sortie                             *
	 *                                                     *
	 * ***************************************************** */
	
	/* Pour chaque cluster */
	
	for (i = 1; i <= k; i++) {
	    
	    /* memory allocation for the points */
	    points = (struct Point *) G_malloc((nbptsclu[i]) * sizeof(struct Point));
	    /* gets the relocations corresponding to the current cluster */
	    kk=0;
	    for (j = 1; j <= numSitePoints; j++) {
		if (numclust[j] == nomclust[i]) {
		    points[kk].x = coor[j][1];
		    points[kk].y = coor[j][2];
		    kk++;
		}
	    }
	    
	    /* computes the convex hull */
	    numHullPoints = convexHull(points, nbptsclu[i], &hull);
	    
	    /* Memory allocation for tmpx and tmpy */
	    tmpx = (double *) G_malloc((numHullPoints+1) * sizeof(double));
	    tmpy = (double *) G_malloc((numHullPoints+1) * sizeof(double));
	    
	    /* gets the coordinates of the vertices of the hull */
	    xc = 0;
	    yc = 0;
	    for (j = 0; j < numHullPoints; j++) {
		pointIdx = hull[j];
		tmpx[j] = points[pointIdx].x;
		tmpy[j] = points[pointIdx].y;
		xc += tmpx[j] / ((double) numHullPoints);
		yc += tmpy[j] / ((double) numHullPoints);
	    }
	    
	    /* adds the first point of the hull at the end, to have 
	       a closed boundary */
	    tmpx[numHullPoints] = points[hull[0]].x;
	    tmpy[numHullPoints] = points[hull[0]].y;
	    
	    /* Creates a new structure for lines and categories */
	    Pointsb = Vect_new_line_struct ();
	    Cats = Vect_new_cats_struct ();
	    
	    /* Now copies the vertices in the line structure */
	    Vect_copy_xyz_to_pnts(Pointsb, tmpx, tmpy, 0, numHullPoints+1);
	    
	    /* And write the line in the map */
	    Vect_write_line (&Map, GV_BOUNDARY, Pointsb, Cats);
	    
	    /* */
	    Vect_reset_line (Pointsb);
	    Vect_append_point (Pointsb,xc, yc, 0.0);
	    Vect_cat_set ( Cats, 1, i );
	    Vect_write_line (&Map, GV_CENTROID, Pointsb, Cats);
	    
	    /* remove everything that has been created in this loop */
	    
	    Vect_destroy_line_struct(Pointsb);
	    Vect_destroy_cats_struct(Cats);
	    G_free (points);
	    G_free (tmpx);
	    G_free (tmpy);
	    G_free (hull);
	}
	freeintvec(nbptsclu);



    } else {
	
	vecintalloc(&assigne, numSitePoints);
	vecintalloc(&numclust, numSitePoints);
	vecintalloc(&numclust, numSitePoints);
	vecintalloc(&nomclust, numSitePoints);
	
	for (m = 1; m <= maxstep; m++) {
	    tmp=0.;

	    for (j = 1; j <= nolig; j++) {
		if (facso[j] == m) {
		    maxid = j;
		}
	    }
	    	    
	    
	    /* on pose assigne = 0 pour tout j */
	    for (j = 1; j <= numSitePoints; j++) {
		assigne[j] = 0;
	    }
	    
	    /* Puis, on determine les clusters encore pas "resolved" pour
	       la limite donnée */
	    for (j = 1; j <= numSitePoints; j++) {
		numclust[j] = 0;
	    }
	    for (j = 1; j <= numSitePoints; j++) {
		nomclust[j] = 0;
	    }
	    
	    for (i = maxid; i>=1; i--) {
		j = nolocso[i];
		if (assigne[j] == 0) {
		    assigne[j] = 1;
		    numclust[j] = cluso[i];
		}
	    }
	    
	    
	    /* et leur nombre */
	    k = 1;
	    for (i = 1; i <= numSitePoints; i++) {
		ok = 0;
		for (j = 1; j <= k; j++) {
		    if (nomclust[j] == numclust[i]) {
			if (nomclust[j] != 0) {
			    ok = 1;
			}
		    }
		}
		if (ok == 0) {
		    if (numclust[i] != 0) {
			nomclust[k] = numclust[i];
		    k++;
		    }
		}
	    }
	    k--;

	    if (m == 64) {
		for (i = 1; i <= numSitePoints; i++) 
		    G_message(_("Maximum step = %d"), nomclust[i]);
	    }
	

	    /* et le nombre de locs pour chacun */
	    vecintalloc(&nbptsclu, k);
	    for (i = 1; i <= k; i++) {
		for (j = 1; j <= numSitePoints; j++) {
		    if (numclust[j] == nomclust[i])
			nbptsclu[i]++;
		}
	    }
	    

	    /* *****************************************************
	     *                                                     *
	     *      Enfin, on repasse à GRASS: on calcule un MCP   *
	     *      par cluster de localisations, que le sort dans *
	     *      la carte de sortie                             *
	     *                                                     *
	     * ***************************************************** */
	    
	    /* Pour chaque cluster */
	    
	    for (i = 1; i <= k; i++) {
		
		/* memory allocation for the points */
		points = (struct Point *) G_malloc((nbptsclu[i]) * sizeof(struct Point));
		/* gets the relocations corresponding to the current cluster */
		kk=0;
		for (j = 1; j <= numSitePoints; j++) {
		    if (numclust[j] == nomclust[i]) {
			points[kk].x = coor[j][1];
			points[kk].y = coor[j][2];
			kk++;
		    }
		}
		
		/* computes the convex hull */
		numHullPoints = convexHull(points, nbptsclu[i], &hull);
		
		/* Memory allocation for tmpx and tmpy */
		tmpx = (double *) G_malloc((numHullPoints+1) * sizeof(double));
		tmpy = (double *) G_malloc((numHullPoints+1) * sizeof(double));
		
		/* gets the coordinates of the vertices of the hull */
		for (j = 0; j < numHullPoints; j++) {
		    pointIdx = hull[j];
		    tmpx[j] = points[pointIdx].x;
		    tmpy[j] = points[pointIdx].y;
		}
		
		/* adds the first point of the hull at the end, to have 
		   a closed line */
		tmpx[numHullPoints] = points[hull[0]].x;
		tmpy[numHullPoints] = points[hull[0]].y;
		
		/* Creates a new structure for lines and categories */
		Pointsb = Vect_new_line_struct ();
		Cats = Vect_new_cats_struct ();
		
		/* Now copies the vertices in the line structure */
		Vect_copy_xyz_to_pnts(Pointsb, tmpx, tmpy, 0, numHullPoints+1);
		
		/* And write the line in the map */
		Vect_cat_set ( Cats, 1, m );
		Vect_write_line (&Map, GV_LINE, Pointsb, Cats);		
		
		/* remove everything that has been created in this loop */
		Vect_destroy_line_struct(Pointsb);
		Vect_destroy_cats_struct(Cats);
		G_free (points);
		G_free (tmpx);
		G_free (tmpy);
		G_free (hull);
	    }
	}
	freeintvec(nbptsclu);
    }
    
    
    /* clean up and bye bye */
    Vect_build (&Map);
    Vect_close (&Map);
    freetab(coor);
    freeintvec(facso);
    freeintvec(nolocso);
    freeintvec(cluso);
    freeintvec(assigne);
    freeintvec(numclust);
    freeintvec(nomclust);
    
}


