/******************************************************************************
* 
* Computes the minimum convex polygon from a file of relocations
* 
* 29 August 2006
*
* Clement Calenge, Original code from Andrea Aime
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


struct Point {
   double x;
   double y;
};

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
    return (loPoints + upPoints);
}




/*
 * Outputs the points that comprises the convex hull as a single closed line
 * and the hull baricenter as the label points (as it is a linear combination
 * of points on the hull is guaranteed to be inside the hull, follow from the
 * definition of convex polygon)
 */

int outputHull(struct Map_info *Map, struct Point* P, int *hull,
               int numPoints) {
    struct line_pnts *Points;
    struct line_cats *Cats;
    double *tmpx, *tmpy;
    int i, pointIdx;
    double xc, yc;

    tmpx = (double *) G_malloc((numPoints + 1) * sizeof(double));
    tmpy = (double *) G_malloc((numPoints + 1) * sizeof(double));

    xc = yc = 0;
    for(i = 0; i < numPoints; i++) {
        pointIdx = hull[i];
        tmpx[i] = P[pointIdx].x;
        tmpy[i] = P[pointIdx].y;
        /* average coordinates calculation... may introduce a little
           numerical error but guaratees that no overflow will occurr */
        xc = xc + tmpx[i] / numPoints;
        yc = yc + tmpy[i] / numPoints;
    }
    tmpx[numPoints] = P[hull[0]].x;
    tmpy[numPoints] = P[hull[0]].y;

    Points = Vect_new_line_struct ();
    Cats = Vect_new_cats_struct ();
    Vect_copy_xyz_to_pnts(Points, tmpx, tmpy, 0, numPoints+1);
    G_free(tmpx);
    G_free(tmpy);

    /* write out convex hull */
    Vect_write_line (Map, GV_BOUNDARY, Points, Cats);
    
    /* find and add centroid */
    Vect_reset_line (Points);
    Vect_append_point (Points,xc, yc, 0.0);
    Vect_cat_set ( Cats, 1, 1 );
    Vect_write_line (Map, GV_CENTROID, Points, Cats);
    Vect_destroy_line_struct (Points);


    return 0;
}



int main(int argc, char **argv) {
    struct GModule *module;
    struct Option *input, *output, *percent;
    struct Flag *all;
    struct Cell_head window;

    char *mapset;
    FILE* fdsite;
    struct Map_info Map, In;
    struct Point *points;  /* point loaded from site file */
    struct Point *pointsb;  /* point after removing outliers */
    int *hull;   /* index of points located on the convex hull */
    int numSitePoints, numHullPoints;
    int *cons;
    int nnn, pascons, ran, kk, i, j;
    double *dist, yc, xc, perc, tmpd;
    double **coordinate;
    
    G_gisinit (argv[0]);

    module = G_define_module();
    module->keywords = _("vector, geometry");
    module->description = "Uses a GRASS vector points map to compute the Minimum convex polygon home range";

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
    percent->required = YES;
    percent->description = "Percentage of the relocations to keep";
    percent->answer = "95";

    if (G_parser (argc, argv)) exit (1);

    Vect_check_input_output_name ( input->answer, output->answer, GV_FATAL_EXIT );
    
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
    if(numSitePoints < 3 )
        G_fatal_error ("MCP calculation requires at least three points");

    /* creates the points data structure */
    points = (struct Point *) G_malloc(numSitePoints * sizeof(struct Point));
    for (i = 0; i < numSitePoints; i++) {
	points[i].x = coordinate[i][0];
	points[i].y = coordinate[i][1];
    }


   /* load the percent */
    perc = atof(percent->answer);
    
    /* create vector file */
    if (0 > Vect_open_new (&Map, output->answer, 0) )
        G_fatal_error ("Unable to open vector file <%s>\n", output->answer);

    Vect_hist_command ( &Map );
    
    /* Compute the barycenter */
    
    vecalloc(&dist, numSitePoints);
    xc=0;
    yc=0;
    for(i = 0; i < numSitePoints; i++) {
        xc = xc + (points[i].x) / ((double) numSitePoints);
        yc = yc + (points[i].y) / ((double) numSitePoints);
    }
    
    for(i = 0; i < numSitePoints; i++) {
        dist[i+1] = sqrt(pow((points[i].x -xc),2) + pow((points[i].y - yc),2));
    }
    
    nnn = ((int) ((double) numSitePoints - (perc * ((double) numSitePoints) / 100)));
    vecintalloc(&cons, nnn);
    
    kk = 1;
    for (i = 1; i <= numSitePoints; i++) {
	tmpd = dist[i];
	ran = 0;
	for (j = 1; j <= numSitePoints; j++) {
	    if (dist[j] > tmpd)
		ran++;
	}
	if (ran < nnn) {
	    cons[kk] = i;
	    kk++;
	}
    }
    
    pointsb = (struct Point *) G_malloc((numSitePoints - nnn) * sizeof(struct Point));
    kk = 0;
    for (i = 1; i <= numSitePoints; i++) {
	pascons = 0;
	for (j = 1; j <= nnn; j++) {
	    if (i==cons[j])
		pascons = 1;
	}
	if (pascons == 0) {
	    pointsb[kk].x = points[i-1].x;
	    pointsb[kk].y = points[i-1].y;
	    kk++;
	}
    }
    numSitePoints = numSitePoints - nnn;
    if(numSitePoints < 3 )
        G_fatal_error ("MCP calculation requires at least three points");
    
    
    /* compute convex hull */
    numHullPoints = convexHull(pointsb, numSitePoints, &hull);

    /* output vector file */
    outputHull(&Map, pointsb, hull, numHullPoints);

    /* clean up and bye bye */
    Vect_build (&Map);
    Vect_close (&Map);
    
    freevec(dist);
    freeintvec(cons);
    return 0;
}
